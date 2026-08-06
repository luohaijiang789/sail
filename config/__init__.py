"""检查项配置加载器。从 config/check_items.yaml 加载。"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class CheckItemConfig(BaseModel):
    key: str
    name: str
    category: str
    source: str  # CODEQL / API_ASSET / MIXED
    codeql_rule: str | None = None
    requires_dataflow: bool = False
    cwe: str | None = None
    description: str | None = None
    risk_score: int = 0
    applies_to_methods: list[str] | None = None
    sensitive_field_patterns: list[str] | None = None
    sensitive_table_patterns: list[str] | None = None


class CheckItemsConfig(BaseModel):
    version: int
    check_items: list[CheckItemConfig]
    dimension_weights: dict[str, float]
    dimension_check_items: dict[str, list[str]]
    result_score_map: dict[str, int]
    score_ranges: dict[str, list[int]]


@lru_cache
def load_check_items_config() -> CheckItemsConfig:
    """加载检查项配置（单例缓存）。"""
    config_path = Path(__file__).parent / "check_items.yaml"
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return CheckItemsConfig(**raw)


def get_check_item(key: str) -> CheckItemConfig | None:
    """按 key 查单个检查项。"""
    config = load_check_items_config()
    for item in config.check_items:
        if item.key == key:
            return item
    return None


def get_check_items_by_source(source: str) -> list[CheckItemConfig]:
    """按来源过滤检查项（CODEQL / API_ASSET）。"""
    config = load_check_items_config()
    return [item for item in config.check_items if item.source == source]
