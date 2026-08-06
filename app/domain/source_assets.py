"""Project / Repository / SourceRevision / Artifact / CodeQLDatabase 模型。

对应架构文档 02-build.md。
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(100))
    default_scan_profile_id: Mapped[int | None] = mapped_column(BigInteger)

    repositories: Mapped[list["Repository"]] = relationship(back_populates="project")


class Repository(Base, TimestampMixin):
    __tablename__ = "repository"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    git_url: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    credential_id: Mapped[str | None] = mapped_column(String(100))
    repository_type: Mapped[str] = mapped_column(String(20), default="git")
    last_scanned_commit: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")

    project: Mapped["Project"] = relationship(back_populates="repositories")
    source_revisions: Mapped[list["SourceRevision"]] = relationship(back_populates="repository")


class SourceRevision(Base, TimestampMixin):
    __tablename__ = "source_revision"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repository.id"), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch: Mapped[str | None] = mapped_column(String(100))
    tag: Mapped[str | None] = mapped_column(String(100))
    commit_time: Mapped[datetime | None] = mapped_column(DateTime)
    author: Mapped[str | None] = mapped_column(String(100))
    source_artifact_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("artifact.id"))
    source_fingerprint: Mapped[str | None] = mapped_column(String(64))
    detected_build_plan: Mapped[dict | None] = mapped_column(JSON)

    repository: Mapped["Repository"] = relationship(back_populates="source_revisions")


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifact"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("project.id"))
    scan_run_id: Mapped[int | None] = mapped_column(BigInteger)
    source_revision_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("source_revision.id"))
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(50))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    retention_policy: Mapped[str] = mapped_column(String(20), default="SHORT")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)


class CodeQLDatabase(Base, TimestampMixin):
    __tablename__ = "codeql_database"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_revision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("source_revision.id"), nullable=False)
    build_plan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    codeql_version: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="java-kotlin")
    build_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    quality: Mapped[str] = mapped_column(String(30), nullable=False)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    artifact_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("artifact.id"))
    build_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    database_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    source_file_count: Mapped[int | None] = mapped_column(Integer)
    extraction_warning_count: Mapped[int | None] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="BUILDING")
