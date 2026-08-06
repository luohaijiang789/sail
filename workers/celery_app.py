"""SAIL Celery 实例与队列路由。

对应架构文档 08-orchestration.md。职责：构建 Celery 应用、声明阶段队列、
按 stage_type 将任务路由到对应队列。
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

# 阶段 → 队列映射。编排器派发任务时按 stage_type 路由。
STAGE_QUEUE_MAP: dict[str, str] = {
    "FETCH_SOURCE": "source_fetch",
    "PREFLIGHT": "scan_orchestrator",
    "BUILD_CODEQL_DATABASE": "java_build_jdk17",
    "EXTRACT_API_FACTS": "source_extract",
    "ENRICH_API_DEPTH": "source_extract",
    "RUN_CODEQL_VULN_SCAN": "codeql_query",
    "FINDING_CANDIDATES": "codeql_query",
    "ASSEMBLE_CONTEXT": "ai_analysis",
    "AI_ANALYZE": "ai_analysis",
    "MERGE_FINDINGS": "result_process",
    "ASSESS_API_SECURITY": "result_process",
    "PERSIST_RESULTS": "result_process",
    "FINALIZE": "maintenance",
}

# 全部队列声明，供 worker -Q 启动参数使用。
SCAN_QUEUES: list[str] = [
    "scan_orchestrator",
    "source_fetch",
    "source_extract",
    "java_build_jdk17",
    "codeql_query",
    "ai_analysis",
    "result_process",
    "maintenance",
]


def task_router(name: str, args, kwargs, options, task=None, **kw) -> dict:
    """按 task name 中的 stage_type 路由到对应队列。

    task name 形如 ``sail.<STAGE_TYPE>``。未识别的 stage 落到默认队列
    ``scan_orchestrator``。
    """
    stage_type = name[len("sail."):] if name.startswith("sail.") else name
    return {"queue": STAGE_QUEUE_MAP.get(stage_type, "scan_orchestrator")}


celery_app = Celery(
    "sail",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_default_queue="scan_orchestrator",
    task_queues={name: {"name": name} for name in SCAN_QUEUES},
    task_routes=(task_router,),
    # Celery 消息只传 scan_run_id + stage_run_id（ADR-03），状态机在 ScanRun 上。
    task_always_eager=False,
    task_eager_propagates=False,
    worker_max_tasks_per_child=50,
)
