"""ScanRun 状态机编排器。

API 进程内的编排逻辑（非 Worker）。按 DAG 拓扑序派发阶段：上游全部 SUCCEEDED
后才派发下游；Worker 通过 HTTP 回调通知完成/失败。
详见 docs/08-orchestration.md「Orchestrator」一节。
"""

from app.domain.scan_run import STAGE_DEFINITIONS, STAGE_DEPENDENCIES


def start_scan(scan_run_id: int) -> None:
    """启动扫描：将 ScanRun 置 RUNNING，按 DAG 拓扑序派发首批可执行阶段。"""
    raise NotImplementedError


def on_stage_complete(stage_run_id: int, output_artifact_id: int, metrics: dict) -> None:
    """Worker 完成回调：标记阶段 SUCCEEDED，记录产出制品与指标，推进下游。"""
    raise NotImplementedError


def on_stage_fail(
    stage_run_id: int,
    error_code: str,
    error_message: str,
    retryable: bool,
) -> None:
    """Worker 失败回调：按 retryable 走重试或 FAILED_FINAL，并按 on_failure 决定降级/中止。"""
    raise NotImplementedError


def _advance_scan(scan_run_id: int) -> None:
    """检查下游阶段是否可派发（上游全 SUCCEEDED 或已 SKIPPED），派发就绪阶段。"""
    raise NotImplementedError


def _check_idempotent(stage_run_id: int) -> bool:
    """幂等检查：该阶段是否已 SUCCEEDED 且 input_fingerprint 匹配。"""
    raise NotImplementedError


def _compute_scan_run_status(scan_run_id: int) -> str:
    """根据所有 ScanStageRun 状态计算 ScanRun 最终状态。

    全 required 成功无降级 → SUCCEEDED；
    全 required 成功但有 DEGRADE/SKIPPED → PARTIAL_SUCCEEDED；
    任一 required+ABORT 阶段 FAILED_FINAL → FAILED。
    """
    raise NotImplementedError


# 引用阶段定义与依赖，便于在模块内做拓扑排序与降级判定。
_ = (STAGE_DEFINITIONS, STAGE_DEPENDENCIES)
