"""FINALIZE Worker。对应架构文档 08-orchestration.md「ScanRun 状态机」。职责：状态收尾 + 产物归档。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.FINALIZE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """扫描收尾：状态机推进、产物归档、报告生成。

    输入：scan_run_id（全流程已完成的扫描）。
    流程：聚合各阶段最终状态，按状态机判定 ScanRun 终态——所有 required 阶段
    成功无降级→SUCCEEDED；有 DEGRADE 或非必需 SKIPPED→PARTIAL_SUCCEEDED；
    任一 required+ABORT 阶段 FAILED_FINAL→FAILED。归档扫描产物（日志、SARIF、
    报告）到对象存储，更新 repository.last_scanned_commit，生成最终扫描报告
    摘要。
    输出：``{"status": "SUCCEEDED", "output": {"scan_run_status": <str>,
    "report_artifact_id": <int>, "summary": {...}}}``。
    required=✓，on_failure=ABORT。
    """
    raise NotImplementedError
