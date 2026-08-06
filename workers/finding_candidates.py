"""FINDING_CANDIDATES Worker。对应架构文档 05-finding-model.md「Finding 三层模型」。职责：解析 SARIF 成 FindingCandidate（含指纹）。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.FINDING_CANDIDATES")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """解析 SARIF 并生成 FindingCandidate。

    输入：sarif_id（RUN_CODEQL_VULN_SCAN 产物）。
    流程：解析 SARIF results，每条转为 finding_candidate 记录（rule_id、
    raw_severity、raw_confidence、file_path、start/end_line、symbol、
    source_location、sink_location、dataflow_path_json）。关联到 API 资产
    （api_asset_id，定位属于哪个 API）。计算 fingerprint
    （``sha256(rule_id + 归一化 source/sink/enclosing_method 符号 + 归一化
    数据流签名 + 归一化路径)``，抗代码插入删除，D6/ADR-09）。
    输出：``{"status": "SUCCEEDED", "output": {"candidate_ids": [<int>...],
    "candidate_count": <int>}}``。
    required=✓，on_failure=ABORT。
    """
    raise NotImplementedError
