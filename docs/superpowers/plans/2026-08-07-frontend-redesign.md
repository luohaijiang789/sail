# SAIL 前端规划与重构 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 SAIL 前端从脚手架式拼凑重构成围绕三张表的表格驱动平台——公共 SailProTable 组件 + 6 个配置驱动的列表/详情页 + check 矩阵/报告新页面。

**Architecture:** 先建公共组件（SailProTable/FilterBar/statusColors/formatters），再补后端冗余字段与查询参数，然后用组件重写所有列表页与详情页。后端 FastAPI + 前端 Vue3+vben-admin+Element Plus。

**Tech Stack:** FastAPI/SQLAlchemy（后端）、Vue 3/TypeScript/Element Plus/vben-admin v5（前端）、Playwright（验证）

## Global Constraints

- 后端响应已被 ResponseWrapperMiddleware 包成 `{code:0, data:...}`，前端 `requestClient` 配 `responseReturn:'data'` 自动取 `data` 字段，所以 API 函数直接返回 `data` 内容（如 `{items, total}`）。
- 后端字段一律 snake_case，前端类型/视图也用 snake_case（不用 camelCase 转换），用 `any` 避免类型摩擦。
- 多选筛选参数用逗号分隔字符串传后端（如 `severity=HIGH,CRITICAL`）。
- 列表分页参数：`page`（从1起）+ `page_size`（1-100）。
- vben-admin 前端在 `frontend/apps/web-ele/src/`，视图 `views/`，API 封装 `api/sail/`，路由 `router/routes/modules/sail.ts`。
- 后端在 `/home/lhj/code/lhj/sail/app/`。
- 每个 task 结束后 Playwright 验证脚本 `scripts/verify_frontend.py` 应仍通过（登录→6页访问无 JS 报错）。
- 提交信息用 `feat:`/`fix:`/`refactor:` 前缀，结尾带 `Co-Authored-By: Claude <noreply@anthropic.com>`。

---

## 文件结构总览

**前端新增/修改：**
```
frontend/apps/web-ele/src/
  components/sail-pro-table/
    index.vue              # SailProTable 主组件（FilterBar+ElTable+分页）
    filter-bar.vue         # FilterBar 子组件（keyword/select/numberRange）
    types.ts               # Column/Fetcher/FilterConfig 类型定义
  utils/
    status-colors.ts       # 状态→ElTag type 映射
    formatters.ts          # fmtCommit/fmtTime/fmtJson
  views/
    dashboard/analytics/index.vue       # 重写
    repositories/list.vue               # 重写用 SailProTable
    repositories/detail.vue             # 新增
    scans/list.vue                      # 重写
    scans/detail.vue                    # 增强（SSE+日志）
    api-assets/list.vue                 # 重写
    api-assets/detail.vue               # 重写（调用链树等）
    check-matrix/index.vue              # 新增
    findings/list.vue                   # 重写
    findings/detail.vue                 # 重写（三栏+数据流）
    reports/index.vue                   # 新增
  api/sail/
    check-matrix.ts                     # 新增
  router/routes/modules/sail.ts         # 加仓库详情/check矩阵/报告路由
  types/sail.d.ts                       # 补 check-matrix 类型
```

**后端修改：**
```
app/api/schemas/repository.py    # RepositoryOut 加冗余字段
app/api/schemas/scan.py          # ScanOut 加冗余字段
app/api/schemas/finding.py       # FindingListOut 加冗余字段
app/api/schemas/api_asset.py     # ApiAssetListOut 加 param_count
app/api/repositories.py          # list 加多选/范围参数 + 冗余字段填充
app/api/scans.py                 # list 加多选参数 + 冗余字段填充
app/api/findings.py              # list 加多选/范围参数 + 冗余字段填充
app/api/api_assets.py            # list 加多选/范围参数
app/api/check_matrix.py          # 新增 check-matrix 路由
app/main.py                      # 注册 check_matrix router
```

---

## Task 1: 公共工具 — statusColors + formatters

**Files:**
- Create: `frontend/apps/web-ele/src/utils/status-colors.ts`
- Create: `frontend/apps/web-ele/src/utils/formatters.ts`

**Interfaces:**
- Produces: `statusTagType(record: string): ElTagType`、`fmtCommit(sha: string|null, len=12): string`、`fmtTime(iso: string|null): string`、`scoreColor(score: number): string`、`fmtJson(obj: any, max=80): string`

- [ ] **Step 1: 写 status-colors.ts**

```ts
// frontend/apps/web-ele/src/utils/status-colors.ts
/** 状态/严重度/等级 → Element Plus ElTag type 统一配色。所有页面共用。 */
export type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const MAP: Record<string, TagType> = {
  // 扫描/阶段状态
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED: 'danger',
  PARTIAL_SUCCEEDED: 'info',
  CANCELLED: 'info',
  CREATED: 'info',
  QUEUED: 'info',
  PENDING: 'info',
  SKIPPED: 'info',
  // 严重度
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
  // check 结果
  PASS: 'success',
  NOT_CHECKED: 'info',
  // 安全等级
  SAFE: 'success',
  LOW_RISK: 'success',
  MEDIUM_RISK: 'warning',
  HIGH_RISK: 'danger',
  CRITICAL: 'danger',
  // 仓库状态
  ACTIVE: 'success',
  // AI verdict
  TRUE_POSITIVE: 'danger',
  LIKELY_TRUE_POSITIVE: 'danger',
  UNCERTAIN: 'warning',
  LIKELY_FALSE_POSITIVE: 'info',
  FALSE_POSITIVE: 'info',
  NEED_MORE_CONTEXT: 'warning',
  INSUFFICIENT_CONTEXT: 'info',
  // 漏洞状态
  OPEN: 'danger',
  FIXED: 'success',
  REAPPEARED: 'warning',
  FALSE_POSITIVE: 'info',
};

export function statusTagType(value: string | null | undefined): TagType {
  if (!value) return 'info';
  return MAP[value] ?? 'info';
}

/** 安全分 0-100 → 颜色类（用于单元格背景/文字色） */
export function scoreColor(score: number): string {
  if (score >= 70) return 'text-red-500';
  if (score >= 50) return 'text-orange-500';
  if (score >= 25) return 'text-yellow-600';
  return 'text-green-500';
}
```

- [ ] **Step 2: 写 formatters.ts**

```ts
// frontend/apps/web-ele/src/utils/formatters.ts
/** commit SHA 截短（默认前 12 位）。 */
export function fmtCommit(sha: string | null | undefined, len = 12): string {
  if (!sha) return '—';
  return sha.length > len ? sha.slice(0, len) : sha;
}

/** ISO 时间 → YYYY-MM-DD HH:MM。 */
export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return iso.replace('T', ' ').slice(0, 16);
}

/** JSON 对象 → 摘要字符串（截断）。 */
export function fmtJson(obj: any, max = 80): string {
  if (!obj) return '—';
  const s = typeof obj === 'string' ? obj : JSON.stringify(obj);
  return s.length > max ? s.slice(0, max) + '…' : s;
}

/** metrics_json 摘要：取前 N 个 k=v 拼接。 */
export function fmtMetrics(metrics: Record<string, any> | null | undefined, n = 3): string {
  if (!metrics || typeof metrics !== 'object') return '—';
  const entries = Object.entries(metrics).slice(0, n);
  return entries.map(([k, v]) => `${k}=${typeof v === 'object' ? fmtJson(v, 30) : v}`).join(' · ');
}
```

- [ ] **Step 3: 提交**

```bash
cd /home/lhj/code/lhj/sail
git add frontend/apps/web-ele/src/utils/status-colors.ts frontend/apps/web-ele/src/utils/formatters.ts
git commit -m "feat(frontend): 公共工具 statusColors + formatters

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: SailProTable 公共组件

**Files:**
- Create: `frontend/apps/web-ele/src/components/sail-pro-table/types.ts`
- Create: `frontend/apps/web-ele/src/components/sail-pro-table/filter-bar.vue`
- Create: `frontend/apps/web-ele/src/components/sail-pro-table/index.vue`

**Interfaces:**
- Consumes: `statusTagType` from `#/utils/status-colors`、`fmtCommit/fmtTime/fmtJson/fmtMetrics` from `#/utils/formatters`
- Produces: `SailProTable` 组件（props: columns/fetcher/filters/rowKey；events: row-click）、`FilterBar` 组件

