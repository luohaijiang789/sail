"""指纹计算后处理器。

对应架构文档 05-finding-model.md「指纹与归一化算法（D6 / ADR-09）」。用归一化后的
source/sink/enclosing_method 符号、归一化数据流签名、归一化路径，按固定顺序拼接后
做 sha256，得到 64 位十六进制指纹。指纹抗代码插入删除与变量重命名，供
``finding_candidate.fingerprint`` 字段与跨扫描历史对比使用。

公式::

    fingerprint = sha256(
        rule_id
        + normalize_symbol(source_symbol)
        + normalize_symbol(sink_symbol)
        + normalize_symbol(enclosing_method)
        + normalize_dataflow_signature(dataflow_path)
        + normalize_path(file_path)
    )
"""

from __future__ import annotations

from scanners.postprocessors.base import BasePostprocessor, register_postprocessor
from scanners.postprocessors.symbol_normalizer import (
    normalize_dataflow_signature,
    normalize_path,
    normalize_symbol,
)
from scanners.sarif_parser import FindingCandidateData


def calculate_fingerprint(
    rule_id: str,
    source_symbol: str | None,
    sink_symbol: str | None,
    enclosing_method: str | None,
    dataflow_path: list[dict],
    file_path: str | None,
) -> str:
    """计算 Finding 候选指纹。

    按 05-finding-model.md 的固定顺序拼接归一化值后做 sha256，返回 64 位十六进制小写串。
    各归一化函数对 ``None`` / 空输入返回 ``""``，保证空字段不影响拼接顺序。

    Args:
        rule_id: 规则标识（SARIF ruleId）。
        source_symbol: 数据流 source 符号（原始）。
        sink_symbol: 数据流 sink 符号（原始）。
        enclosing_method: 漏洞所在方法符号（原始），区别于 source_symbol。
        dataflow_path: 数据流路径节点列表。
        file_path: 漏洞所在文件路径（原始）。

    Returns:
        64 位十六进制 sha256 指纹字符串。
    """
    raise NotImplementedError


@register_postprocessor
class FingerprintCalculator(BasePostprocessor):
    """指纹计算后处理器。

    遍历候选列表，用 :func:`calculate_fingerprint` 为每条候选计算指纹并回填到
    ``candidate.fingerprint`` 字段（注意：``FindingCandidateData`` 默认无该字段，
    持久化时由 Worker 写入 ``finding_candidate.fingerprint`` 列；本后处理器通过
    动态属性或扩展字段携带计算结果，调用方据需读取）。

    依赖前置后处理器已做符号/路径归一化——若直接调用本后处理器，``calculate_fingerprint``
    内部仍会对入参符号调用 :func:`normalize_symbol`，结果等价。
    """

    name = "fingerprint_calculator"

    def process(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """为每条候选计算并回填指纹。

        Args:
            candidates: 已经过符号/路径归一化的候选列表。

        Returns:
            带指纹的候选列表（新列表，候选对象为副本）。
        """
        raise NotImplementedError

    @staticmethod
    def _extract_symbols(candidate: FindingCandidateData) -> tuple[str | None, str | None, str | None]:
        """从候选数据抽取 source_symbol / sink_symbol / enclosing_method。

        - source_symbol 取 ``candidate.source_location["symbol"]``。
        - sink_symbol 取 ``candidate.sink_location["symbol"]``。
        - enclosing_method 取 ``candidate.symbol``（漏洞所在方法符号）。

        Returns:
            ``(source_symbol, sink_symbol, enclosing_method)`` 三元组，缺失为 None。
        """
        raise NotImplementedError
