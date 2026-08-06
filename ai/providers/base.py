"""LLM provider 抽象基类与响应结构。

实现 ``app.infrastructure.interfaces.LlmProvider`` Protocol，为具体 provider
（OpenAI/Anthropic/…）提供统一抽象骨架：单次调用 ``chat``、带限流重试的
``chat_with_retry``、成本估算、限流/超时异常封装。具体 HTTP 调用由子类实现。

设计要点：
- :class:`LlmResponse` 是结构化返回（content/usage/cost/model/raw），比 Protocol 要求的
  ``dict`` 更安全；``to_dict`` 桥接到 :class:`LlmProvider` Protocol 的返回契约。
- 限流/超时统一映射到 ``LlmRateLimitError`` / ``LlmTimeoutError``，二者 ``retryable=True``，
  供编排器分类重试。
- ``chat_with_retry`` 用指数退避；遇 ``LlmRateLimitError`` 且响应带 ``Retry-After`` 时，
  按该值等待而非指数退避，遵守服务端回压。
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.core.exceptions import LlmRateLimitError, LlmTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class LlmResponse:
    """LLM 单次调用的结构化返回。

    Attributes:
        content: 模型输出的文本内容（已从响应体抽取）。
        input_tokens: 输入（prompt）token 数。
        output_tokens: 输出（completion）token 数。
        cost_usd: 本次调用估算的美元成本。
        model: 实际产生响应的模型名（可能含版本后缀）。
        raw_response: 原始响应体，调试/审计用；默认 None。
    """

    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    raw_response: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """转成 :class:`LlmProvider` Protocol 要求的 dict 形态。

        与 ``app.infrastructure.interfaces.LlmProvider.chat`` 文档约定一致：
        ``{content, input_tokens, output_tokens, cost_usd, model}``。
        """
        return {
            "content": self.content,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "model": self.model,
        }


class BaseLlmProvider(ABC):
    """LLM provider 抽象基类，实现 :class:`LlmProvider` Protocol。

    子类只需实现 :meth:`chat`（具体 HTTP 调用），即可获得重试、成本估算、
    限流/超时异常封装等通用能力。

    Args:
        api_key: 厂商 API Key。
        base_url: API 基地址（OpenAI 兼容端点 / Anthropic 端点；为空时用各厂商默认）。
        model: 默认模型名，``chat`` 未显式传 ``model`` 时使用。
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    # --- 抽象方法：由具体 provider 实现 ---

    @abstractmethod
    def chat(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 16384,
        response_format: dict[str, Any] | None = None,
    ) -> LlmResponse:
        """调用 LLM 完成一次 Chat。

        Args:
            prompt: 完整 prompt 字符串。
            model: 模型名；None 时用实例默认 ``self.model``。
            temperature: 采样温度，审计场景建议 0.0-0.2。
            max_tokens: 最大输出 token 数。
            response_format: 强制输出格式，如 ``{"type": "json_object"}``。

        Returns:
            :class:`LlmResponse`。

        Raises:
            LlmRateLimitError: 触发限流。
            LlmTimeoutError: 请求超时。
        """
        ...

    # --- 具体方法 ---

    def chat_with_retry(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> LlmResponse:
        """带限流重试的 Chat 调用（指数退避；遇 Retry-After 按其值等待）。

        只对 ``retryable`` 异常（``LlmRateLimitError`` / ``LlmTimeoutError``）重试，
        其他异常立即抛出。退避序列：1s → 2s → 4s（上限 60s）；若限流响应携带
        ``Retry-After``（秒），则取 ``max(retry_after, base)`` 等待。

        Args:
            prompt: 完整 prompt 字符串。
            model: 模型名；None 时用实例默认。
            temperature: 采样温度。
            max_retries: 最大重试次数（不含首次）。

        Returns:
            :class:`LlmResponse`。

        Raises:
            LlmRateLimitError: 重试耗尽仍被限流。
            LlmTimeoutError: 重试耗尽仍超时。
        """
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return self.chat(prompt, model=model, temperature=temperature)
            except (LlmRateLimitError, LlmTimeoutError) as exc:
                last_exc = exc
                if attempt >= max_retries:
                    logger.warning(
                        "LLM call exhausted retries: model=%s attempt=%d err=%s",
                        model or self.model,
                        attempt,
                        exc.error_code,
                    )
                    break
                # 计算退避：限流优先用 Retry-After，否则指数退避。
                wait = self._compute_backoff(exc, attempt)
                logger.info(
                    "LLM call retrying: model=%s attempt=%d wait=%.1fs err=%s",
                    model or self.model,
                    attempt + 1,
                    wait,
                    exc.error_code,
                )
                time.sleep(wait)
        # mypy: last_exc 必非 None（循环内至少捕过一次异常才会到此）
        assert last_exc is not None
        raise last_exc

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """按当前默认模型单价估算 USD 成本。

        Args:
            input_tokens: 输入 token 数。
            output_tokens: 输出 token 数。

        Returns:
            估算的美元成本。
        """
        from ai.providers.pricing import calculate_cost

        return calculate_cost(self.model, input_tokens, output_tokens)

    # --- 异常封装 ---

    def _handle_rate_limit(self, response: Any) -> None:
        """把 429 限流响应封装成 :class:`LlmRateLimitError`。

        从响应头解析 ``Retry-After``（秒），写入异常 context 供
        :meth:`chat_with_retry` 决定退避时长。

        Args:
            response: HTTP 响应对象（需能取到 status_code / headers）。

        Raises:
            LlmRateLimitError: 始终抛出。
        """
        retry_after: float | None = None
        headers = getattr(response, "headers", None) or {}
        raw = headers.get("Retry-After") or headers.get("retry-after")
        if raw is not None:
            try:
                retry_after = float(raw)
            except (TypeError, ValueError):
                retry_after = None
        ctx: dict[str, Any] = {"retry_after": retry_after}
        raise LlmRateLimitError(
            f"LLM rate limited (429); retry_after={retry_after}s",
            **ctx,
        )

    def _handle_timeout(self) -> None:
        """把请求超时封装成 :class:`LlmTimeoutError`。

        Raises:
            LlmTimeoutError: 始终抛出。
        """
        raise LlmTimeoutError("LLM request timed out")

    # --- 内部 ---

    @staticmethod
    def _compute_backoff(exc: Exception, attempt: int) -> float:
        """计算下一次重试前的等待秒数。

        - 限流异常带 ``retry_after``：取 ``max(retry_after, base)``（不少于指数基）。
        - 其他可重试异常：指数退避 ``2^attempt``，上限 60s。

        Args:
            exc: 捕获的可重试异常。
            attempt: 当前已尝试次数（0 起算）。

        Returns:
            等待秒数。
        """
        base = float(2 ** attempt)
        if isinstance(exc, LlmRateLimitError):
            retry_after = exc.context.get("retry_after")
            if retry_after is not None:
                return max(float(retry_after), base)
        return min(base, 60.0)
