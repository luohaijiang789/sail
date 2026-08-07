<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElMessage,
  ElProgress,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { cancelScanApi, getScanApi, retryScanApi } from '#/api/sail/scans';

defineOptions({ name: 'ScanDetail' });

const route = useRoute();
const scanId = Number(route.params.id);

// any: 后端 snake_case，避免类型摩擦
const scan = ref<any>(null);
const stages = ref<any[]>([]);
const loading = ref(false);

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

const stageStatusTagType: Record<string, TagType> = {
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED_FINAL: 'danger',
  FAILED_RETRYABLE: 'danger',
  PENDING: 'info',
  SKIPPED: 'info',
  CANCELLED: 'info',
  TIMEOUT: 'danger',
};

const isRunning = computed(() => scan.value?.status === 'RUNNING');
const canRetry = computed(
  () =>
    scan.value?.status === 'FAILED' || scan.value?.status === 'CANCELLED',
);

function formatTime(t: null | string): string {
  return t ? t.replace('T', ' ').slice(0, 19) : '-';
}

function metricsSummary(m: any): string {
  if (!m || typeof m !== 'object') return '-';
  const entries = Object.entries(m).slice(0, 4);
  if (entries.length === 0) return '-';
  return entries.map(([k, v]) => `${k}=${v}`).join(' · ');
}

async function loadDetail() {
  loading.value = true;
  try {
    const res: any = await getScanApi(scanId);
    scan.value = res.scan;
    stages.value = res.stages ?? [];
  } catch {
    // 错误提示由 request 拦截器统一处理
  } finally {
    loading.value = false;
  }
}

async function cancelScan() {
  try {
    await cancelScanApi(scanId);
    ElMessage.success('已请求取消扫描');
    await loadDetail();
  } catch {
    // 拦截器处理
  }
}

async function retryScan() {
  try {
    await retryScanApi(scanId);
    ElMessage.success('已请求重试扫描');
    await loadDetail();
  } catch {
    // 后端可能未实现，拦截器处理错误提示
  }
}

onMounted(loadDetail);
</script>

<template>
  <Page description="扫描执行详情" :title="`扫描 #${scanId}`">
    <div class="p-4" v-loading="loading">
      <!-- 顶部：扫描状态卡片 -->
      <ElCard shadow="never" class="mb-4">
        <template #header>
          <div class="flex items-center justify-between">
            <span>扫描状态</span>
            <ElTag v-if="scan" :type="statusTagType[scan.status] ?? 'info'">
              {{ scan.status }}
            </ElTag>
          </div>
        </template>
        <template v-if="scan">
          <ElDescriptions :column="3" border>
            <ElDescriptionsItem label="当前阶段">
              {{ scan.current_stage || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="执行模式">
              {{ scan.mode }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="构建质量">
              {{ scan.build_quality || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="开始时间">
              {{ formatTime(scan.started_at) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="结束时间">
              {{ formatTime(scan.finished_at) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="扫描 ID">
              {{ scan.id }}
            </ElDescriptionsItem>
          </ElDescriptions>
          <div class="mt-4">
            <div class="mb-1 text-sm text-gray-500">进度</div>
            <ElProgress :percentage="scan.progress ?? 0" />
          </div>
        </template>
        <ElEmpty v-else description="暂无扫描数据" />
      </ElCard>

      <!-- 中部：阶段时间线 -->
      <ElCard shadow="never" class="mb-4">
        <template #header>阶段时间线</template>
        <ElTable :data="stages" stripe size="small">
          <ElTableColumn prop="stage_type" label="阶段" min-width="180" />
          <ElTableColumn label="状态" width="120">
            <template #default="{ row }">
              <ElTag
                size="small"
                :type="stageStatusTagType[row.status] ?? 'info'"
              >
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="尝试" width="80">
            <template #default="{ row }">
              {{ row.attempt }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="必需" width="80">
            <template #default="{ row }">
              <ElTag :type="row.required ? 'danger' : 'info'" size="small">
                {{ row.required ? '必需' : '可选' }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="失败策略" width="100">
            <template #default="{ row }">
              {{ row.on_failure }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="开始时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.started_at) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="结束时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.finished_at) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="指标摘要" min-width="200">
            <template #default="{ row }">
              {{ metricsSummary(row.metrics_json) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="错误" min-width="200">
            <template #default="{ row }">
              <span v-if="row.error_message" class="text-red-500">
                [{{ row.error_code || 'ERR' }}] {{ row.error_message }}
              </span>
              <span v-else>-</span>
            </template>
          </ElTableColumn>
        </ElTable>
      </ElCard>

      <!-- 底部：操作 -->
      <ElCard shadow="never">
        <template #header>操作</template>
        <ElButton
          v-if="isRunning"
          type="danger"
          @click="cancelScan"
        >
          取消扫描
        </ElButton>
        <ElButton
          v-if="canRetry"
          type="primary"
          @click="retryScan"
        >
          重试扫描
        </ElButton>
        <span v-if="!isRunning && !canRetry" class="text-gray-400">
          当前状态无可用操作
        </span>
      </ElCard>
    </div>
  </Page>
</template>
