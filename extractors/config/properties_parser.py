"""Properties 解析（application.properties 等）。

对应架构文档 03-api-asset.md。读取 Java properties 格式配置，与 YAML 配置合并后
供 API 资产画像与 AI Evidence 使用。
"""

from __future__ import annotations


def parse_properties(file_path: str) -> dict:
    """解析 properties 文件为嵌套 dict。

    点号分隔的 key（如 ``spring.datasource.url``）展开为嵌套结构。

    Args:
        file_path: properties 文件绝对路径。

    Returns:
        解析后的配置字典；空文件返回 ``{}``。
    """
    raise NotImplementedError
