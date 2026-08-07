<!-- frontend/apps/web-ele/src/views/scans/list.vue -->
<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { ElButton, ElTableColumn } from 'element-plus';

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
  {
    prop: 'started_at',
    label: '开始',
    width: 150,
    formatter: (r) => fmtTime(r.started_at),
  },
  {
    prop: 'finished_at',
    label: '完成',
    width: 150,
    formatter: (r) => fmtTime(r.finished_at),
  },
  { prop: 'finding_count', label: '漏洞数', width: 80 },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '仓库', placeholder: '仓库名' },
  {
    type: 'select',
    field: 'statuses',
    label: '状态',
    multiple: true,
    options: [
      { label: '成功', value: 'SUCCEEDED' },
      { label: '运行中', value: 'RUNNING' },
      { label: '失败', value: 'FAILED' },
      { label: '部分成功', value: 'PARTIAL_SUCCEEDED' },
    ],
  },
  {
    type: 'select',
    field: 'build_qualities',
    label: '构建质量',
    multiple: true,
    options: [
      { label: 'EXTERNAL_CODEQL', value: 'EXTERNAL_CODEQL' },
      { label: 'NO_BUILD_DEGRADED', value: 'NO_BUILD_DEGRADED' },
      { label: 'SUCCESSFUL_AUTOBUILD', value: 'SUCCESSFUL_AUTOBUILD' },
    ],
  },
  {
    type: 'select',
    field: 'modes',
    label: '模式',
    multiple: true,
    options: [
      { label: '全量', value: 'FULL' },
      { label: '增量', value: 'INCREMENTAL' },
    ],
  },
];

function goDetail(row: any) {
  router.push(`/scans/${row.id}`).catch(() => {});
}

function createScan() {
  router.push('/scans/create').catch(() => {});
}
</script>

<template>
  <Page description="扫描任务列表" title="扫描管理">
    <div class="p-4">
      <SailProTable
        :columns="columns"
        :fetcher="getScansApi"
        :filters="filters"
        @row-click="goDetail"
      >
        <template #actions>
          <ElTableColumn label="操作" width="120" fixed="right">
            <template #default>
              <ElButton link type="primary" @click.stop="createScan">
                发起扫描
              </ElButton>
            </template>
          </ElTableColumn>
        </template>
      </SailProTable>
    </div>
  </Page>
</template>
