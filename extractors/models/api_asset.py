"""``ApiAssetData`` 数据类：提取出的 API 资产原始数据。

对应架构文档 03-api-asset.md 的 ``api_asset`` 表 L1 字段。由轻量层
``EXTRACT_API_FACTS`` 阶段聚合端点、参数、安全控制、配置、git 提交人后产出，
供持久化层（``ApiAsset`` ORM）与深度层（``ENRICH_API_DEPTH``）使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from extractors.api.param_extractor import ApiParam
from extractors.api.security_scanner import SecurityControl
from extractors.models.endpoint import ApiEndpoint


@dataclass
class ApiAssetData:
    """单个 API 资产的原始提取数据（对应 api_asset 表 L1 字段）。

    Attributes:
        endpoint: 端点基础信息（方法/路径/类/handler/文件/行/框架）。
        parameters: 参数清单，序列化后写入 ``api_asset.parameters_json``。
        security_controls: 该端点关联的安全控制（不含全局控制）。
        consumes: 请求 ``Content-Type``。
        produces: 响应 ``Content-Type``。
        response_type: 响应体 Java 类型。
        handler_signature: handler 方法签名。
        module: 所属模块名。
        api_group: API 分组。
        commit_author: 最近一次修改该 handler 的 git 提交人。
        commit_time: 最近一次修改的提交时间。
        fingerprint: ``sha256(method+path+controller+handler)``，跨版本关联用。
    """

    endpoint: ApiEndpoint
    parameters: list[ApiParam] = field(default_factory=list)
    security_controls: list[SecurityControl] = field(default_factory=list)
    consumes: str | None = None
    produces: str | None = None
    response_type: str | None = None
    handler_signature: str | None = None
    module: str | None = None
    api_group: str | None = None
    commit_author: str | None = None
    commit_time: str | None = None
    fingerprint: str = ""
