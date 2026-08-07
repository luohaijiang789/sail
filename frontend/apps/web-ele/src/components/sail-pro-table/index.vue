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
