"""Tree-sitter Java 解析器封装。

对应架构文档 03-api-asset.md。提供对单个 Java 文件的语法树解析与节点查询能力，
作为轻量层（L1）API 资产提取的基础。比 CodeQL 建库快一个数量级。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node, Tree


def parse_file(file_path: str) -> Tree:
    """解析单个 Java 文件，返回 Tree-sitter 语法树。

    Args:
        file_path: Java 文件绝对路径。

    Returns:
        Tree-sitter ``Tree`` 对象，根节点为 ``program``。

    Raises:
        FileNotFoundError: 文件不存在。
        UnicodeDecodeError: 文件非 UTF-8 编码。
    """
    raise NotImplementedError


def parse_source(source: str, language: str = "java") -> Tree:
    """解析 Java 源码字符串，返回语法树。

    Args:
        source: Java 源码文本。
        language: 语言名，默认 ``"java"``。

    Returns:
        Tree-sitter ``Tree`` 对象。
    """
    raise NotImplementedError


def query_nodes(tree: Tree, query_pattern: str) -> list[Node]:
    """用 Tree-sitter query 匹配语法树节点。

    Args:
        tree: 已解析的语法树。
        query_pattern: Tree-sitter query S-表达式，例如
            ``(method_declaration (modifiers (annotation) @annotation)) @method``。

    Returns:
        匹配到的 ``Node`` 列表（按出现顺序）。
    """
    raise NotImplementedError
