"""提取流水线：协调 Tree-sitter 提取层各组件，统一产出 API 资产表初版。

对应架构文档 03-api-asset.md 的轻量层 ``EXTRACT_API_FACTS`` 阶段。编排顺序：
端点检测 → 参数补全 → 安全控制扫描 → DB 访问提取 → 配置解析 → 资产聚合。
产出的 :class:`ApiAssetData` 列表由持久化层写入 ``api_asset`` 表 L1 字段，
``code_facts`` / ``module_info`` / ``stats`` 供 AI Evidence 与性能观测使用。

性能预期（见 03-api-asset.md）：10 万行 Java 30-60 秒，比 CodeQL 建库快一个数量级。
L2 字段（调用链深度等）由 ``ENRICH_API_DEPTH`` 阶段补充，本流水线只产 L1 初版。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from extractors.api.endpoint_detector import detect_endpoints
from extractors.api.param_extractor import ApiParam, extract_parameters
from extractors.api.security_scanner import SecurityControl, scan_security_controls
from extractors.config.mybatis_parser import SqlStatement, parse_mapper_xml
from extractors.config.properties_parser import parse_properties
from extractors.config.yaml_parser import parse_yaml
from extractors.models.api_asset import ApiAssetData
from extractors.models.endpoint import ApiEndpoint


@dataclass
class ExtractionResult:
    """提取流水线统一产物。

    Attributes:
        api_assets: API 资产原始数据列表，对应 ``api_asset`` 表 L1 字段，由
            :meth:`ExtractionPipeline._build_api_assets` 聚合端点/参数/安全控制/DB 访问产出。
        code_facts: 通用代码事实列表（非 API 专属），每项为 dict，对应 ``code_fact`` 表
            的一行（``fact_type`` / ``source_type`` / ``symbol`` / ``properties_json`` 等），
            供 AI Evidence 与漏洞后处理使用。
        module_info: 模块信息映射 ``{module_name: {"file_count":..., "endpoints":...}}``，
            供资产分组与统计。
        stats: 提取统计，如 ``{"java_file_count":..., "endpoint_count":...,
            "param_count":..., "control_count":..., "db_access_count":...,
            "duration_seconds":...}``。
    """

    api_assets: list[ApiAssetData] = field(default_factory=list)
    code_facts: list[dict] = field(default_factory=list)
    module_info: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)


class ExtractionPipeline:
    """Tree-sitter 提取流水线。

    协调端点检测器、参数提取器、安全控制扫描器、MyBatis/配置解析器，对 ``source_root``
    执行完整 L1 提取，产出 :class:`ExtractionResult`。

    Attributes:
        source_root: 仓库检出根目录（编译成功的 source_revision）。
    """

    def __init__(self, source_root: str) -> None:
        """初始化提取流水线。

        Args:
            source_root: 仓库检出根目录绝对路径。
        """
        self.source_root = source_root

    def run(self) -> ExtractionResult:
        """执行完整提取流程。

        顺序：
        1. :meth:`_extract_endpoints` —— 检测全部 HTTP 端点。
        2. :meth:`_extract_parameters` —— 为每个端点补全参数清单。
        3. :meth:`_extract_security_controls` —— 扫描安全控制并关联到端点。
        4. :meth:`_extract_db_access` —— 解析 MyBatis Mapper 提取 DB 访问。
        5. :meth:`_extract_config` —— 解析 YAML/Properties 配置。
        6. :meth:`_build_api_assets` —— 聚合为 :class:`ApiAssetData` 列表。

        Returns:
            填充好的 :class:`ExtractionResult`，含 api_assets / code_facts /
            module_info / stats。
        """
        raise NotImplementedError

    def _extract_endpoints(self) -> list[ApiEndpoint]:
        """用 endpoint_detector 检测全部 HTTP 端点。

        委托 :func:`extractors.api.endpoint_detector.detect_endpoints` 遍历
        ``self.source_root`` 下所有 Java 文件，经各框架 Adapter 产出端点列表。

        Returns:
            去重与路径归一化后的 :class:`ApiEndpoint` 列表。
        """
        return detect_endpoints(self.source_root)

    def _extract_parameters(self, endpoints: list[ApiEndpoint]) -> list[ApiParam]:
        """用 param_extractor 为端点补全参数清单。

        对每个 endpoint 所在 handler 方法调用
        :func:`extractors.api.param_extractor.extract_parameters`，产出参数列表。
        参数与 endpoint 的对应关系由调用方按索引或 handler 定位维护。

        Args:
            endpoints: :meth:`_extract_endpoints` 产出的端点列表。

        Returns:
            所有端点的 :class:`ApiParam` 列表（展平）。
        """
        raise NotImplementedError

    def _extract_security_controls(self, endpoints: list[ApiEndpoint]) -> list[SecurityControl]:
        """用 security_scanner 扫描安全控制并关联到 endpoints。

        委托 :func:`extractors.api.security_scanner.scan_security_controls`，
        覆盖 AUTHN/AUTHZ/PARAM_VALIDATION/INPUT_SANITIZATION/RATE_LIMIT/CSRF/CORS 七类，
        含全局控制（``api_asset_id=None``）。

        Args:
            endpoints: 端点列表，用于把方法级/类级控制绑定到对应 ``api_asset_id``。

        Returns:
            :class:`SecurityControl` 列表，含全局控制。
        """
        return scan_security_controls(self.source_root, endpoints)

    def _extract_db_access(self) -> list[dict]:
        """用 mybatis_parser 解析 Mapper XML 提取 DB 访问。

        遍历 ``self.source_root`` 下所有 ``*Mapper.xml``，对每个文件调用
        :func:`extractors.config.mybatis_parser.parse_mapper_xml`，把
        :class:`SqlStatement` 转为 DB 访问记录 dict（含 ``resource_type`` /
        ``resource_name`` / ``operation`` / ``mapper_namespace`` 等），供
        ``api_resource_access`` 表 L1 声明级使用。

        Returns:
            DB 访问记录 dict 列表，每项对应一条 ``api_resource_access`` L1 行。
        """
        raise NotImplementedError

    def _extract_config(self) -> dict:
        """用 yaml/properties parser 解析配置文件。

        扫描 ``self.source_root`` 下 ``application.yml`` / ``application-{profile}.yml``
        / ``application.properties``，分别调用 :func:`parse_yaml` /
        :func:`parse_properties`，合并为单一嵌套 dict。供 API 资产画像（数据源、安全、
        限流、第三方 endpoint）与 AI Evidence 使用。

        Returns:
            合并后的配置字典；无配置文件返回 ``{}``。
        """
        raise NotImplementedError

    def _build_api_assets(
        self,
        endpoints: list[ApiEndpoint],
        params: list[ApiParam],
        controls: list[SecurityControl],
        db_access: list[dict],
    ) -> list[ApiAssetData]:
        """聚合端点/参数/安全控制/DB 访问为 API 资产数据。

        对每个 endpoint 构造一个 :class:`ApiAssetData`：
        - 绑定其 handler 的参数（按 handler 定位匹配 params）。
        - 绑定其方法级/类级安全控制（``api_asset_id`` 对应的 controls，不含全局）。
        - 关联 DB 访问（按 mapper 调用匹配 db_access，L1 仅声明级）。
        - 计算 ``fingerprint = sha256(method+path+controller+handler)``（见 03-api-asset.md）。
        - 填充 module / api_group / handler_signature 等端点自带字段。

        Args:
            endpoints: 端点列表。
            params: 参数列表（展平，需按 handler 二次定位）。
            controls: 安全控制列表（含全局）。
            db_access: DB 访问记录列表。

        Returns:
            :class:`ApiAssetData` 列表，与 endpoints 一一对应。
        """
        raise NotImplementedError

    @staticmethod
    def _calculate_api_fingerprint(endpoint: ApiEndpoint) -> str:
        """计算 API 资产指纹 ``sha256(method+path+controller+handler)``。

        跨版本关联用（见 03-api-asset.md）。与漏洞指纹（05-finding-model.md）不同。

        Args:
            endpoint: 端点数据。

        Returns:
            64 位十六进制 sha256 字符串。
        """
        raise NotImplementedError
