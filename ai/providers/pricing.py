"""LLM 价格表与成本估算（per 1M tokens，单位 USD）。

维护常见模型每百万 token 的输入/输出单价，供 provider 在调用结束后估算
``cost_usd``。价格随厂商调整会变动，集中在此一处维护，便于更新。

价格口径（公开页面对照，截至 2024-12）：
- OpenAI gpt-4o: input $2.5 / output $10.0
- OpenAI gpt-4o-mini: input $0.15 / output $0.6
- OpenAI gpt-4-turbo: input $10.0 / output $30.0
- Anthropic claude-3-5-sonnet: input $3.0 / output $15.0
- Anthropic claude-3-haiku: input $0.25 / output $1.25
- Anthropic claude-3-opus: input $15.0 / output $75.0
"""

from __future__ import annotations

# 每百万 token 的美元价格。键为模型名，值为 {"input": ..., "output": ...}。
# 未命中精确键时按前缀匹配（如 "gpt-4o-2024-08-06" 命中 "gpt-4o"）。
MODEL_PRICING: dict[str, dict[str, float]] = {
    # --- OpenAI ---
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    # --- Anthropic ---
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
}

# 未命中价格表时的兜底单价（per 1M tokens），避免未知模型报错导致整条调用失败。
_DEFAULT_INPUT_PRICE = 1.0
_DEFAULT_OUTPUT_PRICE = 3.0


def get_price(model: str) -> tuple[float, float]:
    """查模型单价，返回 (input_price, output_price) per 1M tokens。

    先精确匹配，再按 ``-`` 截断的前缀最长匹配（处理带日期后缀的版本号，如
    ``gpt-4o-2024-08-06`` 命中 ``gpt-4o``）。仍未命中返回兜底价。

    Args:
        model: 模型名（如 ``"gpt-4o"`` / ``"claude-3-5-sonnet-20240620"``）。

    Returns:
        ``(input_price_per_mtok, output_price_per_mtok)``。
    """
    if not model:
        return (_DEFAULT_INPUT_PRICE, _DEFAULT_OUTPUT_PRICE)

    # 1. 精确匹配
    if model in MODEL_PRICING:
        entry = MODEL_PRICING[model]
        return (entry["input"], entry["output"])

    # 2. 前缀最长匹配（按 "-" 切片逐级缩短）
    parts = model.split("-")
    for i in range(len(parts) - 1, 0, -1):
        candidate = "-".join(parts[:i])
        if candidate in MODEL_PRICING:
            entry = MODEL_PRICING[candidate]
            return (entry["input"], entry["output"])

    return (_DEFAULT_INPUT_PRICE, _DEFAULT_OUTPUT_PRICE)


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """按模型单价与 token 用量估算 USD 成本。

    Args:
        model: 模型名。
        input_tokens: 输入（prompt）token 数。
        output_tokens: 输出（completion）token 数。

    Returns:
        估算的美元成本（保留 6 位小数）。
    """
    input_price, output_price = get_price(model)
    cost = (input_tokens / 1_000_000.0) * input_price + (
        output_tokens / 1_000_000.0
    ) * output_price
    return round(cost, 6)
