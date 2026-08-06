"""端到端扫描运行脚本（本地同步形态，不依赖 Celery/Redis）。

用法：
    .venv/bin/python scripts/run_scan.py [--git-url URL] [--branch BRANCH] [--name NAME]

默认对本地 WebGoat 克隆执行完整 DAG：fetch → preflight → build → extract →
codeql_scan(降级污点分析) → finding_candidates → assemble_context → ai_analyze
(无 LLM key 走启发式) → merge_findings → assess_security → persist → finalize。

结束后打印三张表摘要与扫描详情查询入口。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 确保仓库根在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.create_scan import create_scan
from app.application.orchestrate_scan import run_scan_synchronous
from app.core.logging import setup_logging, get_logger
from app.domain.api_asset import ApiAsset
from app.domain.check_and_security import ApiCheck, ApiSecurityProfile
from app.domain.finding import Finding, FindingInstance
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_SUCCEEDED
from app.domain.source_assets import Project, Repository
from app.infrastructure.database import SessionLocal, engine
from app.domain import Base  # noqa: F401  ensure models registered

logger = get_logger("RunScan")


def ensure_schema() -> None:
    """建表（SQLite 本地开发；生产走 Alembic）。"""
    Base.metadata.create_all(engine)


def ensure_repo(db: Session, name: str, git_url: str, branch: str) -> tuple[int, int]:
    """确保 Project + Repository 存在，返回 (project_id, repository_id)。"""
    project = db.execute(select(Project).where(Project.name == name)).scalar_one_or_none()
    if not project:
        project = Project(name=name, description=f"SAIL test target: {name}")
        db.add(project)
        db.flush()
    repo = db.execute(
        select(Repository).where(Repository.git_url == git_url)
    ).scalar_one_or_none()
    if not repo:
        repo = Repository(
            project_id=project.id, name=name, git_url=git_url,
            default_branch=branch, repository_type="git", status="ACTIVE",
        )
        db.add(repo)
        db.flush()
    db.commit()
    return project.id, repo.id


def print_summary(db: Session, scan_run_id: int) -> None:
    scan = db.get(ScanRun, scan_run_id)
    print("\n" + "=" * 60)
    print(f"扫描完成：ScanRun #{scan_run_id}  状态={scan.status}  进度={scan.progress}%")
    print(f"  build_quality={scan.build_quality}")
    print("-" * 60)

    api_count = db.execute(select(func.count()).select_from(ApiAsset)
                           .where(ApiAsset.scan_run_id == scan_run_id)).scalar()
    check_count = db.execute(select(func.count()).select_from(ApiCheck)
                             .where(ApiCheck.scan_run_id == scan_run_id)).scalar()
    profile_count = db.execute(select(func.count()).select_from(ApiSecurityProfile)
                               .where(ApiSecurityProfile.scan_run_id == scan_run_id)).scalar()
    finding_count = db.execute(select(func.count()).select_from(FindingInstance)
                               .where(FindingInstance.scan_run_id == scan_run_id)).scalar()
    print(f"  ① API 资产表：{api_count} 个 API")
    print(f"  ② check 表：{check_count} 条检查结果（{profile_count} 个安全画像）")
    print(f"  ③ result 表：{finding_count} 个漏洞实例")
    print("-" * 60)

    # 阶段时间线
    stages = db.execute(select(ScanStageRun)
                        .where(ScanStageRun.scan_run_id == scan_run_id)
                        .order_by(ScanStageRun.id)).scalars().all()
    print("  阶段时间线：")
    for s in stages:
        m = s.metrics_json or {}
        extra = ""
        if s.stage_type == "EXTRACT_API_FACTS":
            extra = f" → {m.get('api_assets_created', 0)} APIs"
        elif s.stage_type == "RUN_CODEQL_VULN_SCAN":
            extra = f" → {m.get('scanner_id')} {m.get('result_count', 0)} results"
        elif s.stage_type == "FINDING_CANDIDATES":
            extra = f" → {m.get('candidate_count', 0)} candidates"
        elif s.stage_type == "AI_ANALYZE":
            extra = f" → {m.get('engine')} {m.get('analyzed_count', 0)} analyzed"
        elif s.stage_type == "PERSIST_RESULTS":
            extra = f" → {m.get('persisted_count', 0)} persisted"
        print(f"    {s.status:16s}  {s.stage_type:28s}{extra}")

    # 漏洞清单
    print("-" * 60)
    print("  漏洞清单：")
    instances = db.execute(
        select(FindingInstance).where(FindingInstance.scan_run_id == scan_run_id)
    ).scalars().all()
    for inst in instances:
        finding = db.get(Finding, inst.finding_id)
        print(f"    [{inst.final_severity or inst.raw_severity:8s}] {finding.title if finding else '?'}"
              f"  ({inst.file_path}:{inst.start_line})  ai={inst.ai_verdict}")
    print("=" * 60)
    print(f"\n查看详情：curl http://localhost:8000/api/scans/{scan_run_id}")
    print(f"         curl http://localhost:8000/api/api-assets?scan_run_id={scan_run_id}")
    print(f"         curl http://localhost:8000/api/findings?repository_id={scan.repository_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SAIL 端到端扫描")
    parser.add_argument("--name", default="WebGoat")
    parser.add_argument("--git-url", default="file:///tmp/webgoat",
                        help="git 仓库 URL（默认本地 WebGoat 克隆）")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args()

    setup_logging()
    ensure_schema()

    with SessionLocal() as db:
        _, repo_id = ensure_repo(db, args.name, args.git_url, args.branch)
        print(f"仓库就绪：{args.name} (repo_id={repo_id}, git_url={args.git_url})")

        scan_run = create_scan(
            db=db, repository_id=repo_id,
            revision={"type": "branch", "value": args.branch},
            scan_profile_id=None, ai_analysis=True,
        )
        scan_run_id = scan_run.id
        print(f"扫描已创建：ScanRun #{scan_run_id}，开始执行 DAG...")

    # 编排在独立 session 中运行
    final_status = run_scan_synchronous(scan_run_id)

    with SessionLocal() as db:
        print_summary(db, scan_run_id)

    sys.exit(0 if final_status in ("SUCCEEDED", "PARTIAL_SUCCEEDED") else 1)


if __name__ == "__main__":
    main()
