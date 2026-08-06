"""AI LLM provider 抽象层。

对外只暴露接口与工厂，具体 provider 实现隐藏在子模块。用法：

    from ai.providers import BaseLlmProvider, LlmResponse
    from ai.providers import create_llm_provider, get_strong_llm, get_fast_llm

    strong = get_strong_llm()
    resp = strong.chat_with_retry(prompt, temperature=0.0)
    print(resp.content, resp.cost_usd)

该层实现 ``app.infrastructure.interfaces.LlmProvider`` Protocol；
``LlmResponse.to_dict`` 桥接到 Protocol 要求的 dict 返回契约。
"""

from __future__ import annotations

from ai.providers.base import BaseLlmProvider, LlmResponse
from ai.providers.factory import (
    PROVIDER_REGISTRY,
    create_llm_provider,
    get_fast_llm,
    get_strong_llm,
)

__all__ = [
    "BaseLlmProvider",
    "LlmResponse",
    "PROVIDER_REGISTRY",
    "create_llm_provider",
    "get_strong_llm",
    "get_fast_llm",
]
