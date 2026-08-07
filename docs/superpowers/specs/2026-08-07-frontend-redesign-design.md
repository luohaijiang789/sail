# SAIL 前端规划与重构设计

> 日期：2026-08-07　|　状态：已批准

对 SAIL 扫描平台前端做系统性规划：信息架构、菜单结构、公共表格组件、各页面字段与布局。
目标是把当前"脚手架式拼凑"重构成围绕三张表（API 资产 / check / result）的表格驱动平台。

## 决策（已与用户确认）

| 决策点 | 选择 |
|---|---|
| 导航主轴 | 工作台为中心（功能模块驱动，跨仓库聚合） |
| 覆盖范围 | 全量（架构文档 09 规划的所有页面） |
| 交互密度 | 查看为主（少量操作：发起扫描/取消/重试/漏洞状态/反馈） |
| 公共表格组件 | 中等封装（SailProTable：列+筛选+分页+排序+标签着色） |
| 筛选维度 | 关键字搜索 + 标签多选下拉 + 数值范围（不含时间范围） |

## 1. 信息架构与菜单

工作台为中心，六个一级菜单，URL 扁平。各列表页顶部有仓库筛选器（切仓库后全局过滤）。

```
概览大盘   /dashboard
  统计卡片(扫描数/运行中/漏洞数/高危/仓库数/API数)
  最近扫描列表 + 高危漏洞 Top10

仓库管理   /repositories
  列表 + 详情(/repositories/:id)
  筛选:关键字 | 项目归属多选 | 仓库类型多选 | 最近扫描状态多选 | API数范围 | 高危数范围

扫描管理   /scans
  列表 + 详情(/scans/:id)
  详情:阶段时间线 + SSE实时进度 + 构建日志 + 失败原因 + 取消/重试 + 该扫描API资产

API 资产  /api-assets
  列表 + 详情(/api-assets/:id)
  详情:入口信息 + 调用链树 + 资源访问 + 安全控制 + check矩阵 + 该API漏洞 + 版本历史

check 矩阵 /check-matrix
  全局视图:API(行) × 检查项(列) = 单元格分级色块
  侧栏:覆盖率/盲区统计

漏洞清单   /findings
  列表 + 详情(/findings/:id)
  详情:左基本信息 | 中数据流Source→Sink | 右AI分析+证据+修复 | 底历史实例

报告       /reports
  扫描报告摘要(三张表统计/阶段耗时/漏洞分布) + 版本对比(安全分趋势)
```

## 2. 公共表格组件 SailProTable

所有列表页的基石，配置驱动，消除重复。

### 用法

```ts
<SailProTable
  :columns="columns"
  :fetcher="fetchRepositories"
  :filters="filterConfig"
  row-key="id"
  @row-click="goDetail"
/>
```

### 三部分

**FilterBar（筛选栏）** — 顶部，按 config 自动渲染：

| 控件类型 | 用途 | 后端参数 |
|---|---|---|
| `keyword` | 关键字输入框（模糊搜索） | `keyword` |
| `select` | 单选/多选下拉（标签） | `xxx_ids` 或 `xxx`（逗号分隔） |
| `numberRange` | 数值范围（min-max 两输入） | `min_xxx` / `max_xxx` |

筛选条件变化 → 自动触发 fetcher（带参数），防抖 300ms。

**表格主体** — ElTable 封装：
- 列配置 `columns: [{prop, label, width, sortable, tag?, formatter?}]`
- `tag` 列自动渲染 ElTag 着色（状态/严重度/等级 → 颜色映射）
- `sortable` 列点表头排序（前端排序，首版不做后端排序）
- 行点击 `@row-click`
- loading 态 / 空状态（ElEmpty）内置

**分页栏** — 底部 ElPagination，page/page_size 双向绑定，变化触发 fetcher。

### 通用辅助

