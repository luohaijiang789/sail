"""SAIL FastAPI 应用入口。"""

from fastapi import FastAPI

from app.api import api_assets, feedback, findings, internal, repositories, scans
from app.api.errors import register_exception_handlers
from app.core.logging import setup_logging

app = FastAPI(title="SAIL", description="Java 仓库的 CodeQL + AI 漏洞扫描平台", version="0.1.0")

# 启动时注册统一异常处理器与结构化日志（路由注册见下方 include_router）。
register_exception_handlers(app)
setup_logging()

app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(api_assets.router, prefix="/api/api-assets", tags=["api-assets"])
app.include_router(findings.router, prefix="/api/findings", tags=["findings"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
