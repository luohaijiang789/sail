# 05. 漏洞模型

> [← 04-check-and-security](04-check-and-security.md)　|　下一章：[06-ai-analysis](06-ai-analysis.md)

## RulePack 与 Rule

```
rule_pack: id, name, version, codeql_pack_name, artifact_id, checksum, status
rule: id, rule_pack_id, rule_key, name, category(DATAFLOW/SYNTAX/CONFIG/INHERITANCE),
      cwe, default_severity, requires_dataflow(bool), description, remediation, enabled
```

`requires_dataflow` 决定 NO_BUILD 模式下是否跳过。

## Finding 三层模型——明确创建时序（ADR-05）

```
FINDING_CANDIDATES: 解析 SARIF → FindingCandidate（含指纹）
    ↓
ASSEMBLE_CONTEXT: 为每个 candidate 预取 Evidence Bundle
    ↓
AI_ANALYZE: AI 产出 AI Review（挂在 candidate 上，不挂 instance）
    ↓
MERGE_FINDINGS:
    1. 用 candidate.fingerprint 匹配历史 Finding
    2. 命中→复用 finding_id；未命中→新建 Finding（upsert）
    3. 创建 FindingInstance，关联 candidate + finding
    ↓
PERSIST_RESULTS: 算风险评分，回填 instance 的 final_severity / risk_score
```

**AI Review 挂 candidate 不挂 instance**——消除"instance 要先存在才能挂 AI Review，但 AI Review 又是 instance 字段输入"的循环依赖。

## 三张表

```
finding_candidate: id, scan_run_id, scanner_id, rule_id, raw_severity, raw_confidence,
  file_path, start_line, end_line, symbol, source_location, sink_location,
  dataflow_path_json, api_asset_id(关联API资产), fingerprint,
  raw_artifact_id, evidence_bundle_id, ai_review_id, status

finding: id, repository_id, fingerprint, rule_id, severity, status(OPEN/FIXED/REAPPEARED/FALSE_POSITIVE),
  first_seen_scan_id, last_seen_scan_id, first_seen_commit, last_seen_commit,
  api_asset_id, title, description, remediation, created_at

finding_instance: id, finding_id, scan_run_id, source_revision_id, candidate_id,
  file_path, start_line, end_line, symbol, api_asset_id,
  raw_severity, final_severity, ai_verdict, ai_confidence, risk_score,
  status(NEW/RECURRING/REAPPEARED/RESOLVED)
```

## 指纹与归一化算法（D6 / ADR-09）

不用文件路径+行号，抗代码插入删除。

```python
fingerprint = sha256(
    rule_id
    + normalize_symbol(source_symbol)
    + normalize_symbol(sink_symbol)
    + normalize_symbol(enclosing_method)
    + normalize_dataflow_signature(dataflow_path)
    + normalize_path(file_path)
)
```

| 字段 | 归一化规则 |
|---|---|
| normalize_symbol | 去参数名/局部变量名，保留完全限定类名+方法名+参数**类型**序列 |
| normalize_dataflow_signature | 取路径上每节点的方法签名，`;` 分隔 |
| normalize_path | POSIX 相对路径，去 `./` |
| enclosing_method vs source_symbol | enclosing_method 是漏洞所在方法；source_symbol 是数据流起点符号 |

**不变性**：重命名变量/调整空格/移动位置 → 指纹不变。修改数据流路径上的方法调用 → 指纹变。

## 历史对比

```
fingerprint 在 finding 表存在？
  不存在 → NEW，新建 finding
  存在且上次 OPEN → RECURRING
  存在且上次 FIXED → REAPPEARED
  存在且上次 FALSE_POSITIVE → 保留，不再 AI 分析
```