- **statusColors.ts**：`{SUCCEEDED:'success', HIGH:'danger', CRITICAL:'danger', MEDIUM:'warning', LOW:'info', PASS:'success', NOT_CHECKED:'info', ...}` — 所有页面共用，严重度/状态/等级统一配色。
- **formatters.ts**：`fmtCommit(sha)`→短hash；`fmtTime(iso)`→`YYYY-MM-DD HH:MM`；`fmtJson(obj)`→摘要。

### 文件结构

```
frontend/apps/web-ele/src/
  components/
    sail-pro-table/
      index.vue           # SailProTable 主组件
      filter-bar.vue      # FilterBar 子组件
  utils/
    status-colors.ts      # 状态着色映射
    formatters.ts         # 字段格式化
```

## 3. 各页面字段与布局

### 3.1 概览大盘 `/dashboard`

- 6 个统计卡片（ElStatistic）：扫描总数/运行中/漏洞总数/高危/仓库数/API资产数
- 最近扫描（SailProTable 精简：仓库/状态/进度/构建质量/时间）
- 高危漏洞 Top10（SailProTable：标题/严重度/文件/所属API）
- 数据：`getScanStatsApi()` + `getFindingsApi({severity:'HIGH,CRITICAL', page_size:10})`

### 3.2 仓库管理 `/repositories`

**列表列**：

| 列 | 字段 | 着色/格式 |
|---|---|---|
| ID | id | — |
| 仓库名 | name | 可点击进详情 |
| Git URL | git_url | 截断+tooltip |
| 项目归属 | project_name | ElTag |
| 标签 | repository_type + status | ElTag |
| 默认分支 | default_branch | — |
| 最近 commit | last_scanned_commit | fmtCommit |
| 最近扫描状态 | last_scan_status | statusColors |
| API 数 | api_asset_count | — |
| 高危数 | high_risk_count | >0 红色 |
| 操作 | — | 发起扫描/编辑 |

**筛选**：keyword(名/URL) | 项目归属多选 | 仓库类型多选 | 最近扫描状态多选 | API数范围 | 高危数范围

**仓库详情** `/repositories/:id`（新增）：
- 基本信息（名称/URL/分支/类型/项目/创建时间）
- 扫描历史（SailProTable，按 repository_id 过滤）
- 漏洞概览（按严重度统计 + 列表）

> 后端需补：`RepositoryOut` 加 `project_name`、`last_scan_status`、`api_asset_count`、`high_risk_count` 冗余字段。

### 3.3 扫描管理 `/scans`

**列表列**：

| 列 | 字段 | 着色 |
|---|---|---|
| ID | id | — |
| 仓库 | repository_name | 需后端补冗余 |
| 状态 | status | statusColors |
| 进度 | progress | ElProgress |
| 构建质量 | build_quality | ElTag |
| 当前阶段 | current_stage | — |
| 模式 | mode | — |
| 开始时间 | started_at | fmtTime |
| 完成时间 | finished_at | fmtTime |
| 漏洞数 | finding_count | 需后端补冗余，>0 着色 |

**筛选**：keyword(仓库名) | 仓库多选 | 状态多选 | 构建质量多选 | 模式多选

**扫描详情** `/scans/:id`（增强）：
- 顶部状态卡：状态/进度/构建质量/模式/起止时间 + 取消/重试按钮
- 阶段时间线：13 阶段 ElTable（stage_type/status/attempt/required/on_failure/起止/metrics摘要/error）
- SSE 实时进度（新增）：RUNNING 时 EventSource 订阅 `subscribeScanEventsApi`，顶部进度条实时刷新
- 构建日志面板（新增）：`getScanLogsApi` 轮询拉取，滚动展示
- 该扫描的 API 资产入口（SailProTable 精简）

> 后端需补：`ScanOut` 加 `repository_name`、`finding_count` 冗余字段。

### 3.4 API 资产 `/api-assets`

**列表列**：

| 列 | 字段 | 着色 |
|---|---|---|
| ID | id | — |
| Method | http_method | ElTag(GET=info POST=warning...) |
| Path | full_path 或 path | 截断 |
| Controller | controller_class | — |
| 参数数 | param_count | 需后端补冗余 |
| 调用链深度 | call_chain_depth | — |
| 漏洞数 | finding_count | >0 红色 |
| 安全分 | overall_score | 数字+色(0-24绿/25-49黄/50-69橙/70+红) |
| 等级 | overall_level | statusColors |
| 状态 | status | ElTag |

