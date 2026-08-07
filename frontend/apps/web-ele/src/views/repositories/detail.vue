<!-- frontend/apps/web-ele/src/views/repositories/detail.vue -->
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElCard, ElDescriptions, ElDescriptionsItem, ElButton, ElTag } from 'element-plus';
import { getRepositoryApi } from '#/api/sail/repositories';
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
