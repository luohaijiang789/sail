<script lang="ts" setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElCol,
  ElEmpty,
  ElRow,
  ElStatistic,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import type { ScanRun } from '#/types/sail';

defineOptions({ name: 'SailOverview' });

const router = useRouter();

// 概览统计卡片（mock 数据，真实场景由 /api/scans/stats 提供）
const stats = ref({
  totalScans: 128,
  runningScans: 3,
  totalFindings: 487,
  highRiskFindings: 26,
  totalRepositories: 12,
  totalApiAssets: 1456,
});

// 最近扫描（mock 数据）
const recentScans = ref<ScanRun[]>([
  {
    id: 1,
    repositoryId: 1,
    repositoryName: 'user-center',
    sourceRevisionId: 10,
    scanProfileId: 1,
    aiAnalysis: true,
    status: 'SUCCEEDED',
    startedAt: '2026-08-06 10:23:00',
    finishedAt: '2026-08-06 10:41:00',
    highRiskCount: 5,
    apiAssetCount: 124,
  },
  {
    id: 2,
    repositoryId: 2,
    repositoryName: 'payment-gateway',
    sourceRevisionId: 11,
    scanProfileId: 1,
    aiAnalysis: true,
    status: 'RUNNING',
    startedAt: '2026-08-06 11:02:00',
    finishedAt: null,
    highRiskCount: 0,
    apiAssetCount: 0,
  },
  {
    id: 3,
    repositoryId: 1,
    repositoryName: 'user-center',
    sourceRevisionId: 9,
    scanProfileId: 1,
    aiAnalysis: false,
    status: 'FAILED',
    startedAt: '2026-08-05 18:30:00',
    finishedAt: '2026-08-05 18:45:00',
    highRiskCount: 0,
    apiAssetCount: 0,
  },
  {
    id: 4,
    repositoryId: 3,
    repositoryName: 'order-service',
    sourceRevisionId: 12,
    scanProfileId: 2,
    aiAnalysis: true,
    status: 'PARTIAL_SUCCEEDED',
    startedAt: '2026-08-05 14:10:00',
    finishedAt: '2026-08-05 14:52:00',
    highRiskCount: 12,
    apiAssetCount: 88,
  },
]);

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

function goScanDetail(row: ScanRun) {
  router.push(`/scans/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="SAIL 扫描平台概览" title="概览">
    <div class="p-4">
      <!-- 统计卡片 -->
      <ElRow :gutter="16" class="mb-4">
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="累计扫描" :value="stats.totalScans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="进行中扫描" :value="stats.runningScans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="累计漏洞" :value="stats.totalFindings" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic
              title="高危漏洞"
              :value="stats.highRiskFindings"
              value-style="color: #f56c6c"
            />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="仓库数" :value="stats.totalRepositories" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="API 资产" :value="stats.totalApiAssets" />
          </ElCard>
        </ElCol>
      </ElRow>

      <!-- 最近扫描 -->
      <ElCard shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>最近扫描</span>
          </div>
        </template>
        <ElTable
          v-if="recentScans.length > 0"
          :data="recentScans"
          stripe
          @row-click="goScanDetail"
        >
          <ElTableColumn label="扫描 ID" prop="id" width="80" />
          <ElTableColumn label="仓库" prop="repositoryName" />
          <ElTableColumn label="状态" width="180">
            <template #default="{ row }">
              <ElTag :type="statusTagType[row.status] || 'info'">
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="开始时间" prop="startedAt" width="180" />
          <ElTableColumn label="结束时间" prop="finishedAt" width="180" />
          <ElTableColumn label="API 数" prop="apiAssetCount" width="100" />
          <ElTableColumn label="高危数" prop="highRiskCount" width="100">
            <template #default="{ row }">
              <span :class="row.highRiskCount > 0 ? 'text-red-500' : ''">
                {{ row.highRiskCount }}
              </span>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else description="暂无扫描记录" />
      </ElCard>
    </div>
  </Page>
</template>
