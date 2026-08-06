"""YAML 解析（application.yml / application-{profile}.yml）。

对应架构文档 03-api-asset.md。读取 Spring Boot 配置，提取数据源、安全、限流、
第三方 endpoint 等配置项，供 API 资产画像与 AI Evidence 使用。
"""

from __future__ import annotations


def parse_yaml(file_path: str) -> dict:
    """解析 YAML 配置文件为嵌套 dict。

    Args:
        file_path: YAML 文件绝对路径。

    Returns:
        解析后的配置字典；空文件返回 ``{}``。
    """
    raise NotImplementedError
