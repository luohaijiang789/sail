# 04. check 表、安全画像与优化机制

> [← 03-api-asset](03-api-asset.md)　|　下一章：[05-finding-model](05-finding-model.md)

## check 表：检查项矩阵（ADR-20）

每个 API × 每个检查项 = 一个分级结果。是 finding 模型的超集——含 PASS（查了没问题）和 NOT_CHECKED（盲区）。

```
API              | SQL注入 | XSS | 鉴权缺失 | 参数校验 | 敏感数据 | ...
GET /users/{id}  | HIGH    | PASS| CRITICAL | MEDIUM   | LOW      |
POST /login      | PASS    | PASS| PASS     | PASS     | MEDIUM   |
```

### 预定义必查清单（20 项）

| 检查项 | 类别 | 判定来源 |
|---|---|---|
| SQL注入/命令注入/XPath注入/LDAP注入 | 注入 | CodeQL |
| XSS/开放重定向 | 客户端 | CodeQL |
| 反序列化/SSRF/路径遍历 | 服务端 | CodeQL |
| 鉴权缺失/授权不足 | 访问控制 | API 资产 |
| 参数校验缺失/CSRF缺失/限流缺失 | 访问控制 | API 资产 |
| 敏感数据返回/敏感数据访问 | 数据保护 | API 资产 |
| 硬编码凭证/弱加密/空catch/不安全随机数 | 代码质量 | CodeQL |

清单可扩展。CodeQL 类由规则扫描决定；API 资产类由资产信息判定。

### api_check 模型

```
api_check: id, api_asset_id, scan_run_id, source_revision_id,
  check_item_key, check_item_name, check_category, check_source(CODEQL/API_ASSET/MIXED),
  result(PASS/LOW/MEDIUM/HIGH/CRITICAL/NOT_CHECKED),
  finding_candidate_id, evidence_summary, detail_json, checked_at
```

### result 六态

PASS / LOW / MEDIUM / HIGH / CRITICAL / NOT_CHECKED（未检查盲区）

### 生成时机

ASSESS_API_SECURITY 阶段：CodeQL 结果填检查项 + API 资产判定填检查项 → 合并成完整 check 表。规则未启用的填 NOT_CHECKED。

## 安全画像：四维度汇总

基于 check 表逐项结果汇总成四维度评分。

| 维度 | 权重 | 包含检查项 |
|---|---|---|
| 暴露面与访问控制 | 30% | 鉴权/授权/校验/CSRF/限流 |
| 调用链风险 | 35% | 注入/反序列化/SSRF/路径遍历 |
| 数据敏感性 | 20% | 敏感数据返回/访问 |
| 代码质量 | 15% | 硬编码/弱加密/空catch |

维度分 = max(该维度检查项映射分：CRITICAL=100/HIGH=80/MEDIUM=60/LOW=40/PASS=0)

```
overall_score = round(exposure×0.30 + callchain×0.35 + data×0.20 + codequality×0.15)
```

等级：0-24 SAFE / 25-49 LOW_RISK / 50-69 MEDIUM_RISK / 70-84 HIGH_RISK / 85-100 CRITICAL

```
api_security_profile: id, api_asset_id, scan_run_id, overall_score, overall_level,
  exposure_score, callchain_score, data_sensitivity_score, codequality_score,
  check_coverage, blind_spots, risk_factors_json, ai_assessment, assessed_at
```

**check_coverage 和 blind_spots** 显式呈现检查覆盖度——不只看发现了什么，还看覆盖了多少。

## 版本迭代对比（ADR）

所有 API 数据绑定 commit_sha，通过 fingerprint 跨版本关联（fingerprint 不含参数/调用链内容，那些是 diff 点）。

### 逐项 diff 明细

```
api_version_diff: id, api_asset_id, prev_api_asset_id, scan_run_id, prev_scan_run_id,
  change_type(NEW/REMOVED/CHANGED/UNCHANGED), changes_json,
  security_score_delta, risk_delta
```

changes_json 按维度组织：入口信息/参数/调用链/资源/安全控制/漏洞/安全画像，每个维度有 added/removed/modified。

### 安全分趋势

```
v1.0: 75(HIGH) → v1.1: 45(LOW) → v1.2: 30(LOW)
变化点：v1.0→v1.1 新增鉴权 exposure-30；v1.1→v1.2 修复SQL注入 callchain-15
```

## 四个优化机制

### 优化一：同 API 多检查项合并验证（ADR-21，第二阶段）

同一 API 的非 PASS 检查项共享上下文，合并成一次 LLM 调用。token 降 3-5 倍，且 AI 能交叉判断（无鉴权+SQL注入→可利用性拉高）。约束：单次上下文不超过模型窗口 60%。

### 优化二：增量扫描（ADR-22，第三阶段）

git diff 确定变更范围，通过调用链反向索引映射到受影响 API，只重新处理受影响 API。未变 API 复用上次结果。约束：CodeQL DB 仍全量重建，变更超 30% 退化为全量。

### 优化三：AI 分层过滤（ADR-23，第四阶段）

小模型先快速过滤明显误报（confidence>0.9 FALSE_POSITIVE→直接 PASS），不确定的交强模型深度验证。小模型成本 1/10，过滤 50% 误报省一半成本。

### 优化四：自动优化反馈闭环（ADR-24，第四阶段）

人工反馈不只存库，强 LLM 自动归因 → 判断改进方向 → 给具体建议 → 人工确认 → 应用。

```
人工标误报 + 原因
    ↓ 强 LLM 归因分析
    ↓ 三类改进方向：
      ① PROMPT → AI没看懂关键约束 → 给修改后的prompt片段
      ② RULE → CodeQL规则太宽 → 给规则收窄建议
      ③ PATTERN → 某代码模式确实安全 → 给白名单模式定义
    ↓ 人工确认
    ↓ 应用到 prompt版本/规则配置/白名单库
    ↓ 下次扫描自动生效 + 效果追踪
```

```
feedback_analysis: id, api_check_id, human_verdict, human_reason, ai_verdict_original,
  codeql_result_original, analysis_model, root_cause, improvement_type(PROMPT/RULE/PATTERN/NO_CHANGE),
  improvement_suggestion_json, suggestion_status(PENDING/APPROVED/REJECTED/APPLIED),
  applied_version, reviewer, review_notes
```

**关键约束**：不全自动应用（防漏报），不改 CodeQL 原始规则（在平台白名单层收窄），有效果追踪（对比改进前后同类误报数）。
