<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElCol,
  ElEmpty,
  ElMessage,
  ElRow,
  ElStatistic,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getScanStatsApi } from '#/api/sail/scans';

defineOptions({ name: 'DashboardAnalytics' });

const router = useRouter();

// 后端返回 snake_case 字段，用 any 避免类型摩擦
const stats = ref<any>({
  total_scans: 0,
  running_scans: 0,
  total_findings: 0,
  high_risk_findings: 0,
  total_repositories: 0,
  total_api_assets: 0,
});
const recentScans = ref<any[]>([]);
const loading = ref(false);

async function loadStats() {
  loading.value = true;
  try {
    const data = (await getScanStatsApi()) as any;
    stats.value = data ?? stats.value;
    recentScans.value = data?.recent_scans ?? [];
  } catch (error: any) {
    ElMessage.error(error?.message || '加载概览统计失败');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadStats();
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

function goScanDetail(row: any) {
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
            <ElStatistic title="累计扫描" :value="stats.total_scans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="进行中扫描" :value="stats.running_scans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="累计漏洞" :value="stats.total_findings" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic
              title="高危漏洞"
              :value="stats.high_risk_findings"
              value-style="color: #f56c6c"
            />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="仓库数" :value="stats.total_repositories" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover">
            <ElStatistic title="API 资产" :value="stats.total_api_assets" />
          </ElCard>
        </ElCol>
      </ElRow>

      <!-- 最近扫描 -->
      <ElCard shadow="never">
        <template #header>
          <span>最近扫描</span>
        </template>
        <ElTable
          v-if="recentScans.length > 0"
          v-loading="loading"
          :data="recentScans"
          stripe
          @row-click="goScanDetail"
        >
          <ElTableColumn label="扫描 ID" prop="id" width="90" />
          <ElTableColumn label="状态" width="160">
            <template #default="{ row }">
              <ElTag :type="statusTagType[row.status] || 'info'">
                {{ row.status || '—' }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="进度" width="100">
            <template #default="{ row }">
              {{ row.progress ?? 0 }}%
            </template>
          </ElTableColumn>
          <ElTableColumn
            label="构建质量"
            prop="build_quality"
            width="120"
          />
          <ElTableColumn
            label="当前阶段"
            prop="current_stage"
            min-width="140"
          />
          <ElTableColumn label="模式" prop="mode" width="100" />
          <ElTableColumn
            label="开始时间"
            prop="started_at"
            width="180"
          />
        </ElTable>
        <ElEmpty v-else v-loading="loading" description="暂无扫描记录" />
      </ElCard>
    </div>
  </Page>
</template>
