"""路径标准化后处理器。

对应架构文档 05-finding-model.md 的 ``normalize_path`` 规则：POSIX 相对路径，去 ``./``，
保留模块前缀。统一 :class:`FindingCandidateData` 的 ``file_path``、``source_location.file``、
``sink_location.file`` 以及 ``dataflow_path`` 各节点的 ``file``，使后续指纹计算与跨扫描
历史对比不受绝对路径、``./`` 前缀、Windows 反斜杠干扰。
"""

from __future__ import annotations

from scanners.postprocessors.base import BasePostprocessor, register_postprocessor
from scanners.sarif_parser import FindingCandidateData


def _normalize_path(file_path: str | None) -> str:
    """归一化路径的薄封装：延迟导入 :func:`normalize_path` 避免模块加载顺序耦合。

    ``normalize_path`` 定义在 ``symbol_normalizer`` 模块中，但若在模块顶部导入，
    会触发 ``symbol_normalizer`` 先于本模块注册到 :data:`postprocessor_registry`，
    打乱流水线顺序（要求 path_normalizer 先于 symbol_normalizer）。故在此延迟导入。
    """
    from scanners.postprocessors.symbol_normalizer import normalize_path

    return normalize_path(file_path)


@register_postprocessor
class PathNormalizer(BasePostprocessor):
    """路径标准化后处理器。

    将候选数据中所有文件路径统一为 POSIX 相对路径，去 ``./`` 前缀，保留模块前缀。
    归一化算法见 :func:`scanners.postprocessors.symbol_normalizer.normalize_path`。
    """

    name = "path_normalizer"

    def process(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """对候选列表做路径标准化。

        处理范围：
        - ``candidate.file_path``
        - ``candidate.source_location["file"]``（若存在）
        - ``candidate.sink_location["file"]``（若存在）
        - ``candidate.dataflow_path[*]["file"]``（每个节点）

        Args:
            candidates: SARIF 解析产出的候选列表。

        Returns:
            路径归一化后的候选列表（新列表，候选对象为副本，不修改入参）。
        """
        raise NotImplementedError

    @staticmethod
    def _normalize_location(location: dict) -> dict:
        """归一化单个 location dict 的 ``file`` 字段，返回副本。"""
        raise NotImplementedError
