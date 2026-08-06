"""后处理器基类与注册表。

对应架构文档 05-finding-model.md 的 ``FINDING_CANDIDATES`` 阶段。SARIF 经
:func:`scanners.sarif_parser.parse_sarif` 解析为 :class:`FindingCandidateData` 列表后，
由后处理器做统一处理：路径标准化、符号标准化、指纹计算、扫描内去重。
每个后处理器只关注一类归一化/合并逻辑，彼此可插拔、可组合成流水线。

注册表模式：每个后处理器子类用 ``@register_postprocessor`` 装饰后自动登记到
:data:`postprocessor_registry`，:func:`scanners.postprocessors.pipeline.default_pipeline`
据此构造默认流水线，新增后处理器无需改动 pipeline 代码。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from scanners.sarif_parser import FindingCandidateData


class BasePostprocessor(ABC):
    """后处理器抽象基类。

    子类需声明 :attr:`name`（唯一标识，用于注册表与日志）并实现 :meth:`process`。
    实现应保持无状态：输入候选列表的副本，返回新列表，不修改入参。

    Attributes:
        name: 后处理器唯一名称，如 ``"path_normalizer"``。
    """

    #: 后处理器唯一名称，子类必须覆写。
    name: str = "base"

    @abstractmethod
    def process(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """对候选列表执行后处理。

        Args:
            candidates: SARIF 解析产出的 :class:`FindingCandidateData` 列表。

        Returns:
            处理后的候选列表（可为新列表或入参副本，长度可能变化，如去重会缩减）。
        """
        raise NotImplementedError


class PostprocessorRegistry:
    """后处理器注册中心。

    维护 ``name -> postprocessor_cls`` 映射。:func:`default_pipeline` 据此枚举全部
    默认后处理器构造流水线。

    Attributes:
        _registry: ``{name: postprocessor_cls}`` 映射，按注册顺序。
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[BasePostprocessor]] = {}

    def register(self, postprocessor_cls: type[BasePostprocessor]) -> type[BasePostprocessor]:
        """注册后处理器类。

        Args:
            postprocessor_cls: :class:`BasePostprocessor` 子类。

        Returns:
            原样返回入参，便于作为装饰器使用。

        Raises:
            ValueError: ``postprocessor_cls.name`` 为空或重复注册同名后处理器。
        """
        name = getattr(postprocessor_cls, "name", "")
        if not name:
            raise ValueError(
                f"postprocessor {postprocessor_cls.__name__} 缺少 name 属性"
            )
        if name in self._registry:
            raise ValueError(f"重复注册后处理器: {name}")
        self._registry[name] = postprocessor_cls
        return postprocessor_cls

    def get(self, name: str) -> type[BasePostprocessor]:
        """按名称获取后处理器类。

        Raises:
            KeyError: ``name`` 未注册。
        """
        if name not in self._registry:
            raise KeyError(name)
        return self._registry[name]

    def list_names(self) -> list[str]:
        """返回所有已注册后处理器名称（按注册顺序）。"""
        return list(self._registry.keys())

    def create_all(self) -> list[BasePostprocessor]:
        """实例化全部已注册后处理器，按注册顺序返回。"""
        return [cls() for cls in self._registry.values()]


# 全局单例：``@register_postprocessor`` 装饰器据此登记。
postprocessor_registry = PostprocessorRegistry()


def register_postprocessor(postprocessor_cls: type[BasePostprocessor]) -> type[BasePostprocessor]:
    """类装饰器：把后处理器子类登记到 :data:`postprocessor_registry`。

    用法::

        @register_postprocessor
        class PathNormalizer(BasePostprocessor):
            name = "path_normalizer"
            ...

    Args:
        postprocessor_cls: :class:`BasePostprocessor` 子类。

    Returns:
        原样返回入参。

    Raises:
        ValueError: 名称重复或为空。
    """
    return postprocessor_registry.register(postprocessor_cls)