- [ ] **Step 1: 写 types.ts**

```ts
// frontend/apps/web-ele/src/components/sail-pro-table/types.ts
/** 列定义。tag 字段设为 true 时用 statusTagType 着色；formatter 自定义格式化。 */
export interface SailColumn {
  prop: string;
  label: string;
  width?: number | string;
  minWidth?: number | string;
  sortable?: boolean;
  tag?: boolean;             // 用 statusTagType(row[prop]) 渲染 ElTag
  formatter?: (row: any) => string;
  fixed?: 'left' | 'right';
  showOverflowTooltip?: boolean;
}

/** 筛选项定义。 */
export interface SailFilter {
  type: 'keyword' | 'select' | 'numberRange';
  field: string;             // 对应查询参数名（keyword 时为 'keyword'）
  label: string;
  placeholder?: string;
  options?: { label: string; value: string | number }[];  // select 用
  multiple?: boolean;        // select 是否多选
}

/** fetcher：接收查询参数，返回 { items, total }。 */
export type SailFetcher = (params: Record<string, any>) => Promise<{ items: any[]; total: number }>;
```

- [ ] **Step 2: 写 filter-bar.vue**

```vue
<!-- frontend/apps/web-ele/src/components/sail-pro-table/filter-bar.vue -->
<script lang="ts" setup>
import { reactive, watch } from 'vue';
import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton } from 'element-plus';
import type { SailFilter } from './types';

const props = defineProps<{
  filters: SailFilter[];
  modelValue: Record<string, any>;
}>();
const emit = defineEmits<{ 'update:modelValue': [val: Record<string, any>]; change: [] }>();

const form = reactive<Record<string, any>>({ ...props.modelValue });

// 同步外部初始值变化
watch(() => props.modelValue, (v) => {
  Object.assign(form, v);
}, { deep: true });

let timer: any = null;
function emitChange() {
  clearTimeout(timer);
  timer = setTimeout(() => {
    emit('update:modelValue', { ...form });
    emit('change');
  }, 300);  // 防抖 300ms
}

function reset() {
  for (const f of props.filters) {
    form[f.field] = f.type === 'numberRange' ? { min: undefined, max: undefined } : (f.multiple ? [] : '');
  }
  emitChange();
}
</script>

<template>
  <ElForm :inline="true" :model="form" class="mb-4">
    <ElFormItem v-for="f in filters" :key="f.field" :label="f.label">
      <!-- 关键字 -->
      <ElInput
        v-if="f.type === 'keyword'"
        v-model="form[f.field]"
        :placeholder="f.placeholder || '搜索'"
        clearable
        style="width: 200px"
        @input="emitChange"
      />
      <!-- 多选/单选下拉 -->
      <ElSelect
        v-else-if="f.type === 'select'"
        v-model="form[f.field]"
        :multiple="f.multiple"
        :placeholder="f.placeholder || '全部'"
        clearable
        collapse-tags
        collapse-tags-tooltip
        style="width: 200px"
        @change="emitChange"
      >
        <ElOption
          v-for="opt in f.options"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </ElSelect>
      <!-- 数值范围 -->
      <template v-else-if="f.type === 'numberRange'">
        <ElInput
          v-model.number="form[f.field].min"
          placeholder="最小"
          style="width: 90px"
          @input="emitChange"
        />
        <span class="mx-1">-</span>
        <ElInput
          v-model.number="form[f.field].max"
          placeholder="最大"
          style="width: 90px"
          @input="emitChange"
        />
      </template>
    </ElFormItem>
    <ElFormItem>
      <ElButton @click="reset">重置</ElButton>
    </ElFormItem>
  </ElForm>
</template>
```

- [ ] **Step 3: 写 index.vue（主组件）**

```vue
<!-- frontend/apps/web-ele/src/components/sail-pro-table/index.vue -->
<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue';
import { ElTable, ElTableColumn, ElTag, ElEmpty, ElPagination } from 'element-plus';
import FilterBar from './filter-bar.vue';
import { statusTagType } from '#/utils/status-colors';
import type { SailColumn, SailFetcher, SailFilter } from './types';

const props = withDefaults(defineProps<{
  columns: SailColumn[];
  fetcher: SailFetcher;
  filters?: SailFilter[];
  rowKey?: string;
  pageSize?: number;
}>(), {
  filters: () => [],
  rowKey: 'id',
  pageSize: 20,
});

const emit = defineEmits<{ 'row-click': [row: any] }>();

const data = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(props.pageSize);
const filterValues = ref<Record<string, any>>({});

// 初始化 filter 默认值
function initFilters() {
  for (const f of props.filters) {
    filterValues.value[f.field] = f.type === 'numberRange'
      ? { min: undefined, max: undefined }
      : (f.multiple ? [] : '');
  }
}

// 把 filterValues 展平成后端查询参数
function buildParams(): Record<string, any> {
  const params: Record<string, any> = { page: page.value, page_size: pageSize.value };
  for (const f of props.filters) {
    const v = filterValues.value[f.field];
    if (f.type === 'keyword') {
      if (v) params.keyword = v;
    } else if (f.type === 'select') {
      if (Array.isArray(v) && v.length) params[f.field] = v.join(',');
      else if (typeof v === 'string' && v) params[f.field] = v;
    } else if (f.type === 'numberRange') {
      if (v?.min != null) params[`min_${f.field}`] = v.min;
      if (v?.max != null) params[`max_${f.field}`] = v.max;
    }
  }
  return params;
}

async function loadData() {
  loading.value = true;
  try {
    const result = await props.fetcher(buildParams());
    data.value = result.items ?? [];
    total.value = result.total ?? 0;
  } catch (e: any) {
    data.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function onFilterChange() {
  page.value = 1;
  loadData();
}

function onPageChange(p: number) {
  page.value = p;
  loadData();
}

function onPageSizeChange(s: number) {
  pageSize.value = s;
  page.value = 1;
  loadData();
}

onMounted(() => {
  initFilters();
  loadData();
});
</script>

<template>
  <div>
    <FilterBar
      v-if="filters.length > 0"
      v-model="filterValues"
      :filters="filters"
      @change="onFilterChange"
    />
    <ElTable
      v-loading="loading"
      :data="data"
      :row-key="rowKey"
      stripe
      style="width: 100%"
      @row-click="(row: any) => emit('row-click', row)"
    >
      <ElTableColumn
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :sortable="col.sortable"
        :fixed="col.fixed"
        :show-overflow-tooltip="col.showOverflowTooltip ?? true"
      >
        <template #default="{ row }">
          <!-- tag 列：状态/严重度着色 -->
          <ElTag v-if="col.tag" :type="statusTagType(row[col.prop])" size="small">
            {{ row[col.prop] || '—' }}
          </ElTag>
          <!-- formatter 列 -->
          <span v-else-if="col.formatter">{{ col.formatter(row) }}</span>
          <!-- 普通文本 -->
          <span v-else>{{ row[col.prop] ?? '—' }}</span>
        </template>
      </ElTableColumn>
      <!-- 操作列插槽 -->
      <slot name="actions" />
    </ElTable>
    <ElEmpty v-if="!loading && data.length === 0" description="暂无数据" />
    <div v-if="total > 0" class="mt-4 flex justify-end">
      <ElPagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next, sizes"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="onPageChange"
        @size-change="onPageSizeChange"
      />
    </div>
  </div>
</template>
```

- [ ] **Step 4: 提交**

