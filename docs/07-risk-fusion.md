# 07. 风险融合

> [← 06-ai-analysis](06-ai-analysis.md)　|　下一章：[08-orchestration](08-orchestration.md)

## 后处理流水线

```
FindingCandidate + AI Review
    → Schema校验 → 路径标准化 → 符号标准化 → 指纹计算
    → 扫描内去重 → 历史匹配 → Endpoint绑定 → AI结论融合
    → 风险评分 → 落库
```

## 两段式评分（ADR-06）

**AI 可向下否决，不可向上升级。**

### 第一段：基础分（0-100）

```
规则严重度映射 0-60
    CRITICAL→50-60  HIGH→35-49  MEDIUM→20-34  LOW→10-19  INFO→0-9

上下文加权 0-40
    外部输入可控 0-15
    存在完整数据流 0-15
    属于HTTP Endpoint 0-10

基础分 = 规则严重度映射 + 上下文加权
```

### 第二段：AI verdict 硬调整

```
FALSE_POSITIVE        → min(base_score, 20)    # 封顶Low
LIKELY_FALSE_POSITIVE → min(base_score, 40)    # 封顶Medium
其他                  → base_score             # 不调整
```

- AI 不能把 LOW 升到 CRITICAL（向上无权）
- AI 能把 CRITICAL 降到 LOW（向下否决，排除误报的正当职责）
- 无 AI 分析 → 用 base_score，ai_verdict=null

### 等级

```
0-29 LOW / 30-49 MEDIUM / 50-69 HIGH / 70-100 CRITICAL
```

## 展示分离

前端同时展示三个值：

```
规则严重度：HIGH          ← CodeQL
AI 真实性：FALSE_POSITIVE（0.92） ← AI
最终风险：LOW（base=58, AI封顶20） ← 融合
```
