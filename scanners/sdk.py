"""Scanner Manifest + SDK：加载与校验扫描器清单。

对应架构文档 05-finding-model.md。Scanner Manifest 声明扫描器的 id/version/engine/
language/inputs/outputs/rules/resources，供编排器在 ``RUN_CODEQL_VULN_SCAN`` 阶段
选择正确的 rule pack 与资源。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScannerManifest:
    """扫描器清单。

    Attributes:
        id: 扫描器唯一标识，如 ``"codeql-java"``。
        version: 扫描器版本号。
        engine: 引擎类型，如 ``"codeql"``。
        language: 目标语言，如 ``"java"``。
        inputs: 输入依赖描述列表（如 ``["codeql_database"]``）。
        outputs: 产物描述列表（如 ``["sarif"]``）。
        rules: 规则 pack 引用列表（对应 ``rule_pack.codeql_pack_name``）。
        resources: 运行所需资源描述（如 CPU/内存/超时），供调度器使用。
    """

    id: str
    version: str
    engine: str
    language: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    resources: dict = field(default_factory=dict)


def load_manifest(path: str) -> ScannerManifest:
    """从 YAML/JSON 文件加载并校验 Scanner Manifest。

    Args:
        path: manifest 文件绝对路径。

    Returns:
        填充好的 :class:`ScannerManifest`。

    Raises:
        ValueError: manifest 字段缺失或类型不合法。
    """
    raise NotImplementedError
