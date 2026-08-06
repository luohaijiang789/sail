"""后处理器包：对 SARIF 解析后的 FindingCandidateData 做统一处理。

导出全部后处理器类、归一化函数、流水线与注册表。导入本包即触发各后处理器
通过 ``@register_postprocessor`` 装饰器登记到 :data:`postprocessor_registry`，
:func:`default_pipeline` 据此构造默认流水线。

导入顺序即注册顺序，决定流水线执行序：
1. :class:`PathNormalizer` —— 路径归一化
2. :class:`SymbolNormalizer` —— 符号归一化
3. :class:`FingerprintCalculator` —— 指纹计算（依赖前两步归一化结果）
4. :class:`Deduplicator` —— 扫描内去重（依赖指纹）

对应架构文档 05-finding-model.md「指纹与归一化算法」与 ``FINDING_CANDIDATES`` 阶段。
"""

from __future__ import annotations

# 顺序导入各后处理器模块，触发 @register_postprocessor 注册。
# 导入序即注册序，pipeline.default_pipeline() 据此决定执行顺序。
from scanners.postprocessors.base import (
    BasePostprocessor,
    PostprocessorRegistry,
    postprocessor_registry,
    register_postprocessor,
)
from scanners.postprocessors.path_normalizer import PathNormalizer
from scanners.postprocessors.symbol_normalizer import (
    SymbolNormalizer,
    normalize_dataflow_signature,
    normalize_path,
    normalize_symbol,
)
from scanners.postprocessors.fingerprint_calculator import (
    FingerprintCalculator,
    calculate_fingerprint,
)
from scanners.postprocessors.deduplicator import Deduplicator
from scanners.postprocessors.pipeline import PostprocessPipeline, default_pipeline

__all__ = [
    # 基类与注册表
    "BasePostprocessor",
    "PostprocessorRegistry",
    "postprocessor_registry",
    "register_postprocessor",
    # 后处理器实现
    "PathNormalizer",
    "SymbolNormalizer",
    "FingerprintCalculator",
    "Deduplicator",
    # 归一化函数
    "normalize_symbol",
    "normalize_dataflow_signature",
    "normalize_path",
    # 指纹计算
    "calculate_fingerprint",
    # 流水线
    "PostprocessPipeline",
    "default_pipeline",
]