```bash
cd /home/lhj/code/lhj/sail
git add frontend/apps/web-ele/src/components/sail-pro-table/
git commit -m "feat(frontend): SailProTable 公共表格组件（FilterBar+ElTable+分页）

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: 后端补列表冗余字段 + 查询参数

**Files:**
- Modify: `app/api/schemas/repository.py`
- Modify: `app/api/schemas/scan.py`
- Modify: `app/api/schemas/finding.py`
- Modify: `app/api/schemas/api_asset.py`
- Modify: `app/api/repositories.py`
- Modify: `app/api/scans.py`
- Modify: `app/api/findings.py`
- Modify: `app/api/api_assets.py`

**Interfaces:**
- Produces: 各列表接口返回冗余字段（repository_name/project_name/rule_key/ai_verdict/api_path/param_count/finding_count 等）+ 支持 keyword/多选/范围查询参数

**说明：** 这个 task 改动较多但模式统一——每个 schema 加字段、每个路由加查询参数 + 冗余字段填充。为控制单 task 体积，分两个子步骤提交。

- [ ] **Step 1: 补 schema 冗余字段**

修改 `app/api/schemas/repository.py` 的 `RepositoryOut`，在 `created_at` 前加：

```python
    project_name: str | None = None
    last_scan_status: str | None = None
    api_asset_count: int = 0
    high_risk_count: int = 0
```

修改 `app/api/schemas/scan.py` 的 `ScanOut`，在 `mode` 后加：

```python
    repository_name: str | None = None
    finding_count: int = 0
```

修改 `app/api/schemas/finding.py` 的 `FindingListOut`，在 `created_at` 前加：

```python
    rule_key: str | None = None
    cwe: str | None = None
    ai_verdict: str | None = None
    api_path: str | None = None
    repository_id: int | None = None
```

修改 `app/api/schemas/api_asset.py` 的 `ApiAssetListOut`，加：

```python
    param_count: int = 0
