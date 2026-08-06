"""Spring MVC / WebFlux / Security Adapter。

对应架构文档 03-api-asset.md。识别 Spring 系列注解：

- ``@RestController`` / ``@Controller`` 标记 Controller 类
- ``@RequestMapping`` 类级与方法级路径
- ``@GetMapping`` / ``@PostMapping`` / ``@PutMapping`` / ``@DeleteMapping`` / ``@PatchMapping``
- ``@RequestBody`` / ``@PathVariable`` / ``@RequestParam`` / ``@RequestHeader`` 参数来源
- ``@PreAuthorize`` / ``@Secured`` / ``@Valid`` / ``@Pattern`` 安全控制
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Tree

from extractors.frameworks.base import Endpoint, FrameworkAdapter
from extractors.java.symbol_table import Symbol


class SpringAdapter(FrameworkAdapter):
    """Spring MVC / WebFlux 框架 Adapter。"""

    @property
    def framework(self) -> str:
        """``"spring"``"""
        return "spring"

    def detect(self, tree: Tree, symbol_table: list[Symbol]) -> bool:
        """检测是否出现 ``@RestController`` / ``@Controller`` / ``@RequestMapping`` 等注解。"""
        raise NotImplementedError

    def extract_endpoints(self, tree: Tree, file_path: str) -> list[Endpoint]:
        """提取 Spring Controller 下的全部 HTTP 端点，拼接类级与方法级路径。"""
        raise NotImplementedError
