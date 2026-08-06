"""符号表：从 Tree-sitter AST 提取 Java 符号。

对应架构文档 03-api-asset.md。识别 CLASS/METHOD/FIELD 三类符号，构建全限定名，
供框架 Adapter 定位 Controller/handler、供 AI Evidence 拼装调用链上下文。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tree_sitter import Tree

SymbolKind = Literal["CLASS", "METHOD", "FIELD"]


@dataclass
class Symbol:
    """Java 符号（类/方法/字段）。

    Attributes:
        name: 简单名，如 ``getUser``。
        qualified_name: 全限定名，如 ``com.acme.UserController.getUser``。
        kind: 符号类别，``CLASS`` / ``METHOD`` / ``FIELD``。
        file_path: 符号所在文件绝对路径。
        line: 符号定义起始行号（1-based）。
        signature: 方法签名（含参数类型序列），字段为类型名，类为空串。
    """

    name: str
    qualified_name: str
    kind: SymbolKind
    file_path: str
    line: int
    signature: str = ""


def extract_symbols(tree: Tree, file_path: str) -> list[Symbol]:
    """从已解析的语法树提取符号清单。

    遍历 AST 中的 class/interface/enum/method/field 声明，推导包路径与全限定名。

    Args:
        tree: :func:`extractors.java.parser.parse_file` 返回的语法树。
        file_path: 文件绝对路径，用于填充 :attr:`Symbol.file_path` 与推导包名。

    Returns:
        符号列表，按定义顺序排列。
    """
    raise NotImplementedError
