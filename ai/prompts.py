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


def build_verification_prompt(bundle: dict) -> str:
    """构建单候选验证 prompt（worker 直接消费的 dict 形态 bundle）。

    把 Evidence Bundle 摘要 + 四类引导式问题拼成 prompt，要求 LLM 返回
    AiReviewOutput 兼容的 JSON。
    """
    import json
    api = bundle.get("api_asset") or {}
    summary = {
        "rule_id": bundle.get("rule_id"),
        "severity": bundle.get("severity"),
        "file_path": bundle.get("file_path"),
        "api": {"method": api.get("http_method"), "path": api.get("path"),
                "controller": api.get("controller"), "handler": api.get("handler")},
        "source": bundle.get("source"),
        "sink": bundle.get("sink"),
        "dataflow_steps": len(bundle.get("dataflow_path") or []),
        "security_controls": bundle.get("security_controls"),
    }
    guided = "\n".join(f"- {k}: {v}" for k, v in GUIDED_QUESTIONS.items())
    return (
        "你是 Java Web 安全审计专家。基于以下 Evidence Bundle 判断该漏洞候选是否为真实可利用漏洞。\n"
        "不要顺着扫描器认定漏洞，独立验证 source→sink 数据流完整性。\n\n"
        f"Evidence Bundle:\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
        f"Source 代码片段:\n{bundle.get('source_code_snippet', '')}\n\n"
        f"Sink 代码片段:\n{bundle.get('sink_code_snippet', '')}\n\n"
        f"数据流路径:\n{json.dumps(bundle.get('dataflow_path') or [], ensure_ascii=False, indent=2)}\n\n"
        f"引导式问题（逐项回答）：\n{guided}\n\n"
        "返回严格 JSON：{\"verdict\": \"TRUE_POSITIVE|LIKELY_TRUE_POSITIVE|UNCERTAIN|"
        "LIKELY_FALSE_POSITIVE|FALSE_POSITIVE|NEED_MORE_CONTEXT|INSUFFICIENT_CONTEXT\", "
        "\"confidence\": 0.0-1.0, \"exploitability\": \"HIGH|MEDIUM|LOW|NONE\", "
        "\"auth_required\": bool, \"auth_enforced\": bool, \"reachable_from_endpoint\": bool, "
        "\"reasoning\": {\"input_source\":\"\",\"path_reachability\":\"\",\"sink_constraint\":\"\","
        "\"dataflow_integrity\":\"\"}, \"evidence\": [], \"remediation\": \"\", \"need\": []}"
    )


def build_prompt(evidence_bundle: EvidenceBundle, checks_to_verify: list) -> str:
    """构建深度验证完整 prompt（ADR-21 同 API 合并验证）。

    按同 API 合并：Evidence Bundle 摘要 + 四类引导式问题 + 检查项清单。
    """
    import json
    guided = "\n".join(f"- {k}: {v}" for k, v in GUIDED_QUESTIONS.items())
    checks = [c if isinstance(c, dict) else {"key": str(c)} for c in checks_to_verify]
    return (
        "你是 Java Web 安全审计专家。基于 Evidence Bundle 逐项验证以下检查项是否为真实漏洞。\n"
        f"Evidence Bundle:\n{json.dumps(evidence_bundle.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
        f"待验证检查项:\n{json.dumps(checks, ensure_ascii=False, indent=2)}\n\n"
        f"引导式问题：\n{guided}\n\n返回 JSON 数组，每项一个 AiReviewOutput。"
    )


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
