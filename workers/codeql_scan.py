"""RUN_CODEQL_VULN_SCAN Worker。对应架构文档 02-build.md「CodeQL 的定位」与 05-finding-model.md「RulePack」。职责：CodeQL 漏洞规则扫描，输出 SARIF。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.RUN_CODEQL_VULN_SCAN")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """CodeQL 漏洞规则扫描，产出 SARIF。

    输入：codeql_db_id + rule_pack（规则包）。
    流程：基于已建好的 CodeQL 数据库执行漏洞规则查询（source-sink 数据流类 +
    语法/配置类），按 ``rule.requires_dataflow`` 在 NO_BUILD 模式下裁剪失效
    规则。CodeQL 只扫漏洞，不提取 API 信息（ADR-17）。
    结果归档：``scans/{scan_run_id}/results/{rule_pack}.sarif``。
    输出：``{"status": "SUCCEEDED", "output": {"sarif_artifact_id": <int>,
    "result_count": <int>, "rule_pack_version": <str>}}``。
    required=✓，on_failure=ABORT。
    """
    raise NotImplementedError
