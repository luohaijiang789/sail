"""ENRICH_API_DEPTH Worker。对应架构文档 03-api-asset.md「深度层」与 01-data-flow.md。职责：深度补充调用链/资源/数据流（L2 字段，可选，技术可替换）。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.ENRICH_API_DEPTH")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """深度补充 API 资产的 L2 字段。

    输入：api_asset_ids（轻量层初版）。
    流程：补充跨文件完整调用树（api_call_edge depth>1、VIRTUAL_DISPATCH/
    LAMBDA/REFLECTION）、调用链级资源访问（api_resource_access
    source_layer=L2_CALLCHAIN）、数据流信息。技术可替换（可用 CodeQL 深度
    语义查询或其他工具）。失败不影响资产表初版。
    输出：``{"status": "SUCCEEDED", "output": {"enriched_api_asset_ids":
    [<int>...], "call_edge_count": <int>}}``；失败返回 FAILED 但下游继续。
    required=✗，on_failure=CONTINUE：失败只把对应 API 标 enrichment_status=
    FAILED，不阻断扫描。
    """
    raise NotImplementedError
