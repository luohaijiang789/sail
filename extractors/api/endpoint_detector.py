"""API 入口识别：用各框架 Adapter 检测仓库内全部 HTTP 端点。

对应架构文档 03-api-asset.md 的轻量层 ``EXTRACT_API_FACTS`` 阶段。
遍历 Java 文件，对每个文件尝试所有注册的 :class:`FrameworkAdapter`，
合并产出 :class:`ApiEndpoint` 列表，供参数/安全控制补全与资产落库使用。
"""

from __future__ import annotations

from extractors.models.endpoint import ApiEndpoint


def detect_endpoints(source_root: str) -> list[ApiEndpoint]:
    """扫描 source_root，用各框架 Adapter 检测所有 API 入口。

    Args:
        source_root: 仓库检出根目录（编译成功）。

    Returns:
        所有框架适配器产出的 :class:`ApiEndpoint` 列表，已去重与路径归一化。
    """
    raise NotImplementedError