**筛选**：keyword(路径/Controller) | 仓库多选 | HTTP方法多选 | 框架多选 | 安全等级多选 | 安全分范围 | 漏洞数范围

**API 资产详情** `/api-assets/:id`（按文档 09 布局）：

```
┌ 标题栏：GET /users/{id}  UserController.getUser  [安全分:72 HIGH_RISK] ┐
├──────────────┬─────────────────────────────────────────────────────────┤
│ 入口信息      │ 调用链树（ElTree，可展开）                                │
│ Method/参数/  │  UserController.getUser:44                               │
│ 鉴权/返回类型 │   ├─ UserService.findById:78                             │
│              │   │   └─ UserDao.queryById:132 → [DB] t_user (READ)     │
├──────────────┼─────────────────────────────────────────────────────────┤
│ check 矩阵   │ 安全控制（ElTable）                                      │
│ SQL注入:HIGH │ AUTHZ: @PreAuthorize hasRole('ADMIN')                   │
│ 鉴权缺失:NC  │ AUTHN: Spring Security Filter                            │
│ 覆盖率:85%   │ PARAM_VALIDATION: id @NotNull                            │
├──────────────┴─────────────────────────────────────────────────────────┤
│ 该 API 的漏洞（SailProTable 精简）                                     │
├───────────────────────────────────────────────────────────────────────┤
│ 版本历史（ElTimeline：v1.0(75,HIGH) → v1.1(45,LOW) → v1.2(72,HIGH)）    │
└───────────────────────────────────────────────────────────────────────┘
```

- 调用链树：`getCallTreeApi` → ElTree（首版数据可能空，保留组件）
- check 矩阵：`getApiChecksApi` → 紧凑列表（检查项名/结果色块/evidence）
- 安全画像：`getApiAssetSecurityApi` → 四维度分数 + 覆盖率 + 盲区
- 该 API 漏洞：`getApiAssetFindingsApi`
- 版本历史：`getApiAssetHistoryApi` → ElTimeline

> 后端需补：`ApiAssetListOut` 加 `param_count` 冗余字段。

### 3.5 check 矩阵 `/check-matrix`（新增）

全局视图：API（行）× 检查项（列）= 单元格色块。

```
┌ 侧栏：覆盖率 85% / 盲区 3 项 ┐  ┌ 矩阵主体 ────────────────────────────┐
│  注入类覆盖 100%            │  │ API              SQL注入 命令注入 鉴权 │
│  访问控制覆盖 60%           │  │ getUser          HIGH    PASS    NC   │
│  数据保护覆盖 0%            │  │ deleteUser       PASS    PASS    HIGH │
│  代码质量覆盖 0%            │  │ ...                                  │
└────────────────────────────┘  └──────────────────────────────────────┘
```

- 数据：后端新增 `GET /api/check-matrix?scan_run_id=X` 返回 `{apis:[{id,name}], checks:[{key,name,category}], cells:{[api_id]:{[check_key]:result}}}`
- 单元格色块：result → 背景色（CRITICAL/HIGH=红, MEDIUM=黄, LOW/NOT_CHECKED=灰, PASS=绿）
- 筛选：仓库多选 | 检查项类别多选 | 结果多选（只看高危）
- 首版：固定一个 scan_run_id，行数多时分页

### 3.6 漏洞清单 `/findings`

**列表列**：

| 列 | 字段 | 着色 |
|---|---|---|
| ID | id | — |
| 标题 | title | 可点击 |
| 严重度 | severity | statusColors |
| 规则 | rule_key | 需后端补冗余 |
| CWE | cwe | — |
| AI 结论 | ai_verdict | 需后端补冗余 |
| 文件 | file_path | 截断 |
| 所属 API | api_path | 需后端补冗余 |
| 状态 | status | statusColors |
| 首次 commit | first_seen_commit | fmtCommit |
| 创建时间 | created_at | fmtTime |

