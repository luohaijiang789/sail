# 03. API 资产表

> [← 02-build](02-build.md)　|　下一章：[04-check-and-security](04-check-and-security.md)

API 资产表是平台的第一张表、一等产物。每个 HTTP 接口一条完整记录，尽可能全。

## 分两层：轻量先出 + 深度后补（ADR-16）

```
编译成功
    ↓
第一层 EXTRACT_API_FACTS（Tree-sitter + 框架 Adapter + XML 解析）
    → 入口/参数/注解/Controller/MyBatis SQL/配置/提交人
    → 资产表初版立即可用（L1 字段）
    ↓
第二层 ENRICH_API_DEPTH（可选，技术可替换）
    → 跨文件调用链/资源访问/数据流
    → 补充 L2 字段，失败不影响初版
```

**为什么不用 CodeQL 提取**：CodeQL 太重（要建库编译），提取入口/参数/注解这些 AST 级信息是大材小用。Tree-sitter 快一个数量级。

## api_asset 主表（L1=轻量层，L2=深度层）

```
api_asset
├─ id, repository_id, source_revision_id, scan_run_id
├─ fingerprint              # sha256(method+path+controller+handler)，跨版本关联
├─ http_method, path, full_path, framework          # L1
├─ controller_class, handler_method, handler_signature  # L1
├─ file_path, start_line, end_line                  # L1
├─ consumes, produces, response_type                # L1
├─ parameters_json             # L1 参数完整清单（名/类型/来源/校验）
├─ module, api_group           # L1
├─ commit_author, commit_time  # L1 来自 git
├─ call_chain_depth            # L2 调用链深度（初版 null）
├─ enrichment_status           # INITIAL / ENRICHED / FAILED
├─ first_seen_scan_id, last_seen_scan_id
├─ status                      # ACTIVE / REMOVED / CHANGED
└─ created_at
```

### parameters_json

```json
[
  {"name": "id", "type": "Long", "source": "path", "required": true, "validation": ["@NotNull"]},
  {"name": "user", "type": "UserDTO", "source": "body", "required": true, "validation": ["@Valid"]}
]
```

## api_call_edge 调用链（L2）

```
api_call_edge: id, api_asset_id, scan_run_id, depth, caller_symbol, caller_file, caller_line,
               callee_symbol, callee_file, callee_line, callee_type(INTERNAL/LIBRARY/UNKNOWN),
               edge_kind(DIRECT_CALL/VIRTUAL_DISPATCH/LAMBDA/REFLECTION), parent_edge_id, path_signature
```

轻量层只产出单文件直接调用（depth=1），跨文件完整调用树由深度层补充。

## api_resource_access 资源访问（L1声明级 + L2调用链级）

```
api_resource_access: id, api_asset_id, call_edge_id, scan_run_id,
  source_layer(L1_DECLARED/L2_CALLCHAIN),
  resource_type(DB_TABLE/SQL_QUERY/HTTP_OUTBOUND/RPC/FILE_READ/FILE_WRITE/CACHE/QUEUE),
  resource_name, operation(READ/WRITE/DELETE/EXECUTE), detail_json, file_path, line, is_sensitive
```

## api_security_control 安全控制（L1）

```
api_security_control: id, api_asset_id, scan_run_id,
  control_type(AUTHN/AUTHZ/PARAM_VALIDATION/INPUT_SANITIZATION/RATE_LIMIT/CSRF/CORS),
  control_method, control_value, scope(ENDPOINT/METHOD/PARAM/GLOBAL), file_path, line, enforced
```

## 提取工具链

```
Tree-sitter Java    → AST（入口/参数/注解/符号）
框架 Adapter        → Spring/JAX-RS/Servlet/WebSocket 语义
配置解析器          → YAML/Properties/XML（含 MyBatis Mapper）
git                 → 提交人/时间
```

目录结构：
```
extractors/
├─ java/          # parser, source_index, symbol_table
├─ frameworks/    # spring, jaxrs, servlet, websocket
├─ api/           # endpoint_detector, param_extractor, security_scanner
├─ config/        # yaml, properties, xml, mybatis_parser
├─ models/        # api_asset, endpoint, symbol, code_fact
└─ pipeline.py
```

## 性能预期

单仓库（10万行 Java）轻量提取 30-60 秒，比 CodeQL 建库快一个数量级。

## 统一 code_fact

非 API 专属的通用事实（符号/配置/模块）存 `code_fact` 表，供 AI Evidence 和漏洞后处理使用。API 专属事实不进 code_fact，进独立的 API 资产表。

```
code_fact: id, scan_run_id, fact_type, source_type(TREE_SITTER/CODEQL/BYTECODE/...),
           confidence, file_path, start_line, symbol, properties_json, fingerprint
```
