"""LLM 分析器：漏斗式验证 + 同 API 合并 + NEED_MORE_CONTEXT 闭环。

对应架构文档 06-ai-analysis.md。

- :func:`analyze_api` —— 同 API 多检查项合并验证（ADR-21），AI 逐项验证，token 降 3-5 倍。
- :func:`fast_filter` —— 小模型快速过滤（ADR-23），明显误报直接结案，None 表示交给深度验证。
- :func:`_call_llm` —— LLM API 调用 stub。
- :func:`_run_need_more_context_loop` —— NEED_MORE_CONTEXT 受控多轮闭环（ADR-19，最多 3 轮）。
"""

from __future__ import annotations

from ai.schemas import AiReviewOutput, EvidenceBundle


def analyze_api(api_asset_id: int, checks_to_verify: list) -> list[AiReviewOutput]:
    """同一 API 的非 PASS 检查项合并成一次 LLM 调用，AI 逐项验证（ADR-21）。

    Args:
        api_asset_id: API 资产 ID。
        checks_to_verify: 待验证检查项列表（非 PASS 项）。

    Returns:
        每个检查项一个 :class:`AiReviewOutput`。
    """
    raise NotImplementedError


def fast_filter(check_item, evidence: EvidenceBundle) -> AiReviewOutput | None:
    """小模型快速过滤（ADR-23）。

    Args:
        check_item: 单个检查项。
        evidence: 该检查项的 :class:`EvidenceBundle`。

    Returns:
        ``AiReviewOutput`` 表示小模型已判定（通常为 FALSE_POSITIVE 直接结案）；
        ``None`` 表示小模型不确定，交给深度验证。
    """
    raise NotImplementedError


def _call_llm(prompt: str, model: str, temperature: float = 0.0) -> str:
    """LLM API 调用 stub。

    Args:
        prompt: 完整 prompt 字符串。
        model: 模型名（强模型 ``llm_model_strong`` / 快模型 ``llm_model_fast``）。
        temperature: 采样温度，默认 0.0（审计场景需确定性）。

    Returns:
        LLM 原始响应字符串。
    """
    raise NotImplementedError


def _run_need_more_context_loop(
    bundle: EvidenceBundle, first_result: AiReviewOutput
) -> AiReviewOutput:
    """NEED_MORE_CONTEXT 受控多轮闭环（ADR-19，最多 3 轮）。

    第一轮结果为 ``NEED_MORE_CONTEXT`` 时，按其 ``need`` 列表补取证据后再问，
    直到产出终态 verdict 或达到 3 轮上限（退化为 ``INSUFFICIENT_CONTEXT``）。

    Args:
        bundle: 第一轮的 Evidence Bundle。
        first_result: 第一轮的 :class:`AiReviewOutput`。

    Returns:
        终态 :class:`AiReviewOutput`。
    """
    raise NotImplementedError
