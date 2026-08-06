"""Servlet Adapter。

对应架构文档 03-api-asset.md。识别 ``HttpServlet`` 子类：

- 类继承自 ``javax.servlet.http.HttpServlet`` / ``jakarta.servlet.http.HttpServlet``
- 覆写的 ``doGet`` / ``doPost`` / ``doPut`` / ``doDelete`` / ``doPatch`` / ``doHead`` / ``doOptions``
  映射为 HTTP 方法
- ``web.xml`` 中声明的 ``<servlet-mapping>`` 路径（与类注解/约定合并）
- ``@WebServlet`` 注解路径
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Tree

from extractors.frameworks.base import Endpoint, FrameworkAdapter
from extractors.java.symbol_table import Symbol


class ServletAdapter(FrameworkAdapter):
    """Servlet 框架 Adapter。"""

    @property
    def framework(self) -> str:
        """``"servlet"``"""
        return "servlet"

    def detect(self, tree: Tree, symbol_table: list[Symbol]) -> bool:
        """检测是否存在继承 ``HttpServlet`` 的类。"""
        raise NotImplementedError

    def extract_endpoints(self, tree: Tree, file_path: str) -> list[Endpoint]:
        """提取 HttpServlet 子类的 doGet/doPost 等方法为端点。"""
        raise NotImplementedError
