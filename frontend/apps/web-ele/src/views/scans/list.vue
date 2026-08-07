<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElProgress,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getScansApi } from '#/api/sail/scans';

defineOptions({ name: 'ScanList' });

const router = useRouter();

const scans = ref<any[]>([]);
const loading = ref(false);

async function loadScans() {
  loading.value = true;
  try {
    const data = await getScansApi({ page: 1, pageSize: 50 });
    scans.value = (data as any)?.items ?? [];
  } catch {
    scans.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadScans();
});

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const statusTagType: Record<string, TagType> = {
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED: 'danger',
  PARTIAL_SUCCEEDED: 'info',
  CANCELLED: 'info',
  CREATED: 'info',
  QUEUED: 'info',
};

function viewDetail(row: any) {
  router.push(`/scans/${row.id}`).catch(() => {});
}

function createScan() {
  router.push('/scans/create').catch(() => {});
}

function fmtTime(t: string | null) {
  if (!t) return '—';
  return t.replace('T', ' ').slice(0, 19);
}
</script>

<template>
  <Page description="扫描任务列表" title="扫描">
    <div class="p-4">
      <ElCard shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>扫描列表</span>
            <ElButton type="primary" @click="createScan">发起扫描</ElButton>
          </div>
        </template>
        <ElTable
          v-if="scans.length > 0"
          v-loading="loading"
          :data="scans"
          stripe
          @row-click="viewDetail"
        >
          <ElTableColumn label="ID" prop="id" width="60" />
          <ElTableColumn label="状态" width="160">
            <template #default="{ row }">
              <ElTag :type="statusTagType[row.status] || 'info'">
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="进度" width="120">
            <template #default="{ row }">
              <ElProgress :percentage="row.progress" :status="row.status === 'SUCCEEDED' ? 'success' : row.status === 'FAILED' ? 'exception' : ''" />
            </template>
          </ElTableColumn>
          <ElTableColumn label="构建质量" prop="build_quality" width="160">
            <template #default="{ row }">
              {{ row.build_quality || '—' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="当前阶段" prop="current_stage" width="200">
            <template #default="{ row }">
              {{ row.current_stage || '—' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="开始时间" width="180">
            <template #default="{ row }">
              {{ fmtTime(row.started_at) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="完成时间" width="180">
            <template #default="{ row }">
              {{ fmtTime(row.finished_at) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="模式" prop="mode" width="80" />
        </ElTable>
        <ElEmpty v-else description="暂无扫描记录" />
      </ElCard>
    </div>
  </Page>
</template>
