# 06. AI 分析层

> [← 05-finding-model](05-finding-model.md)　|　下一章：[07-risk-fusion](07-risk-fusion.md)

## 定位（D4）

AI 不发现漏洞，只对 CodeQL 产出的候选做：证据补全、真实性判断、可利用性判断、修复解释。

## 漏斗式验证（ADR-15）

借鉴 Vulnhalla 方法论：CodeQL 提供广度（全量扫描不漏），AI 提供深度（逻辑验证剔误报，目标剔除 >90%）。

## 从 API 入口出发验证（ADR-18）

**Java Web 攻击入口绝大部分是 API。** 不从告警行出发，从 API 入口出发：

```
CodeQL 报告: UserDao.queryById:132 SQL注入
    ↓ 定位: 属于哪个 API？查 finding_candidate.api_asset_id
GET /users/{id} → UserController.getUser → UserService.findById → UserDao.queryById
    ↓ 从 API 入口构建审计上下文:
    入口信息(参数/鉴权/校验) + 完整调用链(每跳代码片段)
    + Source代码 + Sink代码 + 数据流路径 + 安全控制 + 资源访问
    ↓ Evidence Bundle
```

| | 从告警行出发 | 从 API 入口出发 |
|---|---|---|
| 可利用性判断 | 难，不知怎么触达 | 直接，入口到 sink 完整路径 |
| 鉴权判断 | 看不到入口鉴权 | 入口信息含完整安全控制 |

漏洞无法关联到 API 时（api_asset_id 为空），退化为从告警行出发。

## 引导式提问（Guided Questions）

防止 AI 顺着 CodeQL 认定漏洞。强制回答四类审计问题：

1. **输入来源**：用户输入从哪个 API 参数进入？类型？校验是否充分？
2. **路径可达性**：API 是否需鉴权？是否生效？是否外网可达？
3. **Sink 约束**：是否用参数化查询？调用链上有没有 sanitizer？
4. **数据流完整性**：source→sink 是否完整？中间有无转换？

## NEED_MORE_CONTEXT 闭环（ADR-19）

AI 说"信息不够"时附带结构化 Need 列表，编排器自动补取后再问。受控多轮（最多 3 轮，每轮 ≤2000 行）。**不违反 D5**——AI 不主动访问文件系统，只声明需要什么，编排器代为补取。

```json
{"Need": [
  {"type": "CODE_SNIPPET", "symbol": "UserService.findById", "file": "UserService.java", "lines": "70-90"},
  {"type": "SECURITY_CONTROL", "api_asset_id": 123, "reason": "确认是否有全局Filter"}
]}
```

## 同 API 合并验证（ADR-21）

同一 API 的非 PASS 检查项合并成一次 LLM 调用，AI 逐项验证。token 降 3-5 倍，且能交叉判断。

## 结构化输出

```json
{
  "verdict": "LIKELY_TRUE_POSITIVE",
  "confidence": 0.88,
  "exploitability": "HIGH",
  "auth_required": true, "auth_enforced": true,
  "reachable_from_endpoint": true,
  "reasoning": {"input_source":"...", "path_reachability":"...", "sink_constraint":"...", "dataflow_integrity":"..."},
  "evidence": [{"file":"...", "lines":"...", "description":"..."}],
  "remediation": "...",
  "review_required": false
}
```

verdict: TRUE_POSITIVE / LIKELY_TRUE_POSITIVE / UNCERTAIN / LIKELY_FALSE_POSITIVE / FALSE_POSITIVE / NEED_MORE_CONTEXT / INSUFFICIENT_CONTEXT

## AI 与 CodeQL 的关系

AI 不能覆盖 CodeQL 结论，二者并列展示。AI 可向下否决（FALSE_POSITIVE 降级），不可向上升级。评分见 [07-risk-fusion](07-risk-fusion.md)。

## AI 缓存

```
cache_key = sha256(candidate_fingerprint + commit_sha + evidence_hash + model_version + prompt_version)
```

## ai_review 模型

```
ai_review: id, candidate_id, api_asset_id, model_provider, model_name, prompt_version,
  evidence_hash, round(NEED_MORE_CONTEXT轮次), verdict, confidence, exploitability,
  auth_required, auth_enforced, reachable_from_endpoint, response_json,
  need_requests_json, input_tokens, output_tokens, cost_usd, duration_seconds, status
```
