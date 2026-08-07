<!-- frontend/apps/web-ele/src/views/repositories/list.vue -->
<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { ElButton, ElTableColumn } from 'element-plus';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFilter } from '#/components/sail-pro-table/types';
import { getRepositoriesApi } from '#/api/sail/repositories';
import { fmtCommit } from '#/utils/formatters';

defineOptions({ name: 'RepositoryList' });
const router = useRouter();

const columns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'name', label: '仓库名', minWidth: 140 },
  { prop: 'git_url', label: 'Git URL', minWidth: 260, showOverflowTooltip: true },
  { prop: 'project_name', label: '项目归属', width: 120 },
  { prop: 'repository_type', label: '类型', width: 100 },
  { prop: 'default_branch', label: '默认分支', width: 100 },
  { prop: 'last_scanned_commit', label: '最近commit', width: 130, formatter: (r) => fmtCommit(r.last_scanned_commit) },
  { prop: 'last_scan_status', label: '扫描状态', width: 120, tag: true },
  { prop: 'api_asset_count', label: 'API数', width: 80 },
  { prop: 'high_risk_count', label: '高危', width: 80 },
];

const filters: SailFilter[] = [
  { type: 'keyword', field: 'keyword', label: '关键字', placeholder: '名称/URL' },
  { type: 'select', field: 'repository_types', label: '类型', multiple: true,
    options: [{ label: 'git', value: 'git' }, { label: 'java-spring', value: 'java-spring' }] },
  { type: 'select', field: 'last_scan_statuses', label: '扫描状态', multiple: true,
    options: [{ label: '成功', value: 'SUCCEEDED' }, { label: '运行中', value: 'RUNNING' }, { label: '失败', value: 'FAILED' }] },
  { type: 'numberRange', field: 'api_count', label: 'API数' },
  { type: 'numberRange', field: 'high_risk', label: '高危数' },
];

function goDetail(row: any) { router.push(`/repositories/${row.id}`).catch(() => {}); }
function createScan(row: any) { router.push(`/scans/create?repositoryId=${row.id}`).catch(() => {}); }
</script>

<template>
  <Page description="管理受扫描的代码仓库" title="仓库管理">
    <div class="p-4">
      <SailProTable :columns="columns" :fetcher="getRepositoriesApi" :filters="filters" @row-click="goDetail">
        <template #actions>
          <ElTableColumn label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <ElButton link type="primary" @click.stop="createScan(row)">发起扫描</ElButton>
            </template>
          </ElTableColumn>
        </template>
      </SailProTable>
    </div>
  </Page>
</template>
