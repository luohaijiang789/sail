"""参数提取：从 handler 方法的 AST 提取 API 参数清单。

对应架构文档 03-api-asset.md。产出 ``parameters_json`` 所需结构
（名/类型/来源/是否必填/校验注解列表），覆盖 path/query/body/header 四类来源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tree_sitter import Tree

ParamSource = Literal["path", "query", "body", "header"]


@dataclass
class ApiParam:
    """单个 API 参数（对应 api_asset.parameters_json 的一项）。

    Attributes:
        name: 参数名。
        type: 参数 Java 类型，如 ``Long`` / ``UserDTO``。
        source: 来源，``path`` / ``query`` / ``body`` / ``header``。
        required: 是否必填（``@PathVariable`` 默认必填；``@RequestParam(required=true)`` 等）。
        validation: 校验注解列表，如 ``["@NotNull", "@Valid", "@Pattern(...)"]``。
    """

    name: str
    type: str
    source: ParamSource
    required: bool = False
    validation: list[str] = field(default_factory=list)


def extract_parameters(handler_tree: Tree, file_path: str) -> list[ApiParam]:
    """提取 handler 方法的参数清单。

    Args:
        handler_tree: handler 方法节点的语法树（或其所属文件树，由调用方约定）。
        file_path: 文件绝对路径，用于解析导入类型。

    Returns:
        :class:`ApiParam` 列表，按参数声明顺序排列。
    """
    raise NotImplementedError
