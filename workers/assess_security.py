"""ASSESS_API_SECURITY Worker。对应架构文档 04-check-and-security.md。职责：生成 check 表 + 四维度安全画像。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.ASSESS_API_SECURITY")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """为每个 API 生成 check 表与安全画像。

    输入：api_assets + findings（merged）。
    流程（ADR-20）：每个 API × 每个检查项 = 一个分级结果
    （PASS/LOW/MEDIUM/HIGH/CRITICAL/NOT_CHECKED）。CodeQL 类检查项由规则扫描
    结果填，API 资产类由资产信息判定（鉴权/授权/校验/CSRF/限流/敏感数据），
    规则未启用的填 NOT_CHECKED。合并成完整 check 表后按四维度汇总成安全画像
    （暴露面 30% / 调用链 35% / 数据 20% / 代码质量 15%），维度分取该维度检查
    项映射分最大值，算 overall_score 与等级
    （SAFE/LOW_RISK/MEDIUM_RISK/HIGH_RISK/CRITICAL），记录 check_coverage 与
    blind_spots。
    输出：``{"status": "SUCCEEDED", "output": {"profile_ids": [<int>...],
    "check_count": <int>}}``。
    required=✗，on_failure=CONTINUE：失败不影响结果落库，仅缺安全画像。
    """
    raise NotImplementedError
