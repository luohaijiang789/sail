<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import { ElCard, ElCol, ElRow, ElStatistic } from 'element-plus';

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
  {
    prop: 'started_at',
    label: '开始',
    width: 140,
    formatter: (r) => fmtTime(r.started_at),
  },
];
const findingColumns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'severity', label: '严重度', width: 80, tag: true },
  { prop: 'file_path', label: '文件', minWidth: 160 },
];

onMounted(async () => {
  stats.value = (await getScanStatsApi()) as any;
  const fdata = (await getFindingsApi({
    severity: 'HIGH,CRITICAL',
    page: 1,
    page_size: 10,
  } as any)) as any;
  topFindings.value = fdata?.items ?? [];
});

function goScan(row: any) {
  router.push(`/scans/${row.id}`).catch(() => {});
}
function goFinding(row: any) {
  router.push(`/findings/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="SAIL 扫描平台概览" title="概览大盘">
    <div class="p-4 space-y-4">
      <ElRow :gutter="16">
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic title="扫描总数" :value="stats.total_scans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic title="运行中" :value="stats.running_scans" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic title="漏洞总数" :value="stats.total_findings" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic
              title="高危"
              :value="stats.high_risk_findings"
              value-style="color: #f56c6c"
            />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic title="仓库数" :value="stats.total_repositories" />
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="never">
            <ElStatistic title="API资产" :value="stats.total_api_assets" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElCard shadow="never">
        <template #header>最近扫描</template>
        <SailProTable
          :columns="scanColumns"
          :fetcher="
            async () => ({
              items: stats.recent_scans || [],
              total: stats.recent_scans?.length || 0,
            })
          "
          :filters="[]"
          @row-click="goScan"
        />
      </ElCard>

      <ElCard shadow="never">
        <template #header>高危漏洞 Top10</template>
        <SailProTable
          :columns="findingColumns"
          :fetcher="async () => ({ items: topFindings, total: topFindings.length })"
          :filters="[]"
          @row-click="goFinding"
        />
      </ElCard>
    </div>
  </Page>
</template>