**筛选**：keyword(标题/文件) | 仓库多选 | 严重度多选 | 规则多选 | CWE多选 | AI结论多选 | 状态多选

**漏洞详情** `/findings/:id`（三栏布局）：

```
┌ 左：基本信息 ─┬─ 中：数据流 Source→CallPath→Sink ─┬─ 右：AI 分析 ─┐
│ 标题/严重度   │  ElTimeline 步骤列表              │ verdict(着色) │
│ 规则/CWE     │  source(warning)→节点(primary)    │ confidence   │
│ 文件/行号    │  →sink(danger)                    │ exploitability│
│ 状态(可改)   │  每步:file/line/desc              │ reasoning    │
│ commit       │                                   │ 修复建议      │
├──────────────┴───────────────────────────────────┴──────────────┤
│ 底：历史实例（同指纹跨扫描，ElTimeline）                          │
└────────────────────────────────────────────────────────────────┘
```

- 数据：`getFindingApi` + `getFindingDataflowApi` + `getFindingEvidenceApi` + `getFindingInstancesApi`

> 后端需补：`FindingListOut` 加 `rule_key`、`ai_verdict`、`api_path`、`cwe` 冗余字段。

### 3.7 报告 `/reports`（新增）

- 扫描报告摘要：三张表统计（API数/check数/漏洞数按严重度分布）+ 13 阶段耗时 + 构建质量
- 版本对比：同一仓库多次扫描的安全分趋势（ECharts 折线图）+ API 变化（新增/删除/变更）
- 数据：`getScanApi` + `getScanStatsApi` + `getScanApiDiffApi`

## 4. 后端需补内容汇总

### 4.1 列表项冗余字段（避免前端 N+1 查询）

| 接口/Schema | 补充字段 |
|---|---|
| `RepositoryOut` | `project_name`, `last_scan_status`, `api_asset_count`, `high_risk_count` |
| `ScanOut` | `repository_name`, `finding_count` |
| `ApiAssetListOut` | `param_count`（已有 finding_count/overall_score） |
| `FindingListOut` | `rule_key`, `ai_verdict`, `api_path`, `cwe` |

### 4.2 列表查询参数（支撑 FilterBar 筛选）

多选用逗号分隔字符串传（如 `severity=HIGH,CRITICAL`），后端 `split(",")` 解析。数值范围用 `min_xxx`/`max_xxx`。

| 接口 | 需补参数 |
|---|---|
| `/repositories` | `keyword`, `repository_types`, `last_scan_statuses`, `min_api_count`/`max_api_count`, `min_high_risk`/`max_high_risk` |
| `/api-assets` | `keyword`, `http_methods`, `frameworks`, `security_levels`, `min_score`/`max_score`, `min_finding_count`/`max_finding_count` |
| `/findings` | `keyword`, `rule_ids`, `cwes`, `ai_verdicts`, `statuses`(多选) |
| `/scans` | `keyword`, `statuses`(多选), `build_qualities`, `modes` |

### 4.3 新接口

- `GET /api/check-matrix?scan_run_id=X`：返回矩阵数据 `{apis, checks, cells}`

## 5. 实现顺序建议

1. **公共组件先行**：SailProTable + FilterBar + statusColors + formatters
2. **后端补字段+参数**：冗余字段 + 查询参数 + check-matrix 接口
3. **重构现有 6 页**：用 SailProTable 重写 repositories/scans/api-assets/findings 的列表+详情
4. **新增页面**：仓库详情 + check-matrix + reports + SSE实时进度 + 数据流可视化
5. **验证**：Playwright 脚本逐页验证

## 6. 不做的事（首版）

- 列拖拽排序/列显隐/虚拟滚动/导出CSV/保存筛选方案
- 后端排序（首版前端排序）
- 时间范围筛选
- 表格内联编辑/批量操作
- 实时日志流式（首版轮询）
