"""自动优化反馈闭环（ADR-24）。

对应架构文档 06-ai-analysis.md 与 ``feedback_analysis`` 表。强 LLM 对人工反馈做归因，
自动建议优化 prompt/规则/白名单，经人工 review 后应用并记录版本号。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ImprovementType = Literal["PROMPT", "RULE", "PATTERN", "NO_CHANGE"]


@dataclass
class FeedbackAnalysis:
    """反馈归因结果（对应 feedback_analysis 表）。

    Attributes:
        feedback_id: ``feedback_analysis.id``。
        root_cause: 强 LLM 归因的根因描述。
        improvement_type: 改进类型，见 :data:`ImprovementType`。
        improvement_suggestion: 改进建议（prompt 片段/规则 patch/误报 pattern）。
        applied_version: 应用后产出的版本号（未应用为 None）。
    """

    feedback_id: int
    root_cause: str = ""
    improvement_type: ImprovementType = "NO_CHANGE"
    improvement_suggestion: dict = field(default_factory=dict)
    applied_version: str | None = None


def analyze_feedback(feedback_id: int) -> FeedbackAnalysis:
    """强 LLM 对人工反馈做归因分析（ADR-24）。

    Args:
        feedback_id: ``feedback_analysis.id``。

    Returns:
        :class:`FeedbackAnalysis`，含 root_cause 与改进建议。
    """
    raise NotImplementedError


def apply_improvement(feedback_analysis_id: int) -> str:
    """应用改进并返回新版本号。

    根据 ``improvement_type`` 更新 prompt 模板 / 规则 pack / 误报白名单，
    产出新版本号写入对应 ``version`` 字段。

    Args:
        feedback_analysis_id: ``feedback_analysis.id``。

    Returns:
        应用后的版本号字符串（如 ``"1.1"``）。
    """
    raise NotImplementedError


def match_known_false_positive(check_item, code_context) -> bool:
    """匹配已知误报模式。

    用 ``analyze_feedback`` 沉淀的误报 pattern 库快速判定当前候选是否为已知误报，
    命中则跳过 AI 深度验证，降低成本。

    Args:
        check_item: 检查项（含 rule_key/symbol/file_path）。
        code_context: 候选处代码上下文（source/sink 代码片段）。

    Returns:
        True 表示命中已知误报模式。
    """
    raise NotImplementedError
