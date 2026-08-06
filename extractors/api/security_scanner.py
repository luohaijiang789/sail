"""安全控制扫描：识别 API 入口与全局的安全控制。

对应架构文档 03-api-asset.md 的 ``api_security_control`` 表与 ADR-14（API 安全画像四维度）。
识别 AUTHN/AUTHZ/PARAM_VALIDATION/INPUT_SANITIZATION/RATE_LIMIT/CSRF/CORS 七类控制，
覆盖：

- Spring: ``@PreAuthorize`` / ``@Secured`` / ``@RolesAllowed`` / ``@Valid`` / ``@Pattern`` /
  ``@Size`` / ``@NotBlank`` / ``SecurityFilterChain``
- JAX-RS: ``@RolesAllowed`` / ``@PermitAll`` / ``@DenyAll``
- 通用: ``Filter`` / ``HandlerInterceptor`` / ``OncePerRequestFilter`` 实现、``web.xml`` 安全约束
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ControlType = Literal[
    "AUTHN", "AUTHZ", "PARAM_VALIDATION", "INPUT_SANITIZATION", "RATE_LIMIT", "CSRF", "CORS"
]
ControlScope = Literal["ENDPOINT", "METHOD", "PARAM", "GLOBAL"]


@dataclass
class SecurityControl:
    """单个安全控制（对应 api_security_control 表的一行）。

    Attributes:
        api_asset_id: 关联的 API 资产 ID；全局控制为 None。
        control_type: 控制类型，见 :data:`ControlType`。
        control_method: 控制方法/注解，如 ``@PreAuthorize`` / ``JwtAuthenticationFilter``。
        control_value: 控制取值，如 ``"hasRole('ADMIN')"`` / ``"\\d+"``。
        scope: 作用域，见 :data:`ControlScope`。
        file_path: 控制所在文件绝对路径。
        line: 控制定义起始行号（1-based）。
        enforced: 是否实际生效（注解在受保护路径上为 True，仅声明未挂载为 False）。
    """

    api_asset_id: int | None
    control_type: ControlType
    control_method: str
    control_value: str | None = None
    scope: ControlScope = "ENDPOINT"
    file_path: str | None = None
    line: int | None = None
    enforced: bool = True


def scan_security_controls(
    source_root: str, endpoints: list
) -> list[SecurityControl]:
    """扫描全仓库安全控制，并关联到给定 endpoints。

    Args:
        source_root: 仓库检出根目录。
        endpoints: :func:`extractors.api.endpoint_detector.detect_endpoints` 产出的端点列表，
            用于把方法级/类级控制绑定到对应 ``api_asset_id``。

    Returns:
        :class:`SecurityControl` 列表，含全局控制（``api_asset_id=None``）。
    """
    raise NotImplementedError
