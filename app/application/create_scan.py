"""创建扫描的应用服务。

负责：校验仓库存在 → 创建占位 SourceRevision（commit_sha 待 fetch 填充）
→ 创建 ScanRun（CREATED）→ 按 STAGE_DEFINITIONS 批量创建所有 ScanStageRun
（PENDING / attempt=0，required 与 on_failure 取自定义表）→ 提交首个 Celery 任务。
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import RepositoryNotFoundError
from app.core.logging import get_logger
from app.domain.scan_run import (
    SCAN_RUN_CREATED,
    SCAN_RUN_QUEUED,
    STAGE_DEFINITIONS,
    STAGE_PENDING,
    ScanRun,
    ScanStageRun,
)
from app.domain.source_assets import Repository, SourceRevision

logger = get_logger(__name__)


def create_scan(
    db: Session,
    repository_id: int,
    revision: str,
    scan_profile_id: int | None,
    ai_analysis: bool,
) -> ScanRun:
    """创建一次扫描并派发首个阶段任务。

    Args:
        db: SQLAlchemy session，由路由层注入。
        repository_id: 仓库 ID。
        revision: 版本引用值（分支名 / Tag 名 / commit SHA），由调用方从 RevisionRef 解析。
        scan_profile_id: 扫描配置 ID，可为空走默认。
        ai_analysis: 是否开启 AI 分析阶段（影响可选阶段是否实际执行，此处仅记录语义，
            阶段创建仍按 STAGE_DEFINITIONS 全量创建，由编排器按 on_failure 决定降级）。

    Returns:
        新建的 ScanRun 记录（已 flush，含 id）。所有 ScanStageRun 已一并创建。
    """
    # 1. 校验仓库存在
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise RepositoryNotFoundError(f"Repository {repository_id} not found")

    # 2. 创建占位 SourceRevision（commit_sha 待 fetch 填充）
    # revision 可能是 dict {"type": "branch", "value": "main"} 或字符串
    if isinstance(revision, dict):
        rev_type = revision.get("type", "branch")
        rev_value = revision.get("value", "main")
    else:
        rev_type = "commit" if len(str(revision)) == 40 else "branch"
        rev_value = str(revision)

    source_revision = SourceRevision(
        repository_id=repository.id,
        commit_sha=rev_value if rev_type == "commit" else None,  # commit 则直接填，branch 待 fetch
        branch=rev_value if rev_type == "branch" else None,
        tag=rev_value if rev_type == "tag" else None,
    )
    db.add(source_revision)
    db.flush()  # 取到 source_revision.id

    # 3. 创建 ScanRun
    scan_run = ScanRun(
        project_id=repository.project_id,
        repository_id=repository.id,
        source_revision_id=source_revision.id,
        scan_profile_id=scan_profile_id,
        trigger_type="MANUAL",
        status=SCAN_RUN_CREATED,
        progress=0,
        mode="FULL",
    )
    db.add(scan_run)
    db.flush()  # 取到 scan_run.id

    # 4. 按 STAGE_DEFINITIONS 创建所有 ScanStageRun
    for stage_type, definition in STAGE_DEFINITIONS.items():
        stage_run = ScanStageRun(
            scan_run_id=scan_run.id,
            stage_type=stage_type,
            status=STAGE_PENDING,
            attempt=0,
            max_attempts=3,
            required=definition["required"],
            on_failure=definition["on_failure"],
        )
        db.add(stage_run)
    db.flush()

    logger.info(
        "scan_created",
        scan_run_id=scan_run.id,
        repository_id=repository.id,
        source_revision_id=source_revision.id,
        revision=revision,
        ai_analysis=ai_analysis,
    )

    # 5. 提交首个 Celery 任务 start_scan(scan_run_id)。
    # 后台 Celery 不一定连上 Redis，先 print 模拟派发，并置 QUEUED。
    _dispatch_start_scan(scan_run.id)

    scan_run.status = SCAN_RUN_QUEUED
    db.commit()

    return scan_run


def _looks_like_commit_sha(value: str) -> bool:
    """粗判 revision 是否为 commit SHA（40 位十六进制）。"""
    if len(value) < 7:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in value)


def _dispatch_start_scan(scan_run_id: int) -> None:
    """派发 start_scan 任务。

    优先通过 Celery ``send_task("sail.start_scan")`` 派发；若 Celery 不可用
    （Redis 未连、broker 报错）则回退到 print 模拟，保证本地开发不阻塞。
    消息只传 scan_run_id（ADR-03），状态机在 ScanRun 上。
    """
    try:
        from workers.celery_app import celery_app

        celery_app.send_task("sail.start_scan", args=[scan_run_id], queue="scan_orchestrator")
        logger.info("start_scan_dispatched_via_celery", scan_run_id=scan_run_id)
    except Exception:  # noqa: BLE001  Celery / Redis 不可用时回退
        print(f"[create_scan] would dispatch start_scan(scan_run_id={scan_run_id})")
        logger.info("start_scan_dispatched_fallback", scan_run_id=scan_run_id)
