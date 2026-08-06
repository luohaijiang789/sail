"""扫描器注册表：让扫描器可插拔，不写死 CodeQL。

对应架构文档 08-orchestration.md 与 05-finding-model.md。``RUN_CODEQL_VULN_SCAN``
阶段通过 :data:`scanner_registry` 按 ``scanner_id`` 取出对应的
:class:`~scanners.sdk.ScannerManifest` 与 runner 类，调用其执行入口产出 SARIF。
新增扫描器只需实现 runner 契约并调用 ``register`` 或用 ``@register_scanner`` 装饰，
无需改动编排逻辑。

注册约定：
- ``scanner_id`` 全局唯一，建议格式 ``<engine>-<language>``，如 ``codeql-java``。
- ``runner_cls`` 需实现 ``run_vuln_scan(codeql_db_path, rule_pack, output_sarif_path) -> str``
  与 ``run_api_enrich(codeql_db_path, enrich_queries, output_path) -> str`` 两个静态/类方法，
  签名兼容 :mod:`scanners.codeql_runner`。
- :class:`ScannerManifest.language` 供 :meth:`ScannerRegistry.get_scanners_for_language`
  做语言过滤，编排器据此为多语言仓库选择正确的扫描器集合。
"""

from __future__ import annotations

from scanners.sdk import ScannerManifest


class ScannerRegistry:
    """扫描器注册中心。

    维护 ``scanner_id -> (manifest, runner_cls)`` 映射，并提供按语言检索能力。
    全局单例见 :data:`scanner_registry`。

    Attributes:
        _scanners: ``{scanner_id: (ScannerManifest, runner_cls)}`` 注册表。
        _by_language: ``{language: [scanner_id, ...]}`` 反向索引，按语言加速检索。
    """

    def __init__(self) -> None:
        self._scanners: dict[str, tuple[ScannerManifest, type]] = {}
        self._by_language: dict[str, list[str]] = {}

    def register(self, scanner_id: str, manifest: ScannerManifest, runner_cls: type) -> None:
        """注册一个扫描器。

        若 ``scanner_id`` 已存在则覆盖（支持热更新）。同时维护按语言的反向索引：
        将 ``scanner_id`` 追加到 ``manifest.language`` 对应的列表（去重）。

        Args:
            scanner_id: 扫描器唯一标识，如 ``"codeql-java"``。
            manifest: 扫描器清单，其 ``id`` 应与 ``scanner_id`` 一致。
            runner_cls: 执行器类，需实现 codeql_runner 契约的两个方法。

        Raises:
            ValueError: ``scanner_id`` 为空，或 ``manifest.id`` 与 ``scanner_id`` 不一致。
        """
        if not scanner_id:
            raise ValueError("scanner_id 不能为空")
        if manifest.id != scanner_id:
            raise ValueError(
                f"manifest.id ({manifest.id}) 与 scanner_id ({scanner_id}) 不一致"
            )
        self._scanners[scanner_id] = (manifest, runner_cls)
        lang = manifest.language
        bucket = self._by_language.setdefault(lang, [])
        if scanner_id not in bucket:
            bucket.append(scanner_id)

    def get_scanner(self, scanner_id: str) -> tuple[ScannerManifest, type]:
        """获取已注册扫描器的 manifest 与 runner 类。

        Args:
            scanner_id: 扫描器唯一标识。

        Returns:
            ``(manifest, runner_cls)`` 二元组。

        Raises:
            KeyError: ``scanner_id`` 未注册。
        """
        if scanner_id not in self._scanners:
            raise KeyError(scanner_id)
        return self._scanners[scanner_id]

    def list_scanners(self) -> list[str]:
        """返回所有已注册的 scanner_id 列表（按注册顺序）。

        Returns:
            scanner_id 字符串列表。
        """
        return list(self._scanners.keys())

    def get_scanners_for_language(self, language: str) -> list[str]:
        """返回支持指定语言的 scanner_id 列表。

        Args:
            language: 目标语言，如 ``"java"``。

        Returns:
            匹配语言的 scanner_id 列表；无匹配返回空列表。
        """
        return list(self._by_language.get(language, []))

    def is_registered(self, scanner_id: str) -> bool:
        """检查扫描器是否已注册。"""
        return scanner_id in self._scanners

    def unregister(self, scanner_id: str) -> None:
        """注销扫描器，同步清理按语言索引。

        Args:
            scanner_id: 扫描器唯一标识。

        Raises:
            KeyError: ``scanner_id`` 未注册。
        """
        if scanner_id not in self._scanners:
            raise KeyError(scanner_id)
        manifest, _ = self._scanners.pop(scanner_id)
        bucket = self._by_language.get(manifest.language)
        if bucket and scanner_id in bucket:
            bucket.remove(scanner_id)
            if not bucket:
                del self._by_language[manifest.language]


# 全局单例：编排器与 Worker 均通过此实例访问扫描器。
scanner_registry = ScannerRegistry()


def register_scanner(scanner_id: str):
    """类装饰器：把 runner 类连同其 manifest 自动注册到 :data:`scanner_registry`。

    被装饰的类需通过类属性 ``manifest`` 暴露 :class:`ScannerManifest` 实例，例如::

        @register_scanner("codeql-java")
        class CodeQLJavaRunner:
            manifest = ScannerManifest(id="codeql-java", version="2.17", ...)

            @staticmethod
            def run_vuln_scan(...): ...

    Args:
        scanner_id: 扫描器唯一标识。

    Returns:
        类装饰器，注册后原样返回被装饰的类。

    Raises:
        ValueError: 被装饰类缺少 ``manifest`` 属性，或 manifest.id 与 scanner_id 不一致。
    """

    def _decorator(runner_cls: type) -> type:
        manifest = getattr(runner_cls, "manifest", None)
        if manifest is None:
            raise ValueError(
                f"{runner_cls.__name__} 缺少 manifest 类属性"
            )
        scanner_registry.register(scanner_id, manifest, runner_cls)
        return runner_cls

    return _decorator