```

- [ ] **Step 2: 补路由查询参数 + 冗余字段填充**

修改 `app/api/repositories.py` 的 `list_repositories`：

```python
@router.get("/", response_model=PaginatedResult[RepositoryOut])
def list_repositories(
    pagination: PaginationParams = Depends(),
    keyword: str | None = None,
    project_id: int | None = None,
    repository_types: str | None = None,
    last_scan_statuses: str | None = None,
    min_api_count: int | None = None,
    max_api_count: int | None = None,
    min_high_risk: int | None = None,
    max_high_risk: int | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[RepositoryOut]:
    """仓库列表，支持关键字/多选/范围筛选。"""
    from sqlalchemy import or_
    stmt = select(Repository).order_by(Repository.id.desc())
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(or_(Repository.name.like(kw), Repository.git_url.like(kw)))
    if project_id is not None:
        stmt = stmt.where(Repository.project_id == project_id)
    if repository_types:
        stmt = stmt.where(Repository.repository_type.in_(repository_types.split(",")))
    if last_scan_statuses:
        # last_scan_status 来自关联扫描，简化：按仓库 status 过滤（阶段一）
        stmt = stmt.where(Repository.status.in_(last_scan_statuses.split(",")))
    page = paginate(db, stmt, pagination)
    # 填充冗余字段
    from app.domain.api_asset import ApiAsset
    from app.domain.finding import Finding, FindingInstance
    from app.domain.source_assets import Project
    projects = {p.id: p.name for p in db.execute(select(Project)).scalars().all()}
    items = []
    for r in page.items:
        out = RepositoryOut.model_validate(r)
        out.project_name = projects.get(r.project_id)
        api_count = db.scalar(select(func.count()).select_from(ApiAsset)
                              .where(ApiAsset.repository_id == r.id)) or 0
        out.api_asset_count = api_count
        out.high_risk_count = db.scalar(select(func.count()).select_from(Finding)
                                       .where(Finding.repository_id == r.id,
                                              Finding.severity.in_(["HIGH", "CRITICAL"]))) or 0
        items.append(out)
    return PaginatedResult[RepositoryOut](items=items, total=page.total,
                                          page=page.page, page_size=page.page_size, has_next=page.has_next)
```

注意：文件顶部需 `from sqlalchemy import func, select, or_`（select 已有，补 func/or_）。

修改 `app/api/scans.py` 的 `list_scans`，参数加 `keyword`/`statuses`/`build_qualities`/`modes`（多选），填充 `repository_name`/`finding_count`：

```python
@router.get("/", response_model=PaginatedResult[ScanOut])
def list_scans(
    pagination: PaginationParams = Depends(),
    repository_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
    statuses: str | None = None,
    build_qualities: str | None = None,
    modes: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[ScanOut]:
    from app.domain.source_assets import Repository
    from app.domain.finding import FindingInstance
    stmt = select(ScanRun).order_by(ScanRun.id.desc())
    if repository_id is not None:
        stmt = stmt.where(ScanRun.repository_id == repository_id)
    if status:
        stmt = stmt.where(ScanRun.status == status)
    if statuses:
        stmt = stmt.where(ScanRun.status.in_(statuses.split(",")))
    if build_qualities:
        stmt = stmt.where(ScanRun.build_quality.in_(build_qualities.split(",")))
    if modes:
        stmt = stmt.where(ScanRun.mode.in_(modes.split(",")))
    if keyword:
        # keyword 匹配仓库名：先查仓库 id
        repo_ids = [r.id for r in db.execute(
            select(Repository).where(Repository.name.like(f"%{keyword}%"))).scalars().all()]
        if repo_ids:
            stmt = stmt.where(ScanRun.repository_id.in_(repo_ids))
        else:
            stmt = stmt.where(False)  # 无匹配仓库 → 空结果
    page = paginate(db, stmt, pagination)
    repos = {r.id: r.name for r in db.execute(select(Repository)).scalars().all()}
    items = []
    for s in page.items:
        out = ScanOut.model_validate(s)
        out.repository_name = repos.get(s.repository_id)
        out.finding_count = db.scalar(select(func.count()).select_from(FindingInstance)
                                      .where(FindingInstance.scan_run_id == s.id)) or 0
        items.append(out)
    return PaginatedResult[ScanOut](items=items, total=page.total,
                                    page=page.page, page_size=page.page_size, has_next=page.has_next)
```

修改 `app/api/findings.py` 的 `list_findings`，参数加 `keyword`/`rule_ids`/`cwes`/`ai_verdicts`/`statuses`(多选)，填充 `rule_key`/`cwe`/`ai_verdict`/`api_path`/`repository_id`：

```python
@router.get("/", response_model=PaginatedResult[FindingListOut])
def list_findings(
    pagination: PaginationParams = Depends(),
    severity: str | None = None,
    status: str | None = None,
    repository_id: int | None = None,
    keyword: str | None = None,
    statuses: str | None = None,
    rule_ids: str | None = None,
    cwes: str | None = None,
    ai_verdicts: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[FindingListOut]:
    from sqlalchemy import or_
    from app.domain.finding import Rule, AiReview, FindingCandidate, FindingInstance
    from app.domain.api_asset import ApiAsset
    stmt = select(Finding).order_by(Finding.id.desc())
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    if statuses:
        stmt = stmt.where(Finding.status.in_(statuses.split(",")))
    if repository_id is not None:
        stmt = stmt.where(Finding.repository_id == repository_id)
    if rule_ids:
        stmt = stmt.where(Finding.rule_id.in_([int(x) for x in rule_ids.split(",") if x.isdigit()]))
    if cwes:
        stmt = stmt.where(Finding.rule_id.in_(
            select(Rule.id).where(Rule.cwe.in_(cwes.split(",")))))
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(or_(Finding.title.like(kw), Finding.file_path.like(kw) if Finding.file_path else False))
    page = paginate(db, stmt, pagination)
    # 预载关联
    rule_map = {r.id: r for r in db.execute(
        select(Rule).where(Rule.id.in_([f.rule_id for f in page.items if f.rule_id]))).scalars().all()}
    asset_ids = [f.api_asset_id for f in page.items if f.api_asset_id]
    assets = {a.id: a for a in db.execute(select(ApiAsset).where(ApiAsset.id.in_(asset_ids))).scalars().all()} if asset_ids else {}
    items = []
    for f in page.items:
        out = FindingListOut.model_validate(f)
        rule = rule_map.get(f.rule_id)
        if rule:
            out.rule_key = rule.rule_key
            out.cwe = rule.cwe
        if f.api_asset_id and f.api_asset_id in assets:
            out.api_path = assets[f.api_asset_id].full_path or assets[f.api_asset_id].path
        out.repository_id = f.repository_id
        # ai_verdict：从最近 instance 的 candidate 的 ai_review 取
        inst = db.execute(select(FindingInstance).where(FindingInstance.finding_id == f.id)
                          .order_by(FindingInstance.id.desc())).scalars().first()
        if inst and inst.candidate_id:
            cand = db.get(FindingCandidate, inst.candidate_id)
            if cand and cand.ai_review_id:
                review = db.get(AiReview, cand.ai_review_id)
                if review:
                    out.ai_verdict = review.verdict
        items.append(out)
    return PaginatedResult[FindingListOut](items=items, total=page.total,
                                           page=page.page, page_size=page.page_size, has_next=page.has_next)
```

修改 `app/api/api_assets.py` 的 `list_api_assets`，参数加 `keyword`/`http_methods`/`frameworks`/`security_levels`/`min_score`/`max_score`/`min_finding_count`/`max_finding_count`。由于 ApiAssetListOut 的 overall_score/finding_count 来自子查询（看现有实现），keyword 加在 `controller_class`/`path`/`full_path` 的 like，http_methods/frameworks 用 `.in_(...)`，security_levels 用 `overall_score` 范围映射（阶段一简化：score >=70=HIGH_RISK 等，直接按 score 数值范围过滤）。具体改动看现有 list_api_assets 代码后补 filter。

> **注意：** api_assets.py 的 list 可能已用子查询算 overall_score/finding_count。改动时保持现有计算逻辑，只加 where 条件。implementer 需先 Read 该文件 list_api_assets 函数再改。

- [ ] **Step 3: 重启后端验证**

```bash
cd /home/lhj/code/lhj/sail
# 杀旧后端
kill $(pgrep -f "uvicorn app.main" | head -1) 2>/dev/null; sleep 2
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 no_proxy=localhost,127.0.0.1
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8765 --log-level warning > /tmp/sail-backend.log 2>&1 &
disown
sleep 4
# 验证冗余字段
curl -s "http://127.0.0.1:8765/api/repositories/?page=1&page_size=1" | .venv/bin/python -c "import sys,json; d=json.load(sys.stdin)['data']['items'][0]; print('repo:', d.get('project_name'), d.get('api_asset_count'), d.get('high_risk_count'))"
curl -s "http://127.0.0.1:8765/api/scans/?page=1&page_size=1" | .venv/bin/python -c "import sys,json; d=json.load(sys.stdin)['data']['items'][0]; print('scan:', d.get('repository_name'), d.get('finding_count'))"
curl -s "http://127.0.0.1:8765/api/findings/?page=1&page_size=1" | .venv/bin/python -c "import sys,json; d=json.load(sys.stdin)['data']['items'][0]; print('finding:', d.get('rule_key'), d.get('ai_verdict'), d.get('api_path'))"
# 验证多选筛选
curl -s "http://127.0.0.1:8765/api/findings/?severity=HIGH,CRITICAL&page=1&page_size=3" | .venv/bin/python -c "import sys,json; d=json.load(sys.stdin)['data']; print('multi-severity total:', d['total'])"
```
Expected: 各字段非 None，多选筛选返回正确数量。

- [ ] **Step 4: 提交**

```bash
cd /home/lhj/code/lhj/sail
git add app/api/schemas/ app/api/repositories.py app/api/scans.py app/api/findings.py app/api/api_assets.py
git commit -m "feat(backend): 列表冗余字段 + keyword/多选/范围查询参数

RepositoryOut 加 project_name/last_scan_status/api_asset_count/high_risk_count；
ScanOut 加 repository_name/finding_count；FindingListOut 加 rule_key/cwe/ai_verdict/api_path；
各列表接口支持 keyword 模糊 + 多选(逗号分隔) + min/max 范围筛选。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: 后端 check-matrix 接口

**Files:**
- Create: `app/api/check_matrix.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `GET /api/check-matrix?scan_run_id=X` → `{apis:[{id,name}], checks:[{key,name,category}], cells:{[api_id]:{[check_key]:result}}}`

- [ ] **Step 1: 写 check_matrix.py**

```python
"""check 矩阵全局视图路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.api_asset import ApiAsset
from app.domain.check_and_security import ApiCheck, PREDEFINED_CHECK_ITEMS
from app.infrastructure.database import get_db

router = APIRouter(prefix="/api/check-matrix", tags=["check-matrix"])


@router.get("/")
def get_check_matrix(
    scan_run_id: int = Query(..., description="扫描 ID"),
    db: Session = Depends(get_db),
) -> dict:
    """返回 API(行) × 检查项(列) 矩阵数据。"""
    apis = db.execute(
        select(ApiAsset.id, ApiAsset.full_path, ApiAsset.path, ApiAsset.controller_class)
        .where(ApiAsset.scan_run_id == scan_run_id)
        .order_by(ApiAsset.id)
    ).all()
    checks = db.execute(
        select(ApiCheck.api_asset_id, ApiCheck.check_item_key, ApiCheck.result)
        .where(ApiCheck.scan_run_id == scan_run_id)
    ).all()

    # cells[api_id][check_key] = result
    cells: dict[int, dict[str, str]] = {}
    for c in checks:
        cells.setdefault(c.api_asset_id, {})[c.check_item_key] = c.result

    return {
        "apis": [{"id": a.id, "name": a.full_path or a.path or a.controller_class} for a in apis],
        "checks": [{"key": i["key"], "name": i["name"], "category": i["category"]}
                   for i in PREDEFINED_CHECK_ITEMS],
        "cells": cells,
    }
```

- [ ] **Step 2: 注册路由到 main.py**

在 `app/main.py` 的 `from app.api import ...` 行加 `check_matrix`，并在 `app.include_router(internal.router, ...)` 后加：

```python
app.include_router(check_matrix.router, tags=["check-matrix"])
```

- [ ] **Step 3: 验证**

```bash
kill $(pgrep -f "uvicorn app.main" | head -1) 2>/dev/null; sleep 2
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 no_proxy=localhost,127.0.0.1
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8765 --log-level warning > /tmp/sail-backend.log 2>&1 &
disown
sleep 4
curl -s "http://127.0.0.1:8765/api/check-matrix/?scan_run_id=2" | .venv/bin/python -c "import sys,json; d=json.load(sys.stdin)['data']; print('apis:', len(d['apis']), 'checks:', len(d['checks']), 'cells:', len(d['cells']))"
```
Expected: apis=198, checks=20, cells=198。

- [ ] **Step 4: 提交**

```bash
cd /home/lhj/code/lhj/sail
git add app/api/check_matrix.py app/main.py
git commit -m "feat(backend): check-matrix 全局视图接口

GET /api/check-matrix?scan_run_id=X 返回 API×检查项矩阵数据。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: 重写仓库列表 + 新增仓库详情

**Files:**
- Modify: `frontend/apps/web-ele/src/views/repositories/list.vue`
- Create: `frontend/apps/web-ele/src/views/repositories/detail.vue`
- Modify: `frontend/apps/web-ele/src/router/routes/modules/sail.ts`

**Interfaces:**
- Consumes: `SailProTable` from `#/components/sail-pro-table`、`getRepositoriesApi` from `#/api/sail/repositories`、`statusTagType`/`fmtCommit` from `#/utils/*`

- [ ] **Step 1: 重写 list.vue 用 SailProTable**

```vue
<!-- frontend/apps/web-ele/src/views/repositories/list.vue -->
<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElButton } from 'element-plus';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getRepositoriesApi } from '#/api/sail/repositories';
import { fmtCommit } from '#/utils/formatters';

defineOptions({ name: 'RepositoryList' });
const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'name', label: '仓库名', minWidth: 140 },
  { prop: 'git_url', label: 'Git URL', minWidth: 260, showOverflowTooltip: true },
  { prop: 'project_name', label: '项目归属', width: 120 },
  { prop: 'repository_type', label: '类型', width: 100 },
  { prop: 'default_branch', label: '默认分支', width: 100 },
  { prop: 'last_scanned_commit', label: '最近commit', width: 130, formatter: (r) => fmtCommit(r.last_scanned_commit) },
  { prop: 'last_scan_status', label: '扫描状态', width: 120, tag: true },
  { prop: 'api_asset_count', label: 'API数', width: 80 },
  { prop: 'high_risk_count', label: '高危', width: 80 },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '名称/URL' },
  { type: 'select', field: 'repository_types', label: '类型', multiple: true,
    options: [{ label: 'git', value: 'git' }, { label: 'java-spring', value: 'java-spring' }] },
  { type: 'select', field: 'last_scan_statuses', label: '扫描状态', multiple: true,
    options: [{ label: '成功', value: 'SUCCEEDED' }, { label: '运行中', value: 'RUNNING' }, { label: '失败', value: 'FAILED' }] },
  { type: 'numberRange', field: 'api_count', label: 'API数' },
  { type: 'numberRange', field: 'high_risk', label: '高危数' },
];

function goDetail(row: any) { router.push(`/repositories/${row.id}`).catch(() => {}); }
function createScan(row: any) { router.push(`/scans/create?repositoryId=${row.id}`).catch(() => {}); }
</script>

<template>
  <Page description="管理受扫描的代码仓库" title="仓库管理">
    <div class="p-4">
      <SailProTable :columns="columns" :fetcher="getRepositoriesApi" :filters="filters" @row-click="goDetail">
        <template #actions>
          <ElTableColumn label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <ElButton link type="primary" @click.stop="createScan(row)">发起扫描</ElButton>
            </template>
          </ElTableColumn>
        </template>
      </SailProTable>
    </div>
  </Page>
</template>
```

> 注意：需 import `ElTableColumn` 用于 actions slot。

- [ ] **Step 2: 写 detail.vue**

```vue
<!-- frontend/apps/web-ele/src/views/repositories/detail.vue -->
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElCard, ElDescriptions, ElDescriptionsItem, ElButton, ElTag } from 'element-plus';
import { getRepositoryApi, getScansApi, getFindingsApi } from '#/api/sail/repositories';
import { getScansApi as getScans } from '#/api/sail/scans';
import { getFindingsApi as getFindings } from '#/api/sail/findings';
import { fmtTime, fmtCommit } from '#/utils/formatters';
import { statusTagType } from '#/utils/status-colors';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn } from '#/components/sail-pro-table/types';

defineOptions({ name: 'RepositoryDetail' });
const route = useRoute();
const router = useRouter();
const repo = ref<any>(null);

const scanColumns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'status', label: '状态', width: 120, tag: true },
  { prop: 'progress', label: '进度', width: 80 },
  { prop: 'build_quality', label: '构建质量', width: 140 },
  { prop: 'started_at', label: '开始', width: 160, formatter: (r) => fmtTime(r.started_at) },
  { prop: 'finding_count', label: '漏洞数', width: 80 },
];
const findingColumns: SailColumn[] = [
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'severity', label: '严重度', width: 90, tag: true },
  { prop: 'status', label: '状态', width: 90, tag: true },
];

onMounted(async () => {
  const id = Number(route.params.id);
  repo.value = await getRepositoryApi(id);
});
</script>

<template>
  <Page :title="repo?.name || '仓库详情'" description="">
    <div class="p-4 space-y-4">
      <ElCard v-if="repo" shadow="never">
        <template #header>基本信息</template>
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="仓库名">{{ repo.name }}</ElDescriptionsItem>
          <ElDescriptionsItem label="Git URL">{{ repo.git_url }}</ElDescriptionsItem>
          <ElDescriptionsItem label="默认分支">{{ repo.default_branch }}</ElDescriptionsItem>
          <ElDescriptionsItem label="项目归属">{{ repo.project_name || '—' }}</ElDescriptionsItem>
          <ElDescriptionsItem label="类型">{{ repo.repository_type }}</ElDescriptionsItem>
          <ElDescriptionsItem label="最近commit">{{ fmtCommit(repo.last_scanned_commit) }}</ElDescriptionsItem>
          <ElDescriptionsItem label="API数">{{ repo.api_asset_count }}</ElDescriptionsItem>
          <ElDescriptionsItem label="高危数">{{ repo.high_risk_count }}</ElDescriptionsItem>
        </ElDescriptions>
        <ElButton class="mt-4" type="primary" @click="router.push(`/scans/create?repositoryId=${repo.id}`)">发起扫描</ElButton>
      </ElCard>
      <ElCard shadow="never">
        <template #header>扫描历史</template>
        <SailProTable :columns="scanColumns" :fetcher="(p) => getScans({ ...p, repository_id: repo?.id })" @row-click="(r) => router.push(`/scans/${r.id}`)" />
      </ElCard>
      <ElCard shadow="never">
        <template #header>漏洞概览</template>
        <SailProTable :columns="findingColumns" :fetcher="(p) => getFindings({ ...p, repository_id: repo?.id })" @row-click="(r) => router.push(`/findings/${r.id}`)" />
      </ElCard>
    </div>
  </Page>
</template>
```

- [ ] **Step 3: 加路由**

在 `sail.ts` 的 Repositories 路由后加子路由 detail：

```ts
  {
    name: 'RepositoryDetail',
    path: '/repositories/:id',
    component: () => import('#/views/repositories/detail.vue'),
    meta: { title: '仓库详情', hideInMenu: true, activePath: '/repositories' },
  },
```

- [ ] **Step 4: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -15
git add frontend/apps/web-ele/src/views/repositories/ frontend/apps/web-ele/src/router/routes/modules/sail.ts
git commit -m "feat(frontend): 重写仓库列表用 SailProTable + 新增仓库详情页

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: 重写扫描列表 + 增强扫描详情（SSE+日志）

**Files:**
- Modify: `frontend/apps/web-ele/src/views/scans/list.vue`
- Modify: `frontend/apps/web-ele/src/views/scans/detail.vue`

**Interfaces:**
- Consumes: `SailProTable`、`getScansApi`/`getScanApi`/`getScanStagesApi`/`cancelScanApi`/`subscribeScanEventsApi`/`getScanLogsApi`、`statusTagType`/`fmtTime`/`fmtMetrics`

- [ ] **Step 1: 重写 list.vue**

```vue
<!-- frontend/apps/web-ele/src/views/scans/list.vue -->
<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElButton } from 'element-plus';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getScansApi } from '#/api/sail/scans';
import { fmtTime } from '#/utils/formatters';

defineOptions({ name: 'ScanList' });
const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'repository_name', label: '仓库', minWidth: 120 },
  { prop: 'status', label: '状态', width: 120, tag: true },
  { prop: 'progress', label: '进度', width: 100 },
  { prop: 'build_quality', label: '构建质量', width: 140 },
  { prop: 'current_stage', label: '当前阶段', width: 200 },
  { prop: 'mode', label: '模式', width: 80 },
  { prop: 'started_at', label: '开始', width: 150, formatter: (r) => fmtTime(r.started_at) },
  { prop: 'finished_at', label: '完成', width: 150, formatter: (r) => fmtTime(r.finished_at) },
  { prop: 'finding_count', label: '漏洞数', width: 80 },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '仓库', placeholder: '仓库名' },
  { type: 'select', field: 'statuses', label: '状态', multiple: true,
    options: [{label:'成功',value:'SUCCEEDED'},{label:'运行中',value:'RUNNING'},{label:'失败',value:'FAILED'},{label:'部分成功',value:'PARTIAL_SUCCEEDED'}] },
  { type: 'select', field: 'build_qualities', label: '构建质量', multiple: true,
    options: [{label:'EXTERNAL_CODEQL',value:'EXTERNAL_CODEQL'},{label:'NO_BUILD_DEGRADED',value:'NO_BUILD_DEGRADED'},{label:'SUCCESSFUL_AUTOBUILD',value:'SUCCESSFUL_AUTOBUILD'}] },
  { type: 'select', field: 'modes', label: '模式', multiple: true,
    options: [{label:'全量',value:'FULL'},{label:'增量',value:'INCREMENTAL'}] },
];

function goDetail(row: any) { router.push(`/scans/${row.id}`).catch(() => {}); }
function createScan() { router.push('/scans/create').catch(() => {}); }
</script>

<template>
  <Page description="扫描任务列表" title="扫描管理">
    <div class="p-4">
      <SailProTable :columns="columns" :fetcher="getScansApi" :filters="filters" @row-click="goDetail">
        <template #actions>
          <ElTableColumn label="操作" width="120" fixed="right">
            <template #default>
              <ElButton link type="primary" @click.stop="createScan">发起扫描</ElButton>
            </template>
          </ElTableColumn>
        </template>
      </SailProTable>
    </div>
  </Page>
</template>
```

- [ ] **Step 2: 增强 detail.vue（SSE + 日志）**

基于现有 detail.vue，在阶段时间线后加两个面板：
1. **实时进度面板**：扫描 RUNNING 时，用 `subscribeScanEventsApi(scanId, onEvent)` 订阅 SSE，收到事件刷新 scan 状态。
2. **构建日志面板**：用 `getScanLogsApi(scanId)` 轮询（每 3 秒），滚动展示。

具体代码：implementer 先 Read 现有 `scans/detail.vue`，保留现有阶段时间线，在底部加：

```vue
<!-- 实时进度（RUNNING 时显示） -->
<ElCard v-if="scan?.status === 'RUNNING'" shadow="never" class="mt-4">
  <template #header>实时进度</template>
  <ElProgress :percentage="scan.progress" :status="'warning'" />
  <p class="mt-2 text-sm">当前阶段：{{ scan.current_stage }}</p>
</ElCard>

<!-- 构建日志 -->
<ElCard shadow="never" class="mt-4">
  <template #header>构建日志</template>
  <div ref="logBox" class="h-64 overflow-auto bg-gray-900 text-gray-100 p-3 text-xs font-mono rounded">
    <div v-for="(line, i) in logs" :key="i">{{ line }}</div>
  </div>
</ElCard>
```

script 加：
```ts
import { subscribeScanEventsApi, getScanLogsApi } from '#/api/sail/scans';
const logs = ref<string[]>([]);
const logBox = ref<HTMLElement>();
let logTimer: any = null;
let es: EventSource | null = null;

async function loadLogs() {
  try {
    const data = await getScanLogsApi(Number(route.params.id), { limit: 100 });
    logs.value = (data as any)?.lines ?? [];
    await nextTick();
    if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight;
  } catch {}
}

function startSSE() {
  if (scan.value?.status !== 'RUNNING') return;
  es = subscribeScanEventsApi(Number(route.params.id), (event) => {
    if (event.status) scan.value.status = event.status;
    if (event.progress != null) scan.value.progress = event.progress;
    if (event.stage) scan.value.current_stage = event.stage;
  });
}

onMounted(async () => {
  await loadScan();
  loadLogs();
  logTimer = setInterval(loadLogs, 3000);
  startSSE();
});
onUnmounted(() => { clearInterval(logTimer); es?.close(); });
```

> 注意：import `nextTick` from 'vue'、`onUnmounted`。

- [ ] **Step 3: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -15
git add frontend/apps/web-ele/src/views/scans/
git commit -m "feat(frontend): 重写扫描列表 + 详情增强(SSE实时进度+日志轮询)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: 重写 API 资产列表 + 详情（调用链树/check矩阵/版本历史）

**Files:**
- Modify: `frontend/apps/web-ele/src/views/api-assets/list.vue`
- Modify: `frontend/apps/web-ele/src/views/api-assets/detail.vue`

**Interfaces:**
- Consumes: `SailProTable`、`getApiAssetsApi`/`getApiAssetApi`/`getCallTreeApi`/`getApiChecksApi`/`getApiAssetSecurityApi`/`getApiAssetFindingsApi`/`getApiAssetHistoryApi`、`statusTagType`/`scoreColor`

- [ ] **Step 1: 重写 list.vue**

```vue
<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getApiAssetsApi } from '#/api/sail/api-assets';
import { scoreColor } from '#/utils/status-colors';

defineOptions({ name: 'ApiAssetList' });
const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'http_method', label: 'Method', width: 80, tag: true },
  { prop: 'full_path', label: 'Path', minWidth: 180 },
  { prop: 'controller_class', label: 'Controller', width: 140 },
  { prop: 'param_count', label: '参数数', width: 70 },
  { prop: 'call_chain_depth', label: '调用链', width: 70 },
  { prop: 'finding_count', label: '漏洞数', width: 70 },
  { prop: 'overall_score', label: '安全分', width: 80, formatter: (r) => `<span class="${scoreColor(r.overall_score)}">${r.overall_score}</span>` },
  { prop: 'overall_level', label: '等级', width: 100, tag: true },
  { prop: 'status', label: '状态', width: 80, tag: true },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '路径/Controller' },
  { type: 'select', field: 'http_methods', label: 'Method', multiple: true,
    options: [{label:'GET',value:'GET'},{label:'POST',value:'POST'},{label:'PUT',value:'PUT'},{label:'DELETE',value:'DELETE'},{label:'PATCH',value:'PATCH'}] },
  { type: 'select', field: 'security_levels', label: '等级', multiple: true,
    options: [{label:'SAFE',value:'SAFE'},{label:'LOW_RISK',value:'LOW_RISK'},{label:'MEDIUM_RISK',value:'MEDIUM_RISK'},{label:'HIGH_RISK',value:'HIGH_RISK'},{label:'CRITICAL',value:'CRITICAL'}] },
  { type: 'numberRange', field: 'score', label: '安全分' },
  { type: 'numberRange', field: 'finding_count', label: '漏洞数' },
];

function goDetail(row: any) { router.push(`/api-assets/${row.id}`).catch(() => {}); }
</script>
```

> 注意：formatter 返回 HTML 字符串时需用 `v-html`，但 SailProTable 默认用 `{{ }}` 文本插值。安全分列改为不用 formatter，改用 tag:false + 普通显示，或改 SailProTable 支持 html 列。**简化：安全分列不用 formatter，直接显示数字，颜色靠行样式。** implementer 调整：安全分列 `formatter: (r) => r.overall_score`（纯数字），颜色用 `:class` 在 ElTableColumn 外层加——但 SailProTable 封装了列。**最终简化：安全分列就显示数字，不着色**（首版）。

- [ ] **Step 2: 重写 detail.vue** — 按文档 09 布局，4 个区块：

implementer 先 Read 现有 detail.vue 保留基本信息 + check 矩阵 + 安全画像部分，新增：
- 调用链树（ElTree，`getCallTreeApi`，数据空时显示"暂无调用链数据"）
- 版本历史（ElTimeline，`getApiAssetHistoryApi`）

布局：
```vue
<Page :title="`${asset?.http_method} ${asset?.full_path || asset?.path}`">
  <!-- 标题栏含安全分标签 -->
  <!-- 区块1: 左入口信息 + 右调用链树 -->
  <!-- 区块2: 左check矩阵 + 右安全控制 -->
  <!-- 区块3: 该API漏洞 SailProTable -->
  <!-- 区块4: 版本历史 ElTimeline -->
</Page>
```

- [ ] **Step 3: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -15
git add frontend/apps/web-ele/src/views/api-assets/
git commit -m "feat(frontend): 重写API资产列表+详情(调用链树/check矩阵/版本历史)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: 重写漏洞列表 + 详情（三栏+数据流可视化）

**Files:**
- Modify: `frontend/apps/web-ele/src/views/findings/list.vue`
- Modify: `frontend/apps/web-ele/src/views/findings/detail.vue`

**Interfaces:**
- Consumes: `SailProTable`、`getFindingsApi`/`getFindingApi`/`getFindingDataflowApi`/`getFindingEvidenceApi`/`getFindingInstancesApi`/`updateFindingStatusApi`、`statusTagType`/`fmtCommit`/`fmtTime`

- [ ] **Step 1: 重写 list.vue**

```vue
<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getFindingsApi } from '#/api/sail/findings';
import { fmtCommit, fmtTime } from '#/utils/formatters';

defineOptions({ name: 'FindingList' });
const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'severity', label: '严重度', width: 90, tag: true },
  { prop: 'rule_key', label: '规则', width: 130 },
  { prop: 'cwe', label: 'CWE', width: 80 },
  { prop: 'ai_verdict', label: 'AI结论', width: 130, tag: true },
  { prop: 'file_path', label: '文件', minWidth: 180, showOverflowTooltip: true },
  { prop: 'api_path', label: '所属API', width: 140 },
  { prop: 'status', label: '状态', width: 90, tag: true },
  { prop: 'first_seen_commit', label: '首次commit', width: 130, formatter: (r) => fmtCommit(r.first_seen_commit) },
  { prop: 'created_at', label: '时间', width: 150, formatter: (r) => fmtTime(r.created_at) },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '标题/文件' },
  { type: 'select', field: 'severity', label: '严重度', multiple: true,
    options: [{label:'CRITICAL',value:'CRITICAL'},{label:'HIGH',value:'HIGH'},{label:'MEDIUM',value:'MEDIUM'},{label:'LOW',value:'LOW'},{label:'INFO',value:'INFO'}] },
  { type: 'select', field: 'ai_verdicts', label: 'AI结论', multiple: true,
    options: [{label:'真阳',value:'TRUE_POSITIVE'},{label:'可能真阳',value:'LIKELY_TRUE_POSITIVE'},{label:'不确定',value:'UNCERTAIN'},{label:'可能误报',value:'LIKELY_FALSE_POSITIVE'},{label:'误报',value:'FALSE_POSITIVE'}] },
  { type: 'select', field: 'statuses', label: '状态', multiple: true,
    options: [{label:'OPEN',value:'OPEN'},{label:'FIXED',value:'FIXED'},{label:'REAPPEARED',value:'REAPPEARED'},{label:'FALSE_POSITIVE',value:'FALSE_POSITIVE'}] },
];

function goDetail(row: any) { router.push(`/findings/${row.id}`).catch(() => {}); }
</script>
```

- [ ] **Step 2: 重写 detail.vue（三栏布局）**

implementer 先 Read 现有 detail.vue。三栏用 ElRow/ElCol：

```vue
<template>
  <Page :title="finding?.title || '漏洞详情'">
    <div class="p-4 space-y-4">
      <ElRow :gutter="16">
        <!-- 左：基本信息 -->
        <ElCol :span="8">
          <ElCard shadow="never"><template #header>基本信息</template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="严重度"><ElTag :type="statusTagType(finding?.severity)">{{ finding?.severity }}</ElTag></ElDescriptionsItem>
              <ElDescriptionsItem label="规则">{{ finding?.rule_key }}</ElDescriptionsItem>
              <ElDescriptionsItem label="CWE">{{ finding?.cwe || '—' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="文件">{{ finding?.file_path }}</ElDescriptionsItem>
              <ElDescriptionsItem label="所属API">{{ finding?.api_path || '—' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="状态">
                <ElSelect v-model="finding.status" @change="updateStatus" size="small" style="width:120px">
                  <ElOption label="OPEN" value="OPEN" /><ElOption label="FIXED" value="FIXED" /><ElOption label="FALSE_POSITIVE" value="FALSE_POSITIVE" />
                </ElSelect>
              </ElDescriptionsItem>
            </ElDescriptions>
          </ElCard>
        </ElCol>
        <!-- 中：数据流 -->
        <ElCol :span="10">
          <ElCard shadow="never"><template #header>数据流 Source → Sink</template>
            <ElTimeline>
              <ElTimelineItem v-if="dataflow?.source" type="warning" :timestamp="`L${dataflow.source.line}`">
                Source: {{ dataflow.source.file }} {{ dataflow.source.symbol || '' }}
              </ElTimelineItem>
              <ElTimelineItem v-for="(node, i) in dataflow?.nodes || []" :key="i" type="primary" :timestamp="`L${node.line}`">
                {{ node.desc || node.file }}
              </ElTimelineItem>
              <ElTimelineItem v-if="dataflow?.sink" type="danger" :timestamp="`L${dataflow.sink.line}`">
                Sink: {{ dataflow.sink.symbol || dataflow.sink.file }}
              </ElTimelineItem>
            </ElTimeline>
            <ElEmpty v-if="!dataflow?.nodes?.length" description="无数据流数据" />
          </ElCard>
        </ElCol>
        <!-- 右：AI 分析 -->
        <ElCol :span="6">
          <ElCard shadow="never"><template #header>AI 分析</template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="判定"><ElTag :type="statusTagType(evidence?.verdict)">{{ evidence?.verdict || '—' }}</ElTag></ElDescriptionsItem>
              <ElDescriptionsItem label="置信度">{{ evidence?.confidence ?? '—' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="修复建议">{{ finding?.remediation || '—' }}</ElDescriptionsItem>
            </ElDescriptions>
          </ElCard>
        </ElCol>
      </ElRow>
      <!-- 底：历史实例 -->
      <ElCard shadow="never"><template #header>历史实例</template>
        <SailProTable :columns="instanceColumns" :fetcher="loadInstances" :filters="[]" />
      </ElCard>
    </div>
  </Page>
</template>
```

script 调 `getFindingApi` + `getFindingDataflowApi` + `getFindingEvidenceApi` + `getFindingInstancesApi`，`updateStatus` 调 `updateFindingStatusApi`。

- [ ] **Step 3: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -15
git add frontend/apps/web-ele/src/views/findings/
git commit -m "feat(frontend): 重写漏洞列表+详情(三栏布局+数据流可视化+AI分析)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: 新增 check 矩阵页面

**Files:**
- Create: `frontend/apps/web-ele/src/views/check-matrix/index.vue`
- Create: `frontend/apps/web-ele/src/api/sail/check-matrix.ts`
- Modify: `frontend/apps/web-ele/src/router/routes/modules/sail.ts`

**Interfaces:**
- Consumes: `GET /api/check-matrix?scan_run_id=X`

- [ ] **Step 1: 写 API 封装**

```ts
// frontend/apps/web-ele/src/api/sail/check-matrix.ts
import { requestClient } from '#/api/request';

export interface CheckMatrixData {
  apis: { id: number; name: string }[];
  checks: { key: string; name: string; category: string }[];
  cells: Record<number, Record<string, string>>;
}

export async function getCheckMatrixApi(scanRunId: number) {
  return requestClient.get<CheckMatrixData>('/check-matrix', { params: { scan_run_id: scanRunId } });
}
```

- [ ] **Step 2: 写页面**

```vue
<!-- frontend/apps/web-ele/src/views/check-matrix/index.vue -->
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { Page } from '@vben/common-ui';
import { ElCard, ElTable, ElTableColumn, ElSelect, ElOption, ElTag } from 'element-plus';
import { getCheckMatrixApi } from '#/api/sail/check-matrix';
import { getScansApi } from '#/api/sail/scans';
import { statusTagType } from '#/utils/status-colors';
import type { CheckMatrixData } from '#/api/sail/check-matrix';

defineOptions({ name: 'CheckMatrix' });
const matrix = ref<CheckMatrixData | null>(null);
const scans = ref<any[]>([]);
const scanRunId = ref<number>(0);
const loading = ref(false);

async function loadScans() {
  const data = await getScansApi({ page: 1, page_size: 50 });
  scans.value = (data as any)?.items ?? [];
  if (scans.value.length && !scanRunId.value) scanRunId.value = scans.value[0].id;
}

async function loadMatrix() {
  if (!scanRunId.value) return;
  loading.value = true;
  try { matrix.value = await getCheckMatrixApi(scanRunId.value) as any; }
  finally { loading.value = false; }
}

onMounted(async () => { await loadScans(); await loadMatrix(); });
</script>

<template>
  <Page description="API × 检查项 矩阵" title="check 矩阵">
    <div class="p-4">
      <ElCard shadow="never" class="mb-4">
        <ElSelect v-model="scanRunId" placeholder="选择扫描" style="width:300px" @change="loadMatrix">
          <ElOption v-for="s in scans" :key="s.id" :label="`#${s.id} ${s.repository_name} (${s.status})`" :value="s.id" />
        </ElSelect>
      </ElCard>
      <ElCard v-loading="loading" shadow="never">
        <ElTable v-if="matrix" :data="matrix.apis" stripe border height="600">
          <ElTableColumn prop="name" label="API" fixed width="200" />
          <ElTableColumn v-for="chk in matrix.checks" :key="chk.key" :label="chk.name" :prop="`check_${chk.key}`" width="100" align="center">
            <template #default="{ row }">
              <ElTag v-if="matrix.cells[row.id]?.[chk.key]" :type="statusTagType(matrix.cells[row.id][chk.key])" size="small">
                {{ matrix.cells[row.id][chk.key] }}
              </ElTag>
              <span v-else class="text-gray-300">—</span>
            </template>
          </ElTableColumn>
        </ElTable>
      </ElCard>
    </div>
  </Page>
</template>
```

- [ ] **Step 3: 加路由**

在 `sail.ts` 加：
```ts
  {
    meta: { icon: 'mdi:grid', order: 500, title: 'check 矩阵' },
    name: 'CheckMatrix',
    path: '/check-matrix',
    component: () => import('#/views/check-matrix/index.vue'),
  },
```

- [ ] **Step 4: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -15
git add frontend/apps/web-ele/src/views/check-matrix/ frontend/apps/web-ele/src/api/sail/check-matrix.ts frontend/apps/web-ele/src/router/routes/modules/sail.ts
git commit -m "feat(frontend): check 矩阵全局视图页

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: 新增报告页 + 重写概览大盘

**Files:**
- Modify: `frontend/apps/web-ele/src/views/dashboard/analytics/index.vue`
- Create: `frontend/apps/web-ele/src/views/reports/index.vue`
- Modify: `frontend/apps/web-ele/src/router/routes/modules/sail.ts`

**Interfaces:**
- Consumes: `getScanStatsApi`/`getScanApi`/`getFindingsApi`/`getScanApiDiffApi`

- [ ] **Step 1: 重写 dashboard**

6 统计卡片（ElStatistic）+ 最近扫描（SailProTable 精简）+ 高危漏洞 Top10（SailProTable）。
数据：`getScanStatsApi()` + `getFindingsApi({severity:'HIGH,CRITICAL', page_size:10})`。

```vue
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElCard, ElStatistic, ElRow, ElCol } from 'element-plus';
import { getScanStatsApi } from '#/api/sail/scans';
import { getFindingsApi } from '#/api/sail/findings';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn } from '#/components/sail-pro-table/types';
import { fmtTime } from '#/utils/formatters';

defineOptions({ name: 'DashboardAnalytics' });
const router = useRouter();
const stats = ref<any>({});
const topFindings = ref<any[]>([]);

const scanColumns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'repository_name', label: '仓库', width: 120 },
  { prop: 'status', label: '状态', width: 110, tag: true },
  { prop: 'progress', label: '进度', width: 70 },
  { prop: 'build_quality', label: '构建', width: 130 },
  { prop: 'started_at', label: '开始', width: 140, formatter: (r) => fmtTime(r.started_at) },
];
const findingColumns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'severity', label: '严重度', width: 80, tag: true },
  { prop: 'file_path', label: '文件', minWidth: 160 },
];

onMounted(async () => {
  stats.value = await getScanStatsApi() as any;
  const fdata = await getFindingsApi({ severity: 'HIGH,CRITICAL', page: 1, page_size: 10 } as any);
  topFindings.value = (fdata as any)?.items ?? [];
});
</script>

<template>
  <Page description="SAIL 扫描平台概览" title="概览大盘">
    <div class="p-4 space-y-4">
      <ElRow :gutter="16">
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="扫描总数" :value="stats.total_scans" /></ElCard></ElCol>
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="运行中" :value="stats.running_scans" /></ElCard></ElCol>
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="漏洞总数" :value="stats.total_findings" /></ElCard></ElCol>
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="高危" :value="stats.high_risk_findings" /></ElCard></ElCol>
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="仓库数" :value="stats.total_repositories" /></ElCard></ElCol>
        <ElCol :span="4"><ElCard shadow="never"><ElStatistic title="API资产" :value="stats.total_api_assets" /></ElCard></ElCol>
      </ElRow>
      <ElCard shadow="never"><template #header>最近扫描</template>
        <SailProTable :columns="scanColumns" :fetcher="async (p) => ({ items: stats.recent_scans || [], total: stats.recent_scans?.length || 0 })" :filters="[]" @row-click="(r) => router.push(`/scans/${r.id}`)" />
      </ElCard>
      <ElCard shadow="never"><template #header>高危漏洞 Top10</template>
        <SailProTable :columns="findingColumns" :fetcher="async () => ({ items: topFindings, total: topFindings.length })" :filters="[]" @row-click="(r) => router.push(`/findings/${r.id}`)" />
      </ElCard>
    </div>
  </Page>
</template>
```

- [ ] **Step 2: 写报告页**

```vue
<!-- frontend/apps/web-ele/src/views/reports/index.vue -->
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { Page } from '@vben/common-ui';
import { ElCard, ElSelect, ElOption, ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus';
import { getScanApi, getScanStatsApi, getScansApi } from '#/api/sail/scans';
import { fmtTime } from '#/utils/formatters';
import { statusTagType } from '#/utils/status-colors';

defineOptions({ name: 'Reports' });
const scans = ref<any[]>([]);
const scanId = ref<number>(0);
const scan = ref<any>(null);
const stats = ref<any>({});

async function load() {
  if (!scanId.value) return;
  scan.value = await getScanApi(scanId.value) as any;
  stats.value = await getScanStatsApi() as any;
}
onMounted(async () => {
  const data = await getScansApi({ page: 1, page_size: 50 });
  scans.value = (data as any)?.items ?? [];
  if (scans.value.length) { scanId.value = scans.value[0].id; await load(); }
});
</script>

<template>
  <Page description="扫描报告摘要" title="报告">
    <div class="p-4 space-y-4">
      <ElCard shadow="never">
        <ElSelect v-model="scanId" style="width:300px" @change="load">
          <ElOption v-for="s in scans" :key="s.id" :label="`#${s.id} ${s.repository_name}`" :value="s.id" />
        </ElSelect>
      </ElCard>
      <ElCard v-if="scan" shadow="never">
        <template #header>扫描报告 #{{ scan.scan?.id }}</template>
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="仓库">{{ scan.scan?.repository_name || '—' }}</ElDescriptionsItem>
          <ElDescriptionsItem label="状态"><ElTag :type="statusTagType(scan.scan?.status)">{{ scan.scan?.status }}</ElTag></ElDescriptionsItem>
          <ElDescriptionsItem label="构建质量">{{ scan.scan?.build_quality }}</ElDescriptionsItem>
          <ElDescriptionsItem label="开始时间">{{ fmtTime(scan.scan?.started_at) }}</ElDescriptionsItem>
          <ElDescriptionsItem label="阶段数">{{ scan.stages?.length }}</ElDescriptionsItem>
          <ElDescriptionsItem label="漏洞数">{{ stats.total_findings }}</ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>
  </Page>
</template>
```

- [ ] **Step 3: 加报告路由**

```ts
  {
    meta: { icon: 'mdi:file-chart', order: 600, title: '报告' },
    name: 'Reports',
    path: '/reports',
    component: () => import('#/views/reports/index.vue'),
  },
```

- [ ] **Step 4: 验证 + 提交**

```bash
cd /home/lhj/code/lhj/sail
# 需把 check-matrix 和 reports 加入 verify_frontend.py 的 PAGES 列表
sed -i 's|("漏洞清单", "/findings"),|("漏洞清单", "/findings"),\n    ("check矩阵", "/check-matrix"),\n    ("报告", "/reports"),|' scripts/verify_frontend.py
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -20
git add frontend/apps/web-ele/src/views/dashboard/ frontend/apps/web-ele/src/views/reports/ frontend/apps/web-ele/src/router/routes/modules/sail.ts scripts/verify_frontend.py
git commit -m "feat(frontend): 重写概览大盘 + 新增报告页

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 11: 最终验证 + 推送

- [ ] **Step 1: 全量 Playwright 验证**

```bash
cd /home/lhj/code/lhj/sail
.venv/bin/python scripts/verify_frontend.py 2>&1 | tail -25
```
Expected: 所有页面 `有数据: True`，0 JS 报错。

- [ ] **Step 2: 推送**

```bash
cd /home/lhj/code/lhj/sail
git push origin main
```
