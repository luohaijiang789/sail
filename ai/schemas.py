"""AI 分析层 Pydantic schema 定义。

对应架构文档 06-ai-analysis.md。定义 Evidence Bundle、AI Review 输出、Need 请求
三类核心结构，以及 verdict 枚举常量。所有结构均为 Pydantic v2 模型，供序列化进
``ai_review.response_json`` / ``need_requests_json`` 使用。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# --- verdict 枚举常量（对应 06-ai-analysis.md 结构化输出） ---
VERDICT_TRUE_POSITIVE = "TRUE_POSITIVE"
VERDICT_LIKELY_TRUE_POSITIVE = "LIKELY_TRUE_POSITIVE"
VERDICT_UNCERTAIN = "UNCERTAIN"
VERDICT_LIKELY_FALSE_POSITIVE = "LIKELY_FALSE_POSITIVE"
VERDICT_FALSE_POSITIVE = "FALSE_POSITIVE"
VERDICT_NEED_MORE_CONTEXT = "NEED_MORE_CONTEXT"
VERDICT_INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"

Verdict = Literal[
    "TRUE_POSITIVE",
    "LIKELY_TRUE_POSITIVE",
    "UNCERTAIN",
    "LIKELY_FALSE_POSITIVE",
    "FALSE_POSITIVE",
    "NEED_MORE_CONTEXT",
    "INSUFFICIENT_CONTEXT",
]

Exploitability = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


class EvidenceBundle(BaseModel):
    """AI 审计上下文：从 API 入口出发聚合的全部证据（ADR-18）。

    AI 只读此 Bundle，不实时访问文件系统（ADR-04）。

    Attributes:
        api_asset: API 入口信息（参数/鉴权/校验/Controller/handler）。
        rule: 触发的规则元数据（rule_key/cwe/severity）。
        source: 数据流 source 位置与代码片段。
        sink: 数据流 sink 位置与代码片段。
        call_chain: API 入口到 sink 的调用链，每跳含符号/文件/行/代码片段。
        dataflow_path: CodeQL 数据流路径节点列表。
        resources: 沿调用链访问的资源（DB 表/SQL/HTTP 出站/文件/缓存/队列）。
        security_controls: 入口与调用链上的安全控制（AUTHN/AUTHZ/校验/过滤）。
    """

    api_asset: dict = Field(default_factory=dict)
    rule: dict = Field(default_factory=dict)
    source: dict = Field(default_factory=dict)
    sink: dict = Field(default_factory=dict)
    call_chain: list[dict] = Field(default_factory=list)
    dataflow_path: list[dict] = Field(default_factory=list)
    resources: list[dict] = Field(default_factory=list)
    security_controls: list[dict] = Field(default_factory=list)


class NeedRequest(BaseModel):
    """NEED_MORE_CONTEXT 闭环中 AI 声明缺失的上下文（ADR-19）。

    AI 不主动访问文件系统，只声明需要什么，编排器代为补取后再问。

    Attributes:
        type: 缺失类型，``CODE_SNIPPET`` / ``CALLER`` / ``SECURITY_CONTROL``。
        symbol: 需要的符号（方法/类全限定名）。
        file: 文件路径（可选）。
        lines: 行号范围字符串（如 ``"70-90"``，可选）。
        reason: 为什么需要（供审计与归因）。
    """

    type: Literal["CODE_SNIPPET", "CALLER", "SECURITY_CONTROL"]
    symbol: str
    file: str | None = None
    lines: str | None = None
    reason: str = ""


class AiReviewOutput(BaseModel):
    """AI Review 结构化输出（对应 06-ai-analysis.md 结构化输出与 ai_review 表）。

    Attributes:
        verdict: 判定，见 :data:`Verdict`。
        confidence: 置信度 0.0-1.0。
        exploitability: 可利用性，见 :data:`Exploitability`。
        auth_required: API 是否需要鉴权。
        auth_enforced: 鉴权是否实际生效。
        reachable_from_endpoint: 从 API 入口是否可达 sink。
        reasoning: 四类引导式问题的回答（input_source/path_reachability/sink_constraint/dataflow_integrity）。
        evidence: 引用的证据片段列表（file/lines/description）。
        remediation: 修复建议。
        need: NEED_MORE_CONTEXT 时声明的补取请求列表；否则为空。
    """

    verdict: Verdict
    confidence: float
    exploitability: Exploitability | None = None
    auth_required: bool | None = None
    auth_enforced: bool | None = None
    reachable_from_endpoint: bool | None = None
    reasoning: dict = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)
    remediation: str | None = None
    need: list[NeedRequest] = Field(default_factory=list)
