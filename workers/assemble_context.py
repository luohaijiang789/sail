"""ASSEMBLE_CONTEXT Worker。对应架构文档 06-ai-analysis.md「从 API 入口出发验证」。职责：从 API 入口出发为每个 FindingCandidate 构建 Evidence Bundle。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.ASSEMBLE_CONTEXT")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """为每个 FindingCandidate 预取 Evidence Bundle。

    输入：candidate_ids + api_asset_ids。
    流程：不从告警行出发，从 API 入口出发（ADR-18）——通过
    finding_candidate.api_asset_id 定位 API，沿调用链
    （入口→...→source→sink）拼装审计上下文：入口信息（参数/鉴权/校验）+
    完整调用链每跳代码片段 + Source/Sink 代码 + 数据流路径 + 安全控制 +
    资源访问。漏洞无法关联到 API 时退化为从告警行出发。
    输出：``{"status": "SUCCEEDED", "output": {"evidence_bundle_ids":
    [<int>...], "assembled_count": <int>}}``。
    required=✗，on_failure=CONTINUE：失败时对应 candidate 无 evidence，
    AI_ANALYZE 以 INSUFFICIENT_CONTEXT 处理。
    """
    raise NotImplementedError
