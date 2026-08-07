<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getApiAssetsApi } from '#/api/sail/api-assets';

defineOptions({ name: 'ApiAssetList' });

const router = useRouter();

// ponytail: 安全分列首版只显示数字，不着色（SailProTable formatter 返回文本非 HTML）。
// overall_level/full_path/call_chain_depth 由后端 ApiAssetListOut 提供。
const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'http_method', label: 'Method', width: 80, tag: true },
  { prop: 'full_path', label: 'Path', minWidth: 180 },
  { prop: 'controller_class', label: 'Controller', width: 140, showOverflowTooltip: true },
  { prop: 'param_count', label: '参数数', width: 70 },
  { prop: 'call_chain_depth', label: '调用链', width: 70 },
  { prop: 'finding_count', label: '漏洞数', width: 70 },
  { prop: 'overall_score', label: '安全分', width: 80 },
  { prop: 'overall_level', label: '等级', width: 110, tag: true },
  { prop: 'status', label: '状态', width: 90, tag: true },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '路径/Controller' },
  {
    type: 'select',
    field: 'http_methods',
    label: 'Method',
    multiple: true,
    options: [
      { label: 'GET', value: 'GET' },
      { label: 'POST', value: 'POST' },
      { label: 'PUT', value: 'PUT' },
      { label: 'DELETE', value: 'DELETE' },
      { label: 'PATCH', value: 'PATCH' },
    ],
  },
  {
    type: 'select',
    field: 'security_levels',
    label: '等级',
    multiple: true,
    options: [
      { label: 'SAFE', value: 'SAFE' },
      { label: 'LOW_RISK', value: 'LOW_RISK' },
      { label: 'MEDIUM_RISK', value: 'MEDIUM_RISK' },
      { label: 'HIGH_RISK', value: 'HIGH_RISK' },
      { label: 'CRITICAL', value: 'CRITICAL' },
    ],
  },
  { type: 'numberRange', field: 'score', label: '安全分' },
  { type: 'numberRange', field: 'finding_count', label: '漏洞数' },
];

function goDetail(row: any) {
  router.push(`/api-assets/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="已扫描出的 HTTP 接口资产" title="API 资产">
    <div class="p-4">
      <SailProTable
        :columns="columns"
        :fetcher="getApiAssetsApi"
        :filters="filters"
        @row-click="goDetail"
      />
    </div>
  </Page>
</template>
