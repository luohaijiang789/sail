"""Evidence Bundle 构建器：从 API 入口出发聚合审计上下文。

对应架构文档 06-ai-analysis.md（ADR-18 从 API 入口出发验证）。把 API 资产、规则、
source/sink、调用链、数据流路径、资源访问、安全控制聚合成 :class:`EvidenceBundle`，
供 AI 只读消费（ADR-04）。NEED_MORE_CONTEXT 闭环中按 AI 声明的 Need 列表补取证据。
"""

from __future__ import annotations

from ai.schemas import EvidenceBundle, NeedRequest


def build_evidence_bundle(candidate_id: int, api_asset_id: int) -> EvidenceBundle:
    """从 API 入口出发为某个 Finding 候选构建 Evidence Bundle。

    若 ``api_asset_id`` 为空（漏洞无法关联到 API），退化为从告警行出发。

    Args:
        candidate_id: ``finding_candidate.id``。
        api_asset_id: 关联的 ``api_asset.id``，可为 0/None 表示无关联。

    Returns:
        填充好的 :class:`EvidenceBundle`。
    """
    raise NotImplementedError


def enrich_evidence(
    bundle: EvidenceBundle, need_requests: list[NeedRequest]
) -> EvidenceBundle:
    """NEED_MORE_CONTEXT 闭环补取证据（ADR-19）。

    AI 声明缺什么（CODE_SNIPPET/CALLER/SECURITY_CONTROL），编排器代为补取后回填 Bundle，
    受控多轮（最多 3 轮，每轮 ≤2000 行）。AI 不主动访问文件系统。

    Args:
        bundle: 上一轮的 Evidence Bundle。
        need_requests: AI 声明的补取请求列表。

    Returns:
        补取后的新 :class:`EvidenceBundle`。
    """
    raise NotImplementedError
