"""FETCH_SOURCE Worker。对应架构文档 02-build.md「Fetch Worker」。
职责：拉取仓库代码、钉到固定 commit、归档、创建 SourceRevision。
"""

import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.config import settings
from app.domain.source_assets import Artifact, Repository, SourceRevision
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("FetchWorker")


def fetch_source(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    """拉取源码并建立不可变 SourceRevision。

    可被 Celery task 调用，也可直接调用（本地开发不依赖 Celery）。
    """
    # 1. 加载 ScanRun + Repository
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        raise ValueError(f"ScanRun {scan_run_id} not found")

    repo = db.get(Repository, scan_run.repository_id)
    if not repo:
        raise ValueError(f"Repository {scan_run.repository_id} not found")

    # 更新阶段状态
    stage = db.execute(
        select(ScanStageRun).where(
            ScanStageRun.scan_run_id == scan_run_id,
            ScanStageRun.stage_type == "FETCH_SOURCE",
        )
    ).scalar_one_or_none()
    if stage:
        stage.status = STAGE_RUNNING
        stage.started_at = datetime.now(timezone.utc)
        db.flush()

    logger.info("fetch_started", repository=repo.name, git_url=repo.git_url)

    # 2. 准备工作目录
    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source"
    workspace.mkdir(parents=True, exist_ok=True)

    # 3. git clone --depth 1
    clone_dir = workspace / "repo"
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    branch = repo.default_branch or "main"
    git_url = repo.git_url

    # 检查 SourceRevision 是否已指定 commit
    source_rev = db.get(SourceRevision, scan_run.source_revision_id) if scan_run.source_revision_id else None
    commit_sha = source_rev.commit_sha if source_rev else None

    if commit_sha:
        # 拉指定 commit
        logger.info("fetching_commit", commit_sha=commit_sha)
        subprocess.run(
            ["git", "init", str(clone_dir)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "remote", "add", "origin", git_url],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "fetch", "--depth", "1", "origin", commit_sha],
            check=True, capture_output=True, timeout=300,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "checkout", "FETCH_HEAD"],
            check=True, capture_output=True,
        )
    else:
        # 浅克隆分支
        logger.info("cloning_branch", branch=branch)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, git_url, str(clone_dir)],
            check=True, capture_output=True, timeout=300,
        )

    # 4. 获取 commit 信息
    commit_sha = subprocess.run(
        ["git", "-C", str(clone_dir), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    commit_author = subprocess.run(
        ["git", "-C", str(clone_dir), "log", "-1", "--format=%an"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    commit_time = subprocess.run(
        ["git", "-C", str(clone_dir), "log", "-1", "--format=%cI"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    commit_msg = subprocess.run(
        ["git", "-C", str(clone_dir), "log", "-1", "--format=%s"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    logger.info("commit_resolved", sha=commit_sha[:12], author=commit_author)

    # 5. 生成 source_fingerprint（文件树 hash）
    file_hashes = []
    for root, dirs, files in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in sorted(files):
            fp = Path(root) / f
            rel = fp.relative_to(clone_dir)
            file_hashes.append(f"{rel}:{hashlib.sha256(fp.read_bytes()).hexdigest()[:16]}")
    source_fingerprint = hashlib.sha256("\n".join(sorted(file_hashes)).encode()).hexdigest()

    # 统计 Java 文件
    java_files = list(clone_dir.rglob("*.java"))
    java_file_count = len([f for f in java_files if ".git" not in str(f)])

    # 6. 创建 SourceRevision
    if source_rev:
        # 更新已有的占位记录
        source_rev.commit_sha = commit_sha
        source_rev.branch = branch
        source_rev.author = commit_author
        source_rev.commit_time = datetime.fromisoformat(commit_time) if commit_time else None
        source_rev.source_fingerprint = source_fingerprint
    else:
        source_rev = SourceRevision(
            repository_id=repo.id,
            commit_sha=commit_sha,
            branch=branch,
            author=commit_author,
            commit_time=datetime.fromisoformat(commit_time) if commit_time else None,
            source_fingerprint=source_fingerprint,
        )
        db.add(source_rev)
        db.flush()

    # 7. 更新 ScanRun
    scan_run.source_revision_id = source_rev.id
    repo.last_scanned_commit = commit_sha
    db.flush()

    # 8. 更新阶段状态为成功
    if stage:
        stage.status = STAGE_SUCCEEDED
        stage.finished_at = datetime.now(timezone.utc)
        stage.metrics_json = {
            "commit_sha": commit_sha[:12],
            "java_file_count": java_file_count,
            "source_fingerprint": source_fingerprint[:16],
        }

    db.commit()

    logger.info("fetch_succeeded", source_revision_id=source_rev.id, java_files=java_file_count)

    return {
        "status": "SUCCEEDED",
        "output": {
            "source_revision_id": source_rev.id,
            "commit_sha": commit_sha,
            "commit_author": commit_author,
            "commit_message": commit_msg,
            "java_file_count": java_file_count,
            "source_fingerprint": source_fingerprint,
            "source_path": str(clone_dir),
        },
    }


# Celery task 封装（生产环境用）
@celery_app.task(name="sail.FETCH_SOURCE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """Celery task 入口。"""
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return fetch_source(scan_run_id, stage_run_id, db)
