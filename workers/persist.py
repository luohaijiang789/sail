"""PERSIST_RESULTS Worker。对应架构文档 07-risk-fusion.md「两段式评分」与 04-check-and-security.md「版本迭代对比」。职责：风险评分 + 落库 + 版本 diff。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.PERSIST_RESULTS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """计算最终风险评分、落库并产出版本 diff。

    输入：merged_findings + security_profiles。
    流程：两段式评分（ADR-06）——第一段基础分 = 规则严重度映射（0-60）+
    上下文加权（外部输入可控/完整数据流/属 HTTP Endpoint，0-40）；第二段
    AI verdict 硬调整：FALSE_POSITIVE 封顶 20、LIKELY_FALSE_POSITIVE 封顶 40、
    其他不变（AI 可向下否决不可向上升级）。无 AI 分析用 base_score、
    ai_verdict=null。回填 finding_instance 的 final_severity / risk_score，
    等级 LOW/MEDIUM/HIGH/CRITICAL。通过 fingerprint 跨版本关联做逐项 diff
    （api_version_diff：NEW/REMOVED/CHANGED/UNCHANGED，按维度组织
    added/removed/modified）与安全分趋势。
    输出：``{"status": "SUCCEEDED", "output": {"instance_ids": [<int>...],
    "persisted_count": <int>, "diff_count": <int>}}``。
    required=✓，on_failure=ABORT。
    """
    raise NotImplementedError
