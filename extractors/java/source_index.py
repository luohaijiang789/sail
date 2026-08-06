"""源码索引：遍历 Java 仓库建立文件清单与统计。

对应架构文档 03-api-asset.md。轻量层提取的入口：扫描整个仓库的 ``.java`` 文件，
为后续 parser/symbol_table/框架 Adapter 提供统一的文件视图与规模统计。
"""

from __future__ import annotations


class SourceIndex:
    """Java 源码仓库索引。

    Attributes:
        files: 所有 Java 文件的绝对路径列表。
        java_file_count: Java 文件总数。
        file_sizes: ``{file_path: 字节数}`` 映射，供性能调优与按大小排序使用。
    """

    files: list[str]
    java_file_count: int
    file_sizes: dict[str, int]


def build_index(source_root: str) -> SourceIndex:
    """遍历 source_root 下所有 Java 文件建立索引。

    Args:
        source_root: 仓库检出根目录（编译成功的 source_revision）。

    Returns:
        填充好的 :class:`SourceIndex`。
    """
    raise NotImplementedError
