"""开发用 Mock 认证路由（前缀 / 在 main.py 注册，与业务 /api 同级）。

vben-admin 前端登录需要 auth/user 接口；SAIL 后端本身无鉴权（架构文档明确：阶段一不做复杂权限）。
此处提供最小 mock：登录返回 accessToken，user/info 返回固定用户，菜单走前端静态路由
（accessMode=frontend 时前端不调 /menu/all）。仅用于本地开发跑通前端，不用于生产。
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["mock-auth"])


class LoginParams(BaseModel):
    username: str | None = None
    password: str | None = None


@router.post("/auth/login")
def login(_params: LoginParams) -> dict:
    """Mock 登录：任意账密返回 token。"""
    return {"accessToken": "sail-mock-token"}


@router.post("/auth/refresh")
def refresh() -> dict:
    return {"data": "sail-mock-token", "status": 0}


@router.post("/auth/logout")
def logout() -> dict:
    return {"status": 0}


@router.get("/auth/codes")
def codes() -> list[str]:
    return ["AC_100100", "AC_100110", "AC_100120", "AC_100010"]


@router.get("/user/info")
def user_info() -> dict:
    return {
        "userId": "1",
        "username": "sail",
        "realName": "SAIL Admin",
        "avatar": "",
        "roles": [{"roleName": "admin", "value": "super"}],
        "homePath": "/dashboard/analytics",
    }


@router.get("/user/menu")
def user_menu() -> list:
    """后端动态菜单。前端 accessMode=frontend 时不调用；保留兜底。"""
    return []


@router.get("/menu/all")
def menu_all() -> list:
    """前端 accessMode=backend/mixed 时调用。返回空让前端用静态路由。"""
    return []
