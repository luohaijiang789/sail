"""OpenAI 兼容 LLM provider（支持 OpenAI 官方 / Azure OpenAI / 兼容 API）。

继承 :class:`BaseLlmProvider`，调用 Chat Completions API（``/v1/chat/completions``）：
- 用 httpx 同步客户端发请求。
- 支持 ``response_format={"type": "json_object"}`` 强制 JSON 输出。
- 从响应 ``usage`` 解析 input/output token 数。
- 按 model 名查 :mod:`ai.providers.pricing` 估算成本。
- 429 → ``LlmRateLimitError``（带 Retry-After）；超时 → ``LlmTimeoutError``。

注意：当前为接口骨架，实际 HTTP 调用部分 ``raise NotImplementedError``，
待接入真实流量时补全（见 :meth:`OpenAIProvider.chat` 内标注）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ai.providers.base import BaseLlmProvider, LlmResponse
from ai.providers.pricing import calculate_cost
from app.core.exceptions import LlmRateLimitError, LlmTimeoutError

logger = logging.getLogger(__name__)

# Chat Completions 默认路径（base_url 为空时拼接官方端点）。
_DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
_CHAT_COMPLETIONS_PATH = "/chat/completions"
# 默认请求超时（秒）：连接 10s，读取 120s（长输出审计场景）。
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, read=120.0, write=10.0, pool=10.0)


class OpenAIProvider(BaseLlmProvider):
    """OpenAI 兼容 Chat Completions provider。

    Args:
        api_key: ``sk-...`` 形式的 API Key（Azure 用 deployment key）。
        base_url: API 基地址。OpenAI 官方可留空（用 ``api.openai.com``）；
            Azure/OpenAI 兼容服务填完整端点（如 ``https://xxx.openai.azure.com/openai/deployments/<dep>``）。
        model: 默认模型名（如 ``gpt-4o``）。
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        super().__init__(api_key, base_url, model)
        self._endpoint = self._resolve_endpoint(base_url)
        self._client = httpx.Client(timeout=_DEFAULT_TIMEOUT)

    @staticmethod
    def _resolve_endpoint(base_url: str) -> str:
        """解析 Chat Completions 完整端点 URL。

        base_url 为空 → 官方端点；否则在末尾补 ``/chat/completions``（已含则不补）。

        Args:
            base_url: 配置的 base_url。

        Returns:
            完整的 Chat Completions URL。
        """
        root = base_url.rstrip("/") if base_url else _DEFAULT_OPENAI_BASE_URL
        if root.endswith(_CHAT_COMPLETIONS_PATH):
            return root
        return root + _CHAT_COMPLETIONS_PATH

    def chat(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 16384,
        response_format: dict[str, Any] | None = None,
    ) -> LlmResponse:
        """调用 OpenAI Chat Completions API。

        Args:
            prompt: 完整 prompt 字符串（以单条 user message 发送）。
            model: 模型名；None 时用 ``self.model``。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数。
            response_format: 强制输出格式，如 ``{"type": "json_object"}``。

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
        if response_format is not None:
            payload["response_format"] = response_format
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            # TODO(ai): 接入真实流量时替换为实际 POST 调用，例如：
            #   resp = self._client.post(self._endpoint, json=payload, headers=headers)
            #   return self._parse_response(resp, used_model)
            raise NotImplementedError(
                "OpenAIProvider.chat HTTP call not implemented; "
                "wire up httpx POST + parse per TODO."
            )
        except httpx.TimeoutException as exc:
            logger.warning("OpenAI request timed out: model=%s err=%s", used_model, exc)
            self._handle_timeout()
            raise  # 不会到达：_handle_timeout 始终抛出

    def _parse_response(self, response: httpx.Response, model: str) -> LlmResponse:
        """把 OpenAI 响应解析成 :class:`LlmResponse`。

        - 非 2xx：429 → 限流异常，其余抛 ``LlmRateLimitError`` 之外的通用错误。
        - 2xx：抽 ``choices[0].message.content``、``usage.prompt_tokens`` /
          ``completion_tokens``，按 :func:`calculate_cost` 估算成本。

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
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        choices = data.get("choices") or []
        content = ""
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
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
