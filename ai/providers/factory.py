"""LLM provider 工厂与注册表。

按 ``settings.llm_provider`` 创建对应 provider 实例，并暴露强模型 / 快模型两个
便捷获取入口（对应 ``settings.llm_model_strong`` / ``settings.llm_model_fast``）。
新增 provider 只需：实现 :class:`BaseLlmProvider` 子类 → 注册到
:data:`PROVIDER_REGISTRY`。

使用方式：

    from ai.providers import get_strong_llm, get_fast_llm

    resp = get_strong_llm().chat_with_retry(prompt, temperature=0.0)
    fast = get_fast_llm().chat(prompt)
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.core.exceptions import ConfigError

from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.base import BaseLlmProvider
from ai.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

#: provider 注册表：provider 名 → provider 类。新增厂商在此登记。
PROVIDER_REGISTRY: dict[str, type[BaseLlmProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

# 工厂默认 provider 名，``create_llm_provider`` 未传参且 settings 未配置时兜底。
_DEFAULT_PROVIDER = "openai"


def create_llm_provider(
    provider: str | None = None, **kwargs: Any
) -> BaseLlmProvider:
    """按 provider 名创建 LLM provider 实例。

    解析顺序：``provider`` 参数 → ``settings.llm_provider`` → :data:`_DEFAULT_PROVIDER`。
    从 ``settings`` 读取 ``llm_api_key`` / ``llm_base_url`` / 模型名传给构造器；
    调用方可通过 ``kwargs`` 覆盖（如指定不同 model）。

    Args:
        provider: provider 名（``"openai"`` / ``"anthropic"``）；None 用 settings。
        **kwargs: 透传给 provider 构造器的参数，常用 ``model`` / ``api_key`` /
            ``base_url`` 覆盖。未提供的从 settings 取。

    Returns:
        :class:`BaseLlmProvider` 实例。

    Raises:
        ConfigError: provider 名未注册或 ``llm_api_key`` 为空。
    """
    name = provider or settings.llm_provider or _DEFAULT_PROVIDER
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        raise ConfigError(
            f"Unknown LLM provider: {name!r}; "
            f"registered={list(PROVIDER_REGISTRY)}"
        )

    api_key = kwargs.pop("api_key", settings.llm_api_key)
    base_url = kwargs.pop("base_url", settings.llm_base_url)
    model = kwargs.pop("model", settings.llm_model_strong)

    if not api_key:
        raise ConfigError(
            f"LLM api_key is empty; set SAIL_LLM_API_KEY for provider={name!r}"
        )

    logger.debug("Creating LLM provider: name=%s model=%s", name, model)
    return cls(api_key=api_key, base_url=base_url, model=model, **kwargs)


def get_strong_llm() -> BaseLlmProvider:
    """返回强模型 provider（``settings.llm_model_strong``）。

    用于深度验证、反馈归因等需要高推理能力的场景。

    Returns:
        配置为 ``llm_model_strong`` 的 :class:`BaseLlmProvider`。
    """
    return create_llm_provider(model=settings.llm_model_strong)


def get_fast_llm() -> BaseLlmProvider:
    """返回快速模型 provider（``settings.llm_model_fast``）。

    用于小模型快速过滤（ADR-23）等低成本、低延迟场景。

    Returns:
        配置为 ``llm_model_fast`` 的 :class:`BaseLlmProvider`。
    """
    return create_llm_provider(model=settings.llm_model_fast)
