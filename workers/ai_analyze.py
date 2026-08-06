"""AI_ANALYZE Worker。对应 06-ai-analysis.md。

对每个 FindingCandidate 做真实性/可利用性判断。配置了 LLM API key 时调用真实 LLM
（providers 抽象层）；未配置时用规则启发式兜底（基于 source/sink 数据流完整性、
严重度、是否绑 API），产出结构化 AiReview。明确标注 model_name 区分 LLM vs 启发式。
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.schemas import AiReviewOutput
from app.config import settings
from app.core.constants import (
    AI_MAX_NEED_MORE_CONTEXT_ROUNDS,
    VERDICT_FALSE_POSITIVE,
    VERDICT_INSUFFICIENT_CONTEXT,
    VERDICT_LIKELY_TRUE_POSITIVE,
    VERDICT_TRUE_POSITIVE,
    VERDICT_UNCERTAIN,
)
from app.core.logging import get_logger
from app.domain.finding import AiReview, FindingCandidate
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("AiAnalyzeWorker")

PROMPT_VERSION = "1.0"


def ai_analyze(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "AI_ANALYZE", STAGE_RUNNING)

    evidence_dir = Path(settings.workspace_root) / str(scan_run_id) / "evidence"
    candidates = db.execute(
        select(FindingCandidate).where(FindingCandidate.scan_run_id == scan_run_id)
    ).scalars().all()

    llm = _maybe_get_llm()
    analyzed = 0
    for cand in candidates:
        bundle = _load_bundle(evidence_dir, cand.id)
        if bundle is None:
            # 无 evidence：INSUFFICIENT_CONTEXT
            review_out = AiReviewOutput(
                verdict=VERDICT_INSUFFICIENT_CONTEXT, confidence=0.3,
                reasoning={"note": "no evidence bundle assembled"},
            )
        elif llm is not None:
            review_out = _analyze_with_llm(llm, cand, bundle)
        else:
            review_out = _heuristic_verdict(cand, bundle)

        review = AiReview(
            candidate_id=cand.id,
            api_asset_id=cand.api_asset_id,
            model_provider=settings.llm_provider if llm else "rule-heuristic",
            model_name=settings.llm_model_strong if llm else "sail-heuristic-v1",
            prompt_version=PROMPT_VERSION,
            evidence_hash=bundle.get("evidence_hash", "") if bundle else "",
            round=1,
            verdict=review_out.verdict,
            confidence=review_out.confidence,
            exploitability=review_out.exploitability,
            auth_required=review_out.auth_required,
            auth_enforced=review_out.auth_enforced,
            reachable_from_endpoint=review_out.reachable_from_endpoint,
            response_json=review_out.model_dump(mode="json"),
            need_requests_json=[n.model_dump() for n in review_out.need] or None,
            status="SUCCESS",
        )
        db.add(review)
        db.flush()
        cand.ai_review_id = review.id
        analyzed += 1

    db.flush()
    _set_stage(db, scan_run_id, "AI_ANALYZE", STAGE_SUCCEEDED, metrics={
        "analyzed_count": analyzed, "engine": "llm" if llm else "rule-heuristic",
    })
    db.commit()
    logger.info("ai_analyze_done", count=analyzed, engine="llm" if llm else "heuristic")
    return {"status": "SUCCEEDED", "output": {"analyzed_count": analyzed,
            "engine": "llm" if llm else "rule-heuristic"}}


def _maybe_get_llm():
    """配置了 API key 才返回 provider，否则 None（走启发式）。"""
    if not settings.llm_api_key:
        return None
    try:
        from ai.providers.factory import get_strong_llm
        return get_strong_llm()
    except Exception as e:  # noqa: BLE001  provider 构建失败回退启发式
        logger.warning("llm_init_failed_fallback_heuristic", error=str(e)[:200])
        return None


def _load_bundle(evidence_dir: Path, candidate_id: int) -> dict | None:
    p = evidence_dir / f"{candidate_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _analyze_with_llm(llm, cand: FindingCandidate, bundle: dict) -> AiReviewOutput:
    """真实 LLM 调用。把 bundle 喂给 prompt，要求结构化 JSON 输出。"""
    from ai.prompts import build_verification_prompt
    prompt = build_verification_prompt(bundle)
    try:
        resp = llm.chat_with_retry(prompt, temperature=0.0)
        return _parse_llm_response(resp.content)
    except Exception as e:  # noqa: BLE001  LLM 调用失败降级启发式
        logger.warning("llm_call_failed_heuristic", candidate=cand.id, error=str(e)[:200])
        return _heuristic_verdict(cand, bundle)


def _parse_llm_response(content: str) -> AiReviewOutput:
    """解析 LLM JSON 输出为 AiReviewOutput，失败退化为 UNCERTAIN。"""
    try:
        # 容错：提取首个 JSON 对象
        s = content.strip()
        if s.startswith("```"):
            s = s.split("```", 2)[1]
            if s.startswith("json"):
                s = s[4:]
        data = json.loads(s)
        return AiReviewOutput.model_validate(data)
    except Exception:
        return AiReviewOutput(verdict=VERDICT_UNCERTAIN, confidence=0.4,
                              reasoning={"raw": content[:500]})


def _heuristic_verdict(cand: FindingCandidate, bundle: dict) -> AiReviewOutput:
    """规则启发式兜底（无 LLM key 时）。

    判定逻辑（可解释、保守）：
    - 有完整 source→sink 数据流 + 绑定 API 入口 + 高严重度 → LIKELY_TRUE_POSITIVE
    - 有 source→sink 但未绑 API → UNCERTAIN
    - source 或 sink 缺失 → INSUFFICIENT_CONTEXT
    - sink 是 prepareStatement/参数化模式 → FALSE_POSITIVE（已在前置过滤，此处兜底）
    """
    has_source = bool(cand.source_location)
    has_sink = bool(cand.sink_location)
    has_dataflow = bool(cand.dataflow_path_json and len(cand.dataflow_path_json) >= 2)
    bound_api = cand.api_asset_id is not None
    severity = (cand.raw_severity or "").upper()

    if not (has_source and has_sink):
        return AiReviewOutput(
            verdict=VERDICT_INSUFFICIENT_CONTEXT, confidence=0.3,
            reasoning={"source": has_source, "sink": has_sink},
        )

    if has_dataflow and bound_api:
        conf = 0.8 if severity in ("HIGH", "CRITICAL") else 0.65
        return AiReviewOutput(
            verdict=VERDICT_LIKELY_TRUE_POSITIVE, confidence=conf,
            exploitability="HIGH" if severity in ("HIGH", "CRITICAL") else "MEDIUM",
            auth_required=bundle.get("api_asset") is not None,
            auth_enforced=bool(bundle.get("security_controls")),
            reachable_from_endpoint=True,
            reasoning={"heuristic": "complete source→sink flow bound to API endpoint",
                       "severity": severity},
            remediation=_heuristic_remediation(cand),
        )
    if has_dataflow:
        return AiReviewOutput(
            verdict=VERDICT_UNCERTAIN, confidence=0.5,
            reasoning={"heuristic": "dataflow present but not bound to API endpoint"},
        )
    return AiReviewOutput(
        verdict=VERDICT_UNCERTAIN, confidence=0.4,
        reasoning={"heuristic": "sink hit without完整数据流"},
    )


def _heuristic_remediation(cand: FindingCandidate) -> str:
    rule = (cand.symbol or "").lower()
    if "sql" in rule:
        return "使用参数化查询（PreparedStatement + setXxx），禁止拼接 SQL。"
    if "command" in rule:
        return "避免将用户输入传给 Runtime.exec/ProcessBuilder；用白名单校验。"
    if "path" in rule:
        return "对路径输入做规范化与白名单根目录约束，拒绝 .. 路径。"
    if "xpath" in rule:
        return "XPath 查询参数化，禁止拼接。"
    if "ldap" in rule:
        return "LDAP 查询参数转义，禁止拼接。"
    return "审查用户输入到危险 sink 的数据流，增加输入校验与编码。"


def _set_stage(db: Session, scan_run_id: int, stage_type: str, status: str, metrics: dict | None = None) -> None:
    stage = db.execute(
        select(ScanStageRun).where(
            ScanStageRun.scan_run_id == scan_run_id,
            ScanStageRun.stage_type == stage_type,
        )
    ).scalar_one_or_none()
    if stage:
        stage.status = status
        if status == STAGE_RUNNING:
            stage.started_at = datetime.now(timezone.utc)
        elif status == STAGE_SUCCEEDED:
            stage.finished_at = datetime.now(timezone.utc)
            if metrics:
                stage.metrics_json = metrics
        db.flush()


@celery_app.task(name="sail.AI_ANALYZE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return ai_analyze(scan_run_id, stage_run_id, db)
