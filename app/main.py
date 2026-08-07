"""SAIL FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_assets, feedback, findings, internal, mock_auth, repositories, scans
from app.api.errors import register_exception_handlers
from app.api.response_wrapper import ResponseWrapperMiddleware
from app.core.logging import setup_logging

app = FastAPI(title="SAIL", description="Java 仓库的 CodeQL + AI 漏洞扫描平台", version="0.1.0")

# CORS：开发环境允许所有来源（前端 vite 代理可能 307 重定向到后端直连地址）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 响应包装中间件：把成功响应包成 {code:0, data:...}，对齐前端 requestClient 约定。
# 必须在路由前注册。
app.add_middleware(ResponseWrapperMiddleware)

# 启动时注册统一异常处理器与结构化日志（路由注册见下方 include_router）。
register_exception_handlers(app)
setup_logging()

app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(api_assets.router, prefix="/api/api-assets", tags=["api-assets"])
app.include_router(findings.router, prefix="/api/findings", tags=["findings"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])
# 开发用 mock 认证（vben-admin 前端登录所需），见 app/api/mock_auth.py
app.include_router(mock_auth.router, tags=["mock-auth"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
