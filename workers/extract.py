"""EXTRACT_API_FACTS Worker。对应架构文档 03-api-asset.md「轻量层」。职责：Tree-sitter 轻量提取 API 资产表初版（L1 字段）。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.EXTRACT_API_FACTS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """Tree-sitter 轻量提取 API 资产表初版。

    输入：source_artifact_id（须编译成功，代码不完整时提取不可信）。
    流程：Tree-sitter Java 生成 AST，经框架 Adapter（Spring/JAX-RS/Servlet/
    WebSocket）识别 API 入口，配置解析器解析 YAML/Properties/XML（含 MyBatis
    Mapper），git 提取提交人/时间。写入 api_asset 的 L1 字段：
    入口/参数/注解/Controller/handler/MyBatis SQL/配置/提交人，以及单文件
    直接调用（call_edge depth=1）、声明级资源访问、L1 安全控制。
    enrichment_status=INITIAL，call_chain_depth=null（L2 由 ENRICH 补）。
    性能预期：10 万行 Java 30-60 秒，比 CodeQL 建库快一个数量级。
    输出：``{"status": "SUCCEEDED", "output": {"api_asset_ids": [<int>...],
    "api_asset_count": <int>}}``。
    on_failure=ABORT；BUILD 降级 NO_BUILD 时本阶段 SKIPPED。
    """
    raise NotImplementedError
