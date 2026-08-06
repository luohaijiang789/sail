"""SARIF 解析器：把 CodeQL 产出的 SARIF 转为 FindingCandidate 原始数据。

对应架构文档 05-finding-model.md 的 ``FINDING_CANDIDATES`` 阶段。解析 SARIF results，
提取 rule_id/severity/位置/symbol/source/sink/dataflow_path，供后续指纹计算、
API 资产关联（``api_asset_id``）与 AI Evidence 拼装使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FindingCandidateData:
    """单条 Finding 候选原始数据（对应 finding_candidate 表字段）。

    Attributes:
        rule_id: 规则标识（SARIF ruleId，落库时映射到 ``rule.id``）。
        severity: 原始严重度，``INFO`` / ``LOW`` / ``MEDIUM`` / ``HIGH`` / ``CRITICAL``。
        file_path: 漏洞所在文件绝对路径。
        start_line: 起始行号（1-based）。
        end_line: 结束行号（1-based）。
        symbol: 漏洞所在方法/类符号（完全限定名）。
        source_location: 数据流 source 位置 ``{"file":..., "line":..., "symbol":...}``。
        sink_location: 数据流 sink 位置 ``{"file":..., "line":..., "symbol":...}``。
        dataflow_path: 数据流路径节点列表，每节点含位置与方法签名。
    """

    rule_id: str
    severity: str
    file_path: str
    start_line: int
    end_line: int
    symbol: str | None = None
    source_location: dict = field(default_factory=dict)
    sink_location: dict = field(default_factory=dict)
    dataflow_path: list[dict] = field(default_factory=list)


def parse_sarif(sarif_path: str) -> list[FindingCandidateData]:
    """解析 SARIF 文件，提取所有 results 为候选数据。

    Args:
        sarif_path: SARIF 文件绝对路径。

    Returns:
        :class:`FindingCandidateData` 列表，按 SARIF results 顺序排列。

    Raises:
        ValueError: SARIF 格式不符合规范。
    """
    raise NotImplementedError
