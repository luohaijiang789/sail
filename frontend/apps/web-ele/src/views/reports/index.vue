<!-- frontend/apps/web-ele/src/views/reports/index.vue -->
<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElOption,
  ElSelect,
  ElTag,
} from 'element-plus';

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
  scan.value = (await getScanApi(scanId.value)) as any;
  stats.value = (await getScanStatsApi()) as any;
}

onMounted(async () => {
  const data = (await getScansApi({ page: 1, page_size: 50 })) as any;
  scans.value = data?.items ?? [];
  if (scans.value.length > 0) {
    scanId.value = scans.value[0].id;
    await load();
  }
});
</script>

<template>
  <Page description="扫描报告摘要" title="报告">
    <div class="p-4 space-y-4">
      <ElCard shadow="never">
        <ElSelect v-model="scanId" style="width: 300px" @change="load">
          <ElOption
            v-for="s in scans"
            :key="s.id"
            :label="`#${s.id} ${s.repository_name}`"
            :value="s.id"
          />
        </ElSelect>
      </ElCard>

      <ElCard v-if="scan" shadow="never">
        <template #header>扫描报告 #{{ scan.scan?.id }}</template>
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="仓库">{{
            scan.scan?.repository_name || '—'
          }}</ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag :type="statusTagType(scan.scan?.status)">{{
              scan.scan?.status
            }}</ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="构建质量">{{
            scan.scan?.build_quality || '—'
          }}</ElDescriptionsItem>
          <ElDescriptionsItem label="开始时间">{{
            fmtTime(scan.scan?.started_at)
          }}</ElDescriptionsItem>
          <ElDescriptionsItem label="阶段数">{{
            scan.stages?.length ?? 0
          }}</ElDescriptionsItem>
          <ElDescriptionsItem label="漏洞数">{{
            stats.total_findings ?? 0
          }}</ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>
  </Page>
</template>
