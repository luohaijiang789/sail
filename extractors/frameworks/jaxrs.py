"""JAX-RS Adapter。

对应架构文档 03-api-asset.md。识别 ``javax.ws.rs`` / ``jakarta.ws.rs`` 注解：

- ``@Path`` 类级与方法级路径
- ``@GET`` / ``@POST`` / ``@PUT`` / ``@DELETE`` / ``@PATCH`` / ``@HEAD`` / ``@OPTIONS``
- ``@QueryParam`` / ``@PathParam`` / ``@FormParam`` / ``@HeaderParam`` / ``@CookieParam`` /
  ``@BeanParam`` 参数来源
- ``@RolesAllowed`` / ``@PermitAll`` / ``@DenyAll`` 安全控制
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Tree

from extractors.frameworks.base import Endpoint, FrameworkAdapter
from extractors.java.symbol_table import Symbol


class JaxRsAdapter(FrameworkAdapter):
    """JAX-RS 框架 Adapter。"""

    @property
    def framework(self) -> str:
        """``"jaxrs"``"""
        return "jaxrs"

    def detect(self, tree: Tree, symbol_table: list[Symbol]) -> bool:
        """检测是否出现 ``@Path`` / ``@GET`` 等 JAX-RS 注解。"""
        raise NotImplementedError

    def extract_endpoints(self, tree: Tree, file_path: str) -> list[Endpoint]:
        """提取 JAX-RS Resource 类下的全部 HTTP 端点，拼接类级与方法级路径。"""
        raise NotImplementedError
