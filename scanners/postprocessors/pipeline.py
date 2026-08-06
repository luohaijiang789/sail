"""后处理流水线：按顺序执行所有后处理器。

对应架构文档 05-finding-model.md 的 ``FINDING_CANDIDATES`` 阶段。SARIF 解析产出
:class:`FindingCandidateData` 列表后，:class:`PostprocessPipeline.run` 依次执行：
路径标准化 → 符号标准化 → 指纹计算 → 扫描内去重，产出可直接落库的候选列表。

流水线顺序敏感：
- ``path_normalizer`` 与 ``symbol_normalizer`` 必须先于 ``fingerprint_calculator``，
  保证指纹基于归一化值。
- ``fingerprint_calculator`` 必须先于 ``deduplicator``，去重依赖指纹。
顺序由各后处理器的注册顺序决定（见 :mod:`scanners.postprocessors.__init__` 的导入序）。
"""

from __future__ import annotations

from scanners.postprocessors.base import BasePostprocessor, postprocessor_registry
from scanners.sarif_parser import FindingCandidateData


class PostprocessPipeline:
    """后处理流水线。

    按构造时给定的后处理器顺序串行执行 :meth:`run`，前一个的输出作为后一个的输入。

    Attributes:
        postprocessors: 后处理器实例列表，按执行顺序排列。
    """

    def __init__(self, postprocessors: list[BasePostprocessor] | None = None) -> None:
        """初始化流水线。

        Args:
            postprocessors: 后处理器实例列表。为 ``None`` 时调用
                :func:`default_pipeline` 取全部默认后处理器（按注册顺序）。
        """
        self.postprocessors: list[BasePostprocessor] = (
            postprocessors if postprocessors is not None else default_pipeline().postprocessors
        )

    def run(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """按顺序对所有候选执行后处理。

        Args:
            candidates: SARIF 解析产出的原始候选列表。

        Returns:
            经全部后处理器处理后的候选列表。
        """
        raise NotImplementedError


def default_pipeline() -> PostprocessPipeline:
    """返回含全部默认后处理器的流水线。

    通过 :data:`postprocessor_registry.create_all` 取所有已注册后处理器（按注册顺序）。
    注册顺序由 :mod:`scanners.postprocessors.__init__` 的模块导入序保证：
    ``path_normalizer`` → ``symbol_normalizer`` → ``fingerprint_calculator`` → ``deduplicator``。

    Returns:
        装配好的 :class:`PostprocessPipeline` 实例。
    """
    # 触发各后处理器模块导入并完成注册（若尚未导入）。
    import scanners.postprocessors  # noqa: F401

    return PostprocessPipeline(postprocessors=postprocessor_registry.create_all())
