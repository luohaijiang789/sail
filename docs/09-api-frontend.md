# 09. API 与前端

> [← 08-orchestration](08-orchestration.md)　|　下一章：[10-platform](10-platform.md)

## 前端技术栈

基于 vue-vben-admin v5 monorepo 改造，使用 Element Plus 版（apps/web-ele）。

| 组件 | 选型 |
|---|---|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| UI | Element Plus |
| 状态 | Pinia |
| 路由 | Vue Router 4 |
| HTTP | Axios |
| 图表 | ECharts（安全分趋势/调用链可视化） |
| 框架能力 | vben 的布局/权限/国际化/动态路由 |

前端目录：`frontend/apps/web-ele/src/`，页面在 `views/`，API 封装在 `api/sail/`，路由在 `router/routes/modules/sail.ts`。

## REST API

```
# 仓库
POST   /api/repositories
GET    /api/repositories
GET    /api/repositories/{id}
PATCH  /api/repositories/{id}
POST   /api/repositories/{id}/validate

# 扫描
POST   /api/scans
GET    /api/scans
GET    /api/scans/{scan_id}
POST   /api/scans/{scan_id}/cancel
POST   /api/scans/{scan_id}/retry
POST   /api/scans/{scan_id}/stages/{stage_id}/retry
GET    /api/scans/{scan_id}/stages
GET    /api/scans/{scan_id}/logs          # 流式日志
GET    /api/scans/{scan_id}/events        # SSE

# API 资产
GET    /api/api-assets                     # 列表
GET    /api/api-assets/{asset_id}          # 详情
GET    /api/api-assets/{asset_id}/call-tree
GET    /api/api-assets/{asset_id}/resources
GET    /api/api-assets/{asset_id}/security
GET    /api/api-assets/{asset_id}/checks   # check 表
GET    /api/api-assets/{asset_id}/findings # 该 API 的漏洞
GET    /api/api-assets/{asset_id}/history  # 版本历史
GET    /api/scans/{scan_id}/api-assets
GET    /api/scans/{scan_id}/api-diff       # API 变化对比

# 漏洞
GET    /api/findings
GET    /api/findings/{finding_id}
PATCH  /api/findings/{finding_id}/status
GET    /api/findings/{finding_id}/evidence
GET    /api/findings/{finding_id}/dataflow

# 反馈
POST   /api/api-assets/{asset_id}/checks/{check_id}/feedback

# 内部回调（Worker → API）
POST   /internal/stages/{stage_id}/complete
POST   /internal/stages/{stage_id}/fail
```

创建扫描：`{"repository_id":12, "revision":{"type":"branch","value":"main"}, "scan_profile_id":3, "ai_analysis":true}`

## 前端页面

| 页面 | 核心 |
|---|---|
| 仓库列表 | 名称、分支、最近commit、扫描状态、高危数、API数 |
| 创建扫描 | 分支/Tag/Commit、构建方案、规则包、AI开关 |
| 扫描详情 | 阶段时间线 + 实时日志 + 构建质量 + 失败原因 + 重试/取消 |
| **API 资产列表** | Method/Path/Controller/参数数/调用链深度/资源数/漏洞数/安全分/状态 |
| **API 资产详情** | 入口信息 + 调用链树 + 资源访问 + 安全控制 + check矩阵 + 该API漏洞 + 版本历史 |
| **check 矩阵视图** | API × 检查项 = 分级结果，含覆盖率和盲区 |
| 漏洞列表 | 筛选：严重度/规则/CWE/AI结论/文件/所属API/NEW-RECURRING |
| 漏洞详情 | 左：基本信息；中：Source→CallPath→Sink；右：AI分析+证据+修复；底：历史 |

### API 资产详情页

```
┌───────────────────────────────────────────────────────────────────────┐
│ GET /users/{id}  UserController.getUser  [安全分: 72 HIGH_RISK]        │
├──────────────┬────────────────────────────────────────────────────────┤
│ 入口信息      │ 调用链（可展开树）                                      │
│ Method: GET  │ UserController.getUser:44                               │
│ 参数: id(path)│  ├─ UserService.findById:78                            │
│ 鉴权: @PreAuth│  │   ├─ UserDao.queryById:132 → [DB] t_user (READ)    │
│ 返回: User   │  │   └─ AuditService.log:145                           │
├──────────────┼────────────────────────────────────────────────────────┤
│ check 矩阵   │ 安全控制                                                │
│ SQL注入: HIGH│ AUTHZ: @PreAuthorize hasRole('ADMIN')                   │
│ 鉴权缺失: NC │ AUTHN: Spring Security Filter [GLOBAL]                 │
│ 参数校验: MED│ PARAM_VALIDATION: id @NotNull                          │
│ 覆盖率: 85%  │                                                        │
├──────────────┴────────────────────────────────────────────────────────┤
│ 该 API 的漏洞：1 个                                                  │
│ [HIGH] SQL Injection in UserDao.queryById                             │
├───────────────────────────────────────────────────────────────────────┤
│ 版本历史：v1.0(75,HIGH) → v1.1(45,LOW) → v1.2(72,HIGH)               │
└───────────────────────────────────────────────────────────────────────┘
```

## SSE 断线重连（ADR-10）

每个事件带 `event_seq`，客户端重连带 `Last-Event-ID`，服务端补发缺失事件。事件持久化到 Redis（24h）+ MySQL（长期）。
