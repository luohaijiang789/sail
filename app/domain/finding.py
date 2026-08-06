"""Finding 三层模型 + AI Review + 反馈分析。对应架构文档 05/06-finding-model.md。"""

from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain import Base, TimestampMixin


class RulePack(Base, TimestampMixin):
    __tablename__ = "rule_pack"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    codeql_pack_name: Mapped[str] = mapped_column(String(200), nullable=False)
    artifact_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("artifact.id"))
    checksum: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")


class Rule(Base, TimestampMixin):
    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_pack_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rule_pack.id"), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)  # java/sql-injection
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # DATAFLOW/SYNTAX/CONFIG/INHERITANCE
    cwe: Mapped[str | None] = mapped_column(String(20))
    default_severity: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO/LOW/MEDIUM/HIGH/CRITICAL
    requires_dataflow: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    remediation: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class FindingCandidate(Base, TimestampMixin):
    __tablename__ = "finding_candidate"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False, index=True)
    scanner_id: Mapped[str | None] = mapped_column(String(100))
    scanner_version: Mapped[str | None] = mapped_column(String(20))
    rule_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("rule.id"))
    rule_version: Mapped[str | None] = mapped_column(String(20))
    raw_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_confidence: Mapped[float | None] = mapped_column(Float)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    symbol: Mapped[str | None] = mapped_column(String(500))
    source_location: Mapped[dict | None] = mapped_column(JSON)
    sink_location: Mapped[dict | None] = mapped_column(JSON)
    dataflow_path_json: Mapped[list | None] = mapped_column(JSON)
    api_asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("api_asset.id"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_artifact_id: Mapped[int | None] = mapped_column(BigInteger)
    evidence_bundle_id: Mapped[int | None] = mapped_column(BigInteger)
    ai_review_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="NEW")


class Finding(Base, TimestampMixin):
    __tablename__ = "finding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repository.id"), nullable=False, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("rule.id"))
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN/FIXED/REAPPEARED/FALSE_POSITIVE
    first_seen_scan_id: Mapped[int | None] = mapped_column(BigInteger)
    last_seen_scan_id: Mapped[int | None] = mapped_column(BigInteger)
    first_seen_commit: Mapped[str | None] = mapped_column(String(40))
    last_seen_commit: Mapped[str | None] = mapped_column(String(40))
    api_asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("api_asset.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    remediation: Mapped[str | None] = mapped_column(Text)


class FindingInstance(Base, TimestampMixin):
    __tablename__ = "finding_instance"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    finding_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("finding.id"), nullable=False, index=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    source_revision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("source_revision.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("finding_candidate.id"))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    symbol: Mapped[str | None] = mapped_column(String(500))
    api_asset_id: Mapped[int | None] = mapped_column(BigInteger)
    raw_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    final_severity: Mapped[str | None] = mapped_column(String(20))
    ai_verdict: Mapped[str | None] = mapped_column(String(30))
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="NEW")  # NEW/RECURRING/REAPPEARED/RESOLVED


class AiReview(Base, TimestampMixin):
    __tablename__ = "ai_review"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("finding_candidate.id"), nullable=False, index=True)
    api_asset_id: Mapped[int | None] = mapped_column(BigInteger)
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    round: Mapped[int] = mapped_column(Integer, default=1)
    verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    exploitability: Mapped[str | None] = mapped_column(String(20))
    auth_required: Mapped[bool | None] = mapped_column(Boolean)
    auth_enforced: Mapped[bool | None] = mapped_column(Boolean)
    reachable_from_endpoint: Mapped[bool | None] = mapped_column(Boolean)
    response_json: Mapped[dict | None] = mapped_column(JSON)
    need_requests_json: Mapped[list | None] = mapped_column(JSON)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")


class FeedbackAnalysis(Base, TimestampMixin):
    __tablename__ = "feedback_analysis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    api_check_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_check.id"), nullable=False)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    human_verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    human_reason: Mapped[str] = mapped_column(Text, nullable=False)
    ai_verdict_original: Mapped[str | None] = mapped_column(String(30))
    codeql_result_original: Mapped[str | None] = mapped_column(String(20))
    analysis_model: Mapped[str | None] = mapped_column(String(50))
    root_cause: Mapped[str | None] = mapped_column(Text)
    improvement_type: Mapped[str | None] = mapped_column(String(20))  # PROMPT/RULE/PATTERN/NO_CHANGE
    improvement_suggestion_json: Mapped[dict | None] = mapped_column(JSON)
    suggestion_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING/APPROVED/REJECTED/APPLIED
    applied_version: Mapped[str | None] = mapped_column(String(20))
    reviewer: Mapped[str | None] = mapped_column(String(100))
    review_notes: Mapped[str | None] = mapped_column(Text)
