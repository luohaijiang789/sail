"""Prompt 模板：引导式提问 + Evidence Bundle 拼装 + 快速过滤 + 反馈归因。

对应架构文档 06-ai-analysis.md。所有 prompt 带版本号 ``PROMPT_VERSION``，
缓存键依赖 prompt_version（``cache_key = sha256(... + prompt_version)``）。
"""

from __future__ import annotations

from ai.schemas import EvidenceBundle

PROMPT_VERSION = "1.0"

# 四类引导式问题（对应 06-ai-analysis.md Guided Questions）。
# 强制 AI 不顺着 CodeQL 认定漏洞，逐类回答。
GUIDED_QUESTIONS: dict[str, str] = {
    "input_source": "输入来源：用户输入从哪个 API 参数进入？类型是什么？校验是否充分？",
    "path_reachability": "路径可达性：API 是否需要鉴权？鉴权是否生效？是否外网可达？",
    "sink_constraint": "Sink 约束：是否使用参数化查询？调用链上有没有 sanitizer？",
    "dataflow_integrity": "数据流完整性：source→sink 路径是否完整？中间有无类型转换或净化？",
}


def build_prompt(evidence_bundle: EvidenceBundle, checks_to_verify: list) -> str:
    """构建深度验证完整 prompt。

    按 ADR-21 同 API 合并验证：把同一 API 的多个检查项合并成一次 LLM 调用，
    AI 逐项验证。prompt 含 Evidence Bundle 摘要 + 四类引导式问题 + 检查项清单。

    Args:
        evidence_bundle: 从 API 入口聚合的 :class:`EvidenceBundle`。
        checks_to_verify: 待验证的检查项列表（非 PASS 项）。

    Returns:
        完整 prompt 字符串。
    """
    raise NotImplementedError


def build_fast_filter_prompt(check_item, codeql_result, sink_code: str) -> str:
    """构建小模型快速过滤 prompt（ADR-23）。

    小模型快速过滤明显误报，返回 ``FALSE_POSITIVE`` 直接结案；不确定的交给深度验证。

    Args:
        check_item: 单个检查项（含 rule_key/severity）。
        codeql_result: CodeQL 候选数据（含 source/sink/dataflow 摘要）。
        sink_code: sink 处代码片段。

    Returns:
        快速过滤 prompt 字符串。
    """
    raise NotImplementedError


def build_feedback_analysis_prompt(feedback_data) -> str:
    """构建反馈归因 prompt（ADR-24）。

    强 LLM 对人工反馈做归因，输出 root_cause 与改进建议
    （PROMPT/RULE/PATTERN/NO_CHANGE 四类）。

    Args:
        feedback_data: 反馈记录（含人工 verdict/reason 与 AI 原始结论/CodeQL 结论）。

    Returns:
        反馈归因 prompt 字符串。
    """
    raise NotImplementedError
