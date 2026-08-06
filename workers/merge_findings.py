"""MERGE_FINDINGS Worker。对应架构文档 05-finding-model.md「Finding 三层模型」与 07-risk-fusion.md「后处理流水线」。职责：指纹计算 + 历史匹配 + Finding upsert。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.MERGE_FINDINGS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """指纹归一化、历史匹配并 upsert Finding + 创建 FindingInstance。

    输入：finding_candidates + ai_reviews + api_assets。
    流程（07-risk-fusion 后处理流水线）：Schema 校验 → 路径/符号标准化 →
    指纹计算 → 扫描内去重 → 历史匹配 → Endpoint 绑定 → AI 结论融合。
    归并逻辑（ADR-05）：
      1. 用 candidate.fingerprint 匹配历史 finding；
      2. 命中→复用 finding_id，未命中→新建 Finding（upsert）；
      3. 创建 FindingInstance 关联 candidate + finding。
    历史对比：未存在→NEW；上次 OPEN→RECURRING；上次 FIXED→REAPPEARED；
    上次 FALSE_POSITIVE→保留不再 AI 分析。
    输出：``{"status": "SUCCEEDED", "output": {"finding_ids": [<int>...],
    "instance_ids": [<int>...], "new_count": <int>, "recurring_count": <int>}}``。
    required=✓，on_failure=ABORT。
    """
    raise NotImplementedError
