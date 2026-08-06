"""扫描内去重后处理器。

对应架构文档 05-finding-model.md。同一次扫描（同 commit、同 scan_run）内，若多条
:class:`FindingCandidateData` 的指纹相同，视为同一漏洞的重复报告（常见于 CodeQL 对
同一数据流路径产出多个 result），合并为单条候选。合并策略：保留首条（行号最小者），
取最高 severity。

跨扫描历史去重不在本后处理器职责内——那是 ``MERGE_FINDINGS`` 阶段用 fingerprint
匹配历史 :class:`~app.domain.finding.Finding` 的工作（见 05-finding-model.md「历史对比」）。
"""

from __future__ import annotations

from scanners.postprocessors.base import BasePostprocessor, register_postprocessor
from scanners.sarif_parser import FindingCandidateData


@register_postprocessor
class Deduplicator(BasePostprocessor):
    """扫描内去重后处理器。

    按 fingerprint 合并同 commit 内同指纹候选。依赖前置 ``fingerprint_calculator``
    已为每条候选计算并回填指纹；若指纹缺失则该条不参与去重（原样保留）。

    合并规则：
    - 同指纹组内按 ``start_line`` 升序排序，取首条作为代表。
    - severity 取组内最高（按 :data:`app.core.constants.SEVERITY_ORDER` 比较）。
    - ``dataflow_path`` 取最长者（信息最全）。
    - 其余字段取代表候选的值。
    """

    name = "deduplicator"

    def process(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """对候选列表做同 commit 内同指纹合并。

        Args:
            candidates: 已计算指纹的候选列表。

        Returns:
            去重后的候选列表（每个 fingerprint 仅保留一条合并后的代表）。
        """
        raise NotImplementedError

    @staticmethod
    def _merge_group(group: list[FindingCandidateData]) -> FindingCandidateData:
        """合并同指纹候选组为单条代表。

        Args:
            group: 同 fingerprint 的候选列表（至少 1 条）。

        Returns:
            合并后的代表候选（新对象）。
        """
        raise NotImplementedError

    @staticmethod
    def _severity_rank(severity: str) -> int:
        """返回 severity 在 :data:`app.core.constants.SEVERITY_ORDER` 中的序号，未知返回 0。"""
        raise NotImplementedError
