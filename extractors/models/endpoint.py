"""``ApiEndpoint`` 数据类：轻量层提取产出的 HTTP 端点原始数据。

对应架构文档 03-api-asset.md。由 :func:`extractors.api.endpoint_detector.detect_endpoints`
产出，是参数补全、安全控制扫描、资产落库（``api_asset`` 表 L1 字段）的共同载体。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApiEndpoint:
    """单个 HTTP 端点（轻量层产出，对应 api_asset 表 L1 字段）。

    Attributes:
        method: HTTP 方法，如 ``GET`` / ``POST``。
        path: 端点路径，类级与方法级路径已拼接，如 ``/users/{id}``。
        controller_class: Controller 类全限定名。
        handler_method: handler 方法名。
        file_path: 文件绝对路径。
        line: handler 定义起始行号（1-based）。
        framework: 框架标识，``spring`` / ``jaxrs`` / ``servlet`` 等。
        handler_signature: handler 方法签名（含参数类型序列），供指纹与 AI 上下文使用。
        consumes: ``Content-Type``，未声明为 None。
        produces: ``Accept`` / 响应 ``Content-Type``，未声明为 None。
        response_type: 响应体 Java 类型，未声明为 None。
        module: 所属模块名，未识别为 None。
        api_group: API 分组（如 ``@RequestMapping`` 类级路径首段），未识别为 None。
    """

    method: str
    path: str
    controller_class: str
    handler_method: str
    file_path: str
    line: int
    framework: str = ""
    handler_signature: str | None = None
    consumes: str | None = None
    produces: str | None = None
    response_type: str | None = None
    module: str | None = None
    api_group: str | None = None
