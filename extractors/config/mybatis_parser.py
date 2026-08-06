"""MyBatis Mapper XML 解析。

对应架构文档 03-api-asset.md 的 ``api_resource_access`` 表。从 Mapper XML 提取
``<select>`` / ``<insert>`` / ``<update>`` / ``<delete>`` 语句，解析 SQL 与参数映射，
用于把 API 调用链上的 Mapper 调用关联到具体 SQL 与表操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SqlOperation = Literal["SELECT", "INSERT", "UPDATE", "DELETE"]


@dataclass
class SqlStatement:
    """单条 Mapper SQL 语句。

    Attributes:
        id: 语句 id（即 Mapper 接口方法名），如 ``selectById``。
        operation: SQL 操作类型，见 :data:`SqlOperation`。
        sql: 原始 SQL 文本（已去除 XML 注释与多余空白）。
        parameter_type: ``parameterType`` 全限定类名，未声明为 None。
        result_type: ``resultType`` / ``resultMap`` 全限定类名，未声明为 None。
        tables: SQL 涉及的表名列表（供 ``api_resource_access.resource_name`` 使用）。
        mapper_namespace: ``<mapper namespace>`` 全限定接口名，如 ``com.acme.UserMapper``。
        file_path: Mapper XML 文件绝对路径。
        line: 语句定义起始行号（1-based）。
    """

    id: str
    operation: SqlOperation
    sql: str
    parameter_type: str | None = None
    result_type: str | None = None
    tables: list[str] = field(default_factory=list)
    mapper_namespace: str = ""
    file_path: str = ""
    line: int = 0


def parse_mapper_xml(file_path: str) -> list[SqlStatement]:
    """解析 MyBatis Mapper XML，提取 SQL 语句与参数。

    Args:
        file_path: Mapper XML 文件绝对路径。

    Returns:
        :class:`SqlStatement` 列表，按 XML 中出现顺序排列。
    """
    raise NotImplementedError
