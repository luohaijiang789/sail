<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElEmpty,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getApiAssetsApi } from '#/api/sail/api-assets';

defineOptions({ name: 'ApiAssetList' });

const router = useRouter();

const scanRunId = ref<number>(2);
const page = ref(1);
const pageSize = ref(20);

const list = ref<any[]>([]);
const total = ref(0);
const loading = ref(false);

async function fetchList() {
  loading.value = true;
  try {
    const res: any = await getApiAssetsApi({
      scan_run_id: scanRunId.value,
      page: page.value,
      page_size: pageSize.value,
    } as any);
    list.value = res?.items ?? [];
    total.value = res?.total ?? 0;
  } finally {
    loading.value = false;
  }
}

function onScanRunChange() {
  page.value = 1;
  fetchList();
}

function onPageChange(p: number) {
  page.value = p;
  fetchList();
}

function goDetail(row: any) {
  router.push(`/api-assets/${row.id}`).catch(() => {});
}

onMounted(fetchList);

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const methodTagType: Record<string, TagType> = {
  GET: 'success',
  POST: 'warning',
  PUT: 'info',
  DELETE: 'danger',
  PATCH: 'info',
  HEAD: 'info',
  OPTIONS: 'info',
};
</script>

<template>
  <Page description="已扫描出的 HTTP 接口资产" title="API 资产">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">扫描批次</span>
          <ElSelect
            v-model="scanRunId"
            style="width: 160px"
            @change="onScanRunChange"
          >
            <ElOption label="Scan Run #1" :value="1" />
            <ElOption label="Scan Run #2" :value="2" />
            <ElOption label="Scan Run #3" :value="3" />
          </ElSelect>
        </div>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>API 资产列表</template>
        <ElTable
          v-loading="loading"
          :data="list"
          stripe
          @row-click="goDetail"
        >
          <ElTableColumn label="方法" width="90">
            <template #default="{ row }">
              <ElTag size="small" :type="methodTagType[row.http_method]">
                {{ row.http_method }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="Path" prop="path" min-width="220" />
          <ElTableColumn
            label="Controller"
            prop="controller_class"
            width="200"
          />
          <ElTableColumn label="安全分" width="90">
            <template #default="{ row }">
              {{ row.overall_score ?? '-' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="漏洞数" width="90">
            <template #default="{ row }">
              <span :class="row.finding_count > 0 ? 'text-red-500' : ''">
                {{ row.finding_count ?? 0 }}
              </span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" prop="status" width="110">
            <template #default="{ row }">
              <ElTag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
          <template #empty>
            <ElEmpty description="暂无 API 资产" />
          </template>
        </ElTable>

        <div v-if="total > 0" class="mt-4 flex justify-end">
          <ElPagination
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="onPageChange"
          />
        </div>
      </ElCard>
    </div>
  </Page>
</template>
