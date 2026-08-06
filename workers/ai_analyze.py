"""AI_ANALYZE Worker。对应架构文档 06-ai-analysis.md。职责：LLM 引导式提问 + NEED_MORE_CONTEXT 闭环，对 FindingCandidate 做真实性/可利用性判断。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.AI_ANALYZE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """LLM 引导式提问验证 FindingCandidate。

    输入：evidence_bundle_ids（ASSEMBLE_CONTEXT 产物）。
    流程：AI 不发现漏洞，只对 CodeQL 候选做证据补全、真实性判断、可利用性
    判断、修复解释（D4）。强制回答四类引导式审计问题：输入来源 / 路径可达性
    / Sink 约束 / 数据流完整性，防止顺着 CodeQL 认定漏洞。verdict 含
    NEED_MORE_CONTEXT 时附结构化 Need 列表，编排器自动补取后再问（受控多轮，
    最多 3 轮每轮 ≤2000 行，ADR-19，不违反 D5——AI 不主动访问文件系统）。
    AI Review 挂 candidate 不挂 instance（消除循环依赖，ADR-05）。
    按 ``sha256(candidate_fingerprint+commit_sha+evidence_hash+model_version+
    prompt_version)`` 缓存。AI 可向下否决（FALSE_POSITIVE 降级），不可向上
    升级。
    输出结构化 verdict/confidence/exploitability/reasoning/evidence/remediation，
    ``{"status": "SUCCEEDED", "output": {"ai_review_ids": [<int>...],
    "analyzed_count": <int>}}``。
    required=✗，on_failure=CONTINUE：失败时 instance 用 base_score、ai_verdict=null。
    """
    raise NotImplementedError
