"""ASSESS_API_SECURITY Worker。对应 04-check-and-security.md。

为每个 API 生成 check 表（API × 检查项 = 分级结果）+ 四维度安全画像。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import (
    SCORE_LEVEL_CRITICAL,
    SCORE_LEVEL_HIGH_RISK,
    SCORE_LEVEL_LOW_RISK,
    SCORE_LEVEL_MEDIUM_RISK,
    SCORE_LEVEL_SAFE,
)
from app.core.logging import get_logger
from app.domain.api_asset import ApiAsset, ApiSecurityControl
from app.domain.check_and_security import (
    DIMENSION_CHECK_ITEMS,
    DIMENSION_WEIGHTS,
    RESULT_SCORE_MAP,
    ApiCheck,
    ApiSecurityProfile,
    CHECK_CRITICAL,
    CHECK_HIGH,
    CHECK_NOT_CHECKED,
    CHECK_PASS,
    PREDEFINED_CHECK_ITEMS,
)
from app.domain.finding import FindingCandidate
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from app.domain.source_assets import SourceRevision
from workers.celery_app import celery_app

logger = get_logger("AssessSecurityWorker")

# 规则 key → check item key 映射（CodeQL/污点分析发现的规则落到对应检查项）
RULE_TO_CHECK = {
    "sql-injection": "SQL_INJECTION",
    "command-injection": "COMMAND_INJECTION",
    "xpath-injection": "XPATH_INJECTION",
    "ldap-injection": "LDAP_INJECTION",
    "xss": "XSS",
    "path-traversal": "PATH_TRAVERSAL",
}

SEVERITY_TO_CHECK = {
    "CRITICAL": CHECK_CRITICAL,
    "HIGH": CHECK_HIGH,
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
}


def assess_api_security(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        return {"status": "FAILED", "error_code": "SOURCE_NOT_FOUND"}

    _set_stage(db, scan_run_id, "ASSESS_API_SECURITY", STAGE_RUNNING)

    api_assets = db.execute(
        select(ApiAsset).where(ApiAsset.scan_run_id == scan_run_id)
    ).scalars().all()
    candidates = db.execute(
        select(FindingCandidate).where(FindingCandidate.scan_run_id == scan_run_id)
    ).scalars().all()
    controls = db.execute(
        select(ApiSecurityControl).where(ApiSecurityControl.scan_run_id == scan_run_id)
    ).scalars().all()

    # 按 api_asset_id 索引候选与控制
    cands_by_api: dict[int, list[FindingCandidate]] = {}
    for c in candidates:
        if c.api_asset_id:
            cands_by_api.setdefault(c.api_asset_id, []).append(c)
    controls_by_api: dict[int, list[ApiSecurityControl]] = {}
    for c in controls:
        controls_by_api.setdefault(c.api_asset_id, []).append(c)
    # 预载 rule_id → rule_key，用于候选→检查项匹配
    rule_ids = {c.rule_id for c in candidates if c.rule_id}
    rule_key_by_id: dict[int, str] = {}
    if rule_ids:
        from app.domain.finding import Rule
        for r in db.execute(select(Rule).where(Rule.id.in_(rule_ids))).scalars().all():
            rule_key_by_id[r.id] = r.rule_key

    check_count = 0
    profile_ids: list[int] = []

    for api in api_assets:
        api_cands = cands_by_api.get(api.id, [])
        api_controls = controls_by_api.get(api.id, [])
        # 该 API 各候选的 rule_key 集合
        api_rule_keys = {rule_key_by_id.get(c.rule_id) for c in api_cands if c.rule_id}
        api_cand_by_rule: dict[str, FindingCandidate] = {}
        for c in api_cands:
            rk = rule_key_by_id.get(c.rule_id)
            if rk:
                api_cand_by_rule.setdefault(rk, c)
        checks: list[ApiCheck] = []

        for item in PREDEFINED_CHECK_ITEMS:
            result, evidence, cand_id = _evaluate_check(
                item, api, api_cands, api_controls, api_rule_keys, api_cand_by_rule)
            chk = ApiCheck(
                api_asset_id=api.id,
                scan_run_id=scan_run_id,
                source_revision_id=source_rev.id,
                check_item_key=item["key"],
                check_item_name=item["name"],
                check_category=item["category"],
                check_source=item["source"],
                result=result,
                finding_candidate_id=cand_id,
                evidence_summary=evidence,
            )
            db.add(chk)
            checks.append(chk)
            check_count += 1

        db.flush()
        profile = _build_profile(api, checks, scan_run_id, source_rev.id)
        db.add(profile)
        db.flush()
        profile_ids.append(profile.id)

    _set_stage(db, scan_run_id, "ASSESS_API_SECURITY", STAGE_SUCCEEDED, metrics={
        "check_count": check_count, "profile_count": len(profile_ids),
    })
    db.commit()
    logger.info("assess_done", checks=check_count, profiles=len(profile_ids))
    return {"status": "SUCCEEDED", "output": {"check_count": check_count,
            "profile_count": len(profile_ids)}}


def _evaluate_check(item, api, cands, controls, api_rule_keys, api_cand_by_rule) -> tuple[str, str, int | None]:
    """评估单个检查项，返回 (result, evidence, candidate_id)。"""
    key = item["key"]
    # CodeQL/污点类：看是否有对应规则候选（按 rule_key 匹配）
    if item["source"] == "CODEQL":
        for rule_key, check_key in RULE_TO_CHECK.items():
            if check_key == key and rule_key in api_rule_keys:
                c = api_cand_by_rule.get(rule_key)
                sev = SEVERITY_TO_CHECK.get(c.raw_severity, CHECK_HIGH) if c else CHECK_HIGH
                ev = f"source→sink: {c.source_location}→{c.sink_location}" if c else "finding present"
                return sev, ev, c.id if c else None
        # 规则未启用或无发现：PASS（未发现不代表安全，但阶段一记 PASS）
        return CHECK_PASS, "no finding", None

    # API 资产类：看是否有对应安全控制
    ctrl_types = {c.control_type for c in controls}
    if key == "NO_AUTHN":
        has_authn = "AUTHN" in ctrl_types or any(
            c.control_method in ("@PreAuthorize", "@Secured", "@RolesAllowed") for c in controls
        )
        return (CHECK_PASS if has_authn else CHECK_HIGH,
                "authn control present" if has_authn else "no authentication detected", None)
    if key == "NO_AUTHZ":
        has_authz = "AUTHZ" in ctrl_types
        return (CHECK_PASS if has_authz else CHECK_NOT_CHECKED,
                "authz control present" if has_authz else "authz not detected", None)
    if key == "NO_PARAM_VALIDATION":
        has_val = "PARAM_VALIDATION" in ctrl_types
        params = api.parameters_json or []
        needs_val = any(p.get("source") in ("body", "query", "path") for p in params)
        if not needs_val:
            return CHECK_PASS, "no user-input params", None
        return (CHECK_PASS if has_val else CHECK_HIGH,
                "validation present" if has_val else "params lack validation", None)
    if key == "NO_CSRF":
        # 阶段一：POST/PUT/DELETE/PATCH 无 CSRF token 即 HIGH
        if api.http_method in ("POST", "PUT", "DELETE", "PATCH"):
            has_csrf = "CSRF" in ctrl_types
            return (CHECK_PASS if has_csrf else CHECK_NOT_CHECKED,
                    "csrf present" if has_csrf else "state-changing method, csrf not detected", None)
        return CHECK_PASS, "non-state-changing method", None
    if key == "NO_RATE_LIMIT":
        return CHECK_NOT_CHECKED, "rate limit not assessed in phase 1", None
    if key == "SENSITIVE_DATA_RETURN":
        return CHECK_NOT_CHECKED, "requires runtime/data model analysis", None
    if key == "SENSITIVE_DATA_ACCESS":
        return CHECK_NOT_CHECKED, "requires data model analysis", None
    # 代码质量类：阶段一未扫
    return CHECK_NOT_CHECKED, "code quality not scanned in phase 1", None


def _build_profile(api, checks, scan_run_id, source_rev_id) -> ApiSecurityProfile:
    """按四维度汇总成安全画像。维度分取该维度检查项映射分最大值。"""
    check_by_key = {c.check_item_key: c for c in checks}
    dim_scores: dict[str, int] = {}
    for dim, items in DIMENSION_CHECK_ITEMS.items():
        scores = [RESULT_SCORE_MAP.get(check_by_key[i].result, 0) for i in items if i in check_by_key]
        dim_scores[dim] = max(scores) if scores else 0

    overall = int(
        dim_scores["exposure"] * DIMENSION_WEIGHTS["exposure"]
        + dim_scores["callchain"] * DIMENSION_WEIGHTS["callchain"]
        + dim_scores["data_sensitivity"] * DIMENSION_WEIGHTS["data_sensitivity"]
        + dim_scores["codequality"] * DIMENSION_WEIGHTS["codequality"]
    )
    level = _score_to_level(overall)
    checked = sum(1 for c in checks if c.result != CHECK_NOT_CHECKED)
    coverage = int(checked / len(checks) * 100) if checks else 0
    blind = [c.check_item_key for c in checks if c.result == CHECK_NOT_CHECKED]

    return ApiSecurityProfile(
        api_asset_id=api.id,
        scan_run_id=scan_run_id,
        source_revision_id=source_rev_id,
        overall_score=overall,
        overall_level=level,
        exposure_score=dim_scores["exposure"],
        callchain_score=dim_scores["callchain"],
        data_sensitivity_score=dim_scores["data_sensitivity"],
        codequality_score=dim_scores["codequality"],
        check_coverage=coverage,
        blind_spots=blind,
        risk_factors_json={"dim_scores": dim_scores},
    )


def _score_to_level(score: int) -> str:
    if score >= 85:
        return SCORE_LEVEL_CRITICAL
    if score >= 70:
        return SCORE_LEVEL_HIGH_RISK
    if score >= 50:
        return SCORE_LEVEL_MEDIUM_RISK
    if score >= 25:
        return SCORE_LEVEL_LOW_RISK
    return SCORE_LEVEL_SAFE


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


@celery_app.task(name="sail.ASSESS_API_SECURITY")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return assess_api_security(scan_run_id, stage_run_id, db)
