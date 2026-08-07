"""响应包装中间件：统一前后端响应格式。

前端 vben requestClient 的 defaultResponseInterceptor 期望：
    { code: 0, data: <payload> }   成功
    { code: <非0>, message: ... }  失败

本中间件把所有成功 JSON 响应包成 ``{code: 0, data: <原 body>}``。
失败响应（已由 errors.py 处理成 ApiResponse.fail 形态）统一转成
``{code: <http_status>, message: ...}``。

跳过：/health、/openapi、/docs、SSE/流式响应、非 JSON 响应。
"""

from __future__ import annotations

import json
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# 不包装的路径前缀
_SKIP_PREFIXES = ("/health", "/openapi", "/docs", "/redoc", "/internal")
# 不包装的内容类型
_SKIP_CONTENT_TYPES = ("text/event-stream", "text/html", "text/plain", "application/octet-stream")


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """把成功 JSON 响应包成 {code: 0, data: ...}。"""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)

        # 跳过非 2xx（错误响应由 errors.py 处理，但也统一包装成 code/message）
        # 跳过流式/非 JSON
        content_type = response.headers.get("content-type", "")
        path = request.url.path

        if path.startswith(_SKIP_PREFIXES):
            return response
        if any(ct in content_type for ct in _SKIP_CONTENT_TYPES):
            return response
        if "application/json" not in content_type:
            return response

        # 读取 body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 非 JSON，原样返回
            return Response(content=body, status_code=response.status_code,
                            headers=dict(response.headers), media_type=response.media_type)

        # 已是 {code, data} 形态的不重复包装
        if isinstance(data, dict) and "code" in data and "data" in data:
            return Response(content=body, status_code=response.status_code,
                            headers=dict(response.headers), media_type="application/json")

        # 成功：包成 {code: 0, data: ...}
        if 200 <= response.status_code < 300:
            wrapped = {"code": 0, "data": data}
        else:
            # 失败：统一成 {code: <status>, message: ...}
            # errors.py 的 ApiResponse.fail 形如 {success:false, error:{code,message}}
            message = ""
            if isinstance(data, dict):
                err = data.get("error")
                if isinstance(err, dict):
                    message = err.get("message", "")
                    code_val = err.get("code")
                    wrapped = {"code": code_val or response.status_code, "message": message,
                               "data": data.get("data")}
                else:
                    message = data.get("message") or data.get("detail") or str(data)
                    wrapped = {"code": response.status_code, "message": message}
            else:
                wrapped = {"code": response.status_code, "message": str(data)}

        new_body = json.dumps(wrapped, ensure_ascii=False, default=str).encode("utf-8")
        # 复制 headers 但更新 content-length
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        headers["content-length"] = str(len(new_body))
        return Response(content=new_body, status_code=response.status_code,
                        headers=headers, media_type="application/json")
