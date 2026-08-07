<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getFindingsApi } from '#/api/sail/findings';
import { fmtCommit, fmtTime } from '#/utils/formatters';

defineOptions({ name: 'FindingList' });

const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'severity', label: '严重度', width: 90, tag: true },
  { prop: 'rule_key', label: '规则', width: 130 },
  { prop: 'cwe', label: 'CWE', width: 80 },
  { prop: 'ai_verdict', label: 'AI结论', width: 130, tag: true },
  { prop: 'file_path', label: '文件', minWidth: 180, showOverflowTooltip: true },
  { prop: 'api_path', label: '所属API', width: 140 },
  { prop: 'status', label: '状态', width: 90, tag: true },
  {
    prop: 'first_seen_commit',
    label: '首次commit',
    width: 130,
    formatter: (r) => fmtCommit(r.first_seen_commit),
  },
  {
    prop: 'created_at',
    label: '时间',
    width: 150,
    formatter: (r) => fmtTime(r.created_at),
  },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '标题/文件' },
  {
    type: 'select',
    field: 'severity',
    label: '严重度',
    multiple: true,
    options: [
      { label: 'CRITICAL', value: 'CRITICAL' },
      { label: 'HIGH', value: 'HIGH' },
      { label: 'MEDIUM', value: 'MEDIUM' },
      { label: 'LOW', value: 'LOW' },
      { label: 'INFO', value: 'INFO' },
    ],
  },
  {
    type: 'select',
    field: 'ai_verdicts',
    label: 'AI结论',
    multiple: true,
    options: [
      { label: '真阳', value: 'TRUE_POSITIVE' },
      { label: '可能真阳', value: 'LIKELY_TRUE_POSITIVE' },
      { label: '不确定', value: 'UNCERTAIN' },
      { label: '可能误报', value: 'LIKELY_FALSE_POSITIVE' },
      { label: '误报', value: 'FALSE_POSITIVE' },
    ],
  },
  {
    type: 'select',
    field: 'statuses',
    label: '状态',
    multiple: true,
    options: [
      { label: 'OPEN', value: 'OPEN' },
      { label: 'FIXED', value: 'FIXED' },
      { label: 'REAPPEARED', value: 'REAPPEARED' },
      { label: 'FALSE_POSITIVE', value: 'FALSE_POSITIVE' },
    ],
  },
];

function goDetail(row: any) {
  router.push(`/findings/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="CodeQL + AI 验证后的漏洞清单" title="漏洞清单">
    <div class="p-4">
      <SailProTable
        :columns="columns"
        :fetcher="getFindingsApi"
        :filters="filters"
        @row-click="goDetail"
      />
    </div>
  </Page>
</template>
