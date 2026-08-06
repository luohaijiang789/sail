"""Anthropic Claude LLM provider。

继承 :class:`BaseLlmProvider`，调用 Anthropic Messages API（``/v1/messages``）：
- 用 httpx 同步客户端发请求，带 ``x-api-key`` + ``anthropic-version`` 头。
- 从响应 ``usage`` 解析 ``input_tokens`` / ``output_tokens``。
- 按 model 名查 :mod:`ai.providers.pricing` 估算成本。
- 429 → ``LlmRateLimitError``（带 Retry-After）；超时 → ``LlmTimeoutError``。

注意：当前为接口骨架，实际 HTTP 调用部分 ``raise NotImplementedError``，
待接入真实流量时补全（见 :meth:`AnthropicProvider.chat` 内标注）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ai.providers.base import BaseLlmProvider, LlmResponse
from ai.providers.pricing import calculate_cost
from app.core.exceptions import LlmRateLimitError, LlmTimeoutError

logger = logging.getLogger(__name__)

# Anthropic Messages API 默认端点与版本。
_DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
_MESSAGES_PATH = "/messages"
_ANTHROPIC_VERSION = "2023-06-01"
# 默认请求超时（秒）。
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, read=120.0, write=10.0, pool=10.0)


class AnthropicProvider(BaseLlmProvider):
    """Anthropic Claude Messages API provider。

    Args:
        api_key: ``sk-ant-...`` 形式的 API Key。
        base_url: API 基地址；为空用官方 ``api.anthropic.com``。
        model: 默认模型名（如 ``claude-3-5-sonnet``）。
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        super().__init__(api_key, base_url, model)
        self._endpoint = self._resolve_endpoint(base_url)
        self._client = httpx.Client(timeout=_DEFAULT_TIMEOUT)

    @staticmethod
    def _resolve_endpoint(base_url: str) -> str:
        """解析 Messages API 完整端点 URL。

        base_url 为空 → 官方端点；否则末尾补 ``/messages``（已含则不补）。

        Args:
            base_url: 配置的 base_url。

        Returns:
            完整的 Messages URL。
        """
        root = base_url.rstrip("/") if base_url else _DEFAULT_ANTHROPIC_BASE_URL
        if root.endswith(_MESSAGES_PATH):
            return root
        return root + _MESSAGES_PATH

    def chat(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 16384,
        response_format: dict[str, Any] | None = None,
    ) -> LlmResponse:
        """调用 Anthropic Messages API。

        Anthropic 无原生 ``response_format``，强制 JSON 时通过 system prompt 指示，
        此处接收参数但不透传（``response_format`` 保留以兼容接口）。

        Args:
            prompt: 完整 prompt 字符串（以单条 user message 发送）。
            model: 模型名；None 时用 ``self.model``。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数（Anthropic 必填）。
            response_format: 兼容参数，Anthropic 当前不透传。

        Returns:
            :class:`LlmResponse`，含 content/usage/cost/model/raw_response。

        Raises:
            LlmRateLimitError: 429 限流。
            LlmTimeoutError: 请求超时。
        """
        used_model = model or self.model
        payload: dict[str, Any] = {
            "model": used_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # response_format 在 Anthropic 侧不透传，仅记录以备日志/调试。
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

        try:
            # TODO(ai): 接入真实流量时替换为实际 POST 调用，例如：
            #   resp = self._client.post(self._endpoint, json=payload, headers=headers)
            #   return self._parse_response(resp, used_model)
            raise NotImplementedError(
                "AnthropicProvider.chat HTTP call not implemented; "
                "wire up httpx POST + parse per TODO."
            )
        except httpx.TimeoutException as exc:
            logger.warning("Anthropic request timed out: model=%s err=%s", used_model, exc)
            self._handle_timeout()
            raise  # 不会到达：_handle_timeout 始终抛出

    def _parse_response(self, response: httpx.Response, model: str) -> LlmResponse:
        """把 Anthropic 响应解析成 :class:`LlmResponse`。

        - 非 2xx：429 → 限流异常，其余 ``raise_for_status``。
        - 2xx：拼接 ``content[*].text``（content 为 block 数组），读 ``usage`` 的
          ``input_tokens`` / ``output_tokens``，按 :func:`calculate_cost` 估算成本。

        Args:
            response: httpx 响应对象。
            model: 实际使用的模型名。

        Returns:
            :class:`LlmResponse`。
        """
        if response.status_code == 429:
            self._handle_rate_limit(response)  # 始终抛 LlmRateLimitError
            raise  # 不可达

        response.raise_for_status()
        data: dict[str, Any] = response.json()
        usage = data.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        # Anthropic content 是 block 数组：[{"type": "text", "text": "..."}, ...]
        blocks = data.get("content") or []
        parts: list[str] = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
        content = "".join(parts)
        used_model = data.get("model") or model
        cost = calculate_cost(used_model, input_tokens, output_tokens)
        return LlmResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            model=used_model,
            raw_response=data,
        )

    def close(self) -> None:
        """关闭底层 httpx 客户端，释放连接。"""
        self._client.close()
