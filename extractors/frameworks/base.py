"""框架 Adapter 基类。

对应架构文档 03-api-asset.md。每个 Web 框架（Spring/JAX-RS/Servlet/...）实现一个
Adapter，负责：1) 检测当前 AST 是否使用该框架；2) 从中提取 HTTP 端点。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from extractors.java.symbol_table import Symbol

if TYPE_CHECKING:
    from tree_sitter import Tree


@dataclass
class Endpoint:
    """框架适配器产出的原始端点（未补全参数/安全控制）。

    Attributes:
        method: HTTP 方法，如 ``GET`` / ``POST``，未声明时为空串。
        path: 端点路径，如 ``/users/{id}``；类级与方法级路径已拼接。
        controller_class: Controller 类全限定名。
        handler_method: handler 方法名。
        file_path: 文件绝对路径。
        line: handler 定义起始行号（1-based）。
        framework: 框架标识，如 ``spring`` / ``jaxrs`` / ``servlet``。
    """

    method: str
    path: str
    controller_class: str
    handler_method: str
    file_path: str
    line: int
    framework: str = ""


class FrameworkAdapter(ABC):
    """框架 Adapter 抽象基类。

    子类需实现 :meth:`detect` 与 :meth:`extract_endpoints`。
    """

    @property
    def framework(self) -> str:
        """框架标识，如 ``"spring"``，供端点落库使用。"""
        raise NotImplementedError

    @abstractmethod
    def detect(self, tree: Tree, symbol_table: list[Symbol]) -> bool:
        """检测当前文件是否使用本框架。

        Args:
            tree: 已解析的语法树。
            symbol_table: 该文件的符号表。

        Returns:
            True 表示该文件属于本框架，需进一步提取端点。
        """
        raise NotImplementedError

    @abstractmethod
    def extract_endpoints(self, tree: Tree, file_path: str) -> list[Endpoint]:
        """从 AST 提取 HTTP 端点。

        Args:
            tree: 已解析的语法树。
            file_path: 文件绝对路径。

        Returns:
            :class:`Endpoint` 列表。
        """
        raise NotImplementedError
