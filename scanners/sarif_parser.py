"""SARIF 解析器：把 CodeQL 产出的 SARIF 转为 FindingCandidate 原始数据。

对应 05-finding-model.md 的 FINDING_CANDIDATES 阶段。解析 SARIF results，提取
rule_id/severity/位置/symbol/source/sink/dataflow_path。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FindingCandidateData:
    """单条 Finding 候选原始数据。"""

    rule_id: str
    severity: str
    file_path: str
    start_line: int
    end_line: int
    symbol: str | None = None
    source_location: dict = field(default_factory=dict)
    sink_location: dict = field(default_factory=dict)
    dataflow_path: list[dict] = field(default_factory=list)
    cwe: str | None = None
    category: str | None = None


# SARIF level → 平台 severity
_LEVEL_TO_SEVERITY = {
    "error": "HIGH",
    "warning": "MEDIUM",
    "note": "LOW",
    "none": "INFO",
}


def parse_sarif(sarif_path: str) -> list[FindingCandidateData]:
    """解析 SARIF 文件，提取所有 results 为候选数据。"""
    data = json.loads(Path(sarif_path).read_text(encoding="utf-8"))
    candidates: list[FindingCandidateData] = []

    for run in data.get("runs", []):
        rules = _index_rules(run)
        results = run.get("results", [])
        for res in results:
            candidates.append(_result_to_candidate(res, rules))

    return [c for c in candidates if c.rule_id]


def _index_rules(run: dict) -> dict[str, dict]:
    """run.tool.driver.rules → {rule_id: rule}。"""
    rules: dict[str, dict] = {}
    for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
        rid = rule.get("id")
        if rid:
            rules[rid] = rule
    return rules


def _result_to_candidate(res: dict, rules: dict[str, dict]) -> FindingCandidateData:
    rule_id = res.get("ruleId") or res.get("rule", {}).get("id", "")
    rule = rules.get(rule_id, {})
    level = res.get("level") or rule.get("defaultConfiguration", {}).get("level", "warning")
    severity = _LEVEL_TO_SEVERITY.get(level, "MEDIUM")

    # 位置：CodeQL 第一个 location 是 sink/primary，codeFlows 描述数据流
    locations = res.get("locations", [])
    primary = locations[0].get("physicalLocation", {}) if locations else {}
    artifact = primary.get("artifactLocation", {}).get("uri", "")
    region = primary.get("region", {})
    start_line = region.get("startLine", 0)
    end_line = region.get("endLine", start_line)

    # 数据流：从 codeFlows 提取 source/sink
    source_loc: dict = {}
    sink_loc: dict = {"file": artifact, "line": start_line}
    path_nodes: list[dict] = []
    code_flows = res.get("codeFlows", [])
    if code_flows:
        steps = []
        for cf in code_flows:
            for fl in cf.get("threadFlows", []):
                steps.extend(fl.get("locations", []))
        if steps:
            first = steps[0].get("location", {}).get("physicalLocation", {})
            last = steps[-1].get("location", {}).get("physicalLocation", {})
            source_loc = {"file": first.get("artifactLocation", {}).get("uri", artifact),
                          "line": first.get("region", {}).get("startLine", start_line)}
            sink_loc = {"file": last.get("artifactLocation", {}).get("uri", artifact),
                        "line": last.get("region", {}).get("startLine", start_line)}
            for i, st in enumerate(steps):
                pl = st.get("location", {}).get("physicalLocation", {})
                msg = st.get("location", {}).get("message", {}).get("text", "")
                path_nodes.append({"step": i, "file": pl.get("artifactLocation", {}).get("uri", ""),
                                   "line": pl.get("region", {}).get("startLine", 0), "desc": msg})
    else:
        # 无 codeFlows：用 locations 做单点
        path_nodes = [{"step": 0, "file": artifact, "line": start_line, "desc": "primary location"}]

    symbol = res.get("locations", [{}])[0].get("message", {}).get("text") if locations else None

    # CWE 从 rule.tags
    cwe = None
    for tag in rule.get("properties", {}).get("tags", []):
        if tag.startswith("CWE-"):
            cwe = tag
            break

    return FindingCandidateData(
        rule_id=rule_id,
        severity=severity,
        file_path=artifact,
        start_line=start_line,
        end_line=end_line,
        symbol=symbol,
        source_location=source_loc,
        sink_location=sink_loc,
        dataflow_path=path_nodes,
        cwe=cwe,
        category=rule.get("properties", {}).get("precision"),
    )
