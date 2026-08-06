"""结构化日志配置。每条日志含 scan_run_id/stage_run_id 等上下文。"""

import logging
import sys
from typing import Any

import structlog


def setup_logging(level: str = "INFO") -> None:
    """初始化结构化日志。应在应用启动时调用。"""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """获取绑定日志器。"""
    return structlog.get_logger(name)


def bind_scan_context(scan_run_id: int, stage_run_id: int | None = None,
                      repository_id: int | None = None, commit_sha: str | None = None) -> None:
    """绑定扫描上下文到日志。后续所有日志自动携带这些字段。"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        scan_run_id=scan_run_id,
        stage_run_id=stage_run_id,
        repository_id=repository_id,
        commit_sha=commit_sha,
    )


def unbind_context() -> None:
    """清除日志上下文。"""
    structlog.contextvars.clear_contextvars()
