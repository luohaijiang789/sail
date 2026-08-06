<script lang="ts" setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import type { Repository } from '#/types/sail';

defineOptions({ name: 'RepositoryList' });

const router = useRouter();

// mock 数据，真实场景调 getRepositoriesApi
const repositories = ref<Repository[]>([
  {
    id: 1,
    projectId: 1,
    name: 'user-center',
    gitUrl: 'git@github.com:sail/user-center.git',
    defaultBranch: 'main',
    credentialId: 1,
    repositoryType: 'java-spring',
    lastScannedCommit: 'a1b2c3d',
    lastScanStatus: 'SUCCEEDED',
    lastScanAt: '2026-08-06 10:41:00',
    apiAssetCount: 124,
    highRiskCount: 5,
    createdAt: '2026-07-01 09:00:00',
  },
  {
    id: 2,
    projectId: 1,
    name: 'payment-gateway',
    gitUrl: 'git@github.com:sail/payment-gateway.git',
    defaultBranch: 'main',
    credentialId: 1,
    repositoryType: 'java-spring',
    lastScannedCommit: 'e4f5g6h',
    lastScanStatus: 'RUNNING',
    lastScanAt: '2026-08-06 11:02:00',
    apiAssetCount: 0,
    highRiskCount: 0,
    createdAt: '2026-07-02 09:00:00',
  },
  {
    id: 3,
    projectId: 1,
    name: 'order-service',
    gitUrl: 'git@github.com:sail/order-service.git',
    defaultBranch: 'develop',
    credentialId: null,
    repositoryType: 'java-spring',
    lastScannedCommit: 'i7j8k9l',
    lastScanStatus: 'PARTIAL_SUCCEEDED',
    lastScanAt: '2026-08-05 14:52:00',
    apiAssetCount: 88,
    highRiskCount: 12,
    createdAt: '2026-07-03 09:00:00',
  },
]);

const queryForm = ref({
  keyword: '',
  repositoryType: '',
  lastScanStatus: '',
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

function createScan(row: any) {
  router.push(`/scans/create?repositoryId=${row.id}`).catch(() => {});
}

function viewRepository(row: any) {
  // 暂未做仓库详情页，跳到该仓库最近一次扫描
  router.push(`/repositories/${row.id}`).catch(() => {});
}

function refresh() {
  // TODO: 调 getRepositoriesApi(queryForm.value)
}
</script>

<template>
  <Page description="管理受扫描的代码仓库" title="仓库管理">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <ElForm :inline="true" :model="queryForm">
          <ElFormItem label="关键字">
            <ElInput
              v-model="queryForm.keyword"
              placeholder="仓库名 / Git URL"
              clearable
            />
          </ElFormItem>
          <ElFormItem label="仓库类型">
            <ElSelect
              v-model="queryForm.repositoryType"
              placeholder="全部"
              clearable
              style="width: 160px"
            >
              <ElOption label="Java Spring" value="java-spring" />
              <ElOption label="JAX-RS" value="java-jaxrs" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="最近扫描状态">
            <ElSelect
              v-model="queryForm.lastScanStatus"
              placeholder="全部"
              clearable
              style="width: 160px"
            >
              <ElOption label="成功" value="SUCCEEDED" />
              <ElOption label="进行中" value="RUNNING" />
              <ElOption label="失败" value="FAILED" />
              <ElOption label="部分成功" value="PARTIAL_SUCCEEDED" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem>
            <ElButton type="primary" @click="refresh">查询</ElButton>
          </ElFormItem>
        </ElForm>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>仓库列表</span>
            <ElButton type="primary">新增仓库</ElButton>
          </div>
        </template>
        <ElTable
          v-if="repositories.length > 0"
          :data="repositories"
          stripe
          @row-click="viewRepository"
        >
          <ElTableColumn label="ID" prop="id" width="60" />
          <ElTableColumn label="仓库名" prop="name" min-width="140" />
          <ElTableColumn label="默认分支" prop="defaultBranch" width="110" />
          <ElTableColumn label="类型" prop="repositoryType" width="130" />
          <ElTableColumn
            label="最近 commit"
            prop="lastScannedCommit"
            width="140"
          />
          <ElTableColumn label="最近扫描" width="160">
            <template #default="{ row }">
              <ElTag
                v-if="row.lastScanStatus"
                :type="statusTagType[row.lastScanStatus] || 'info'"
              >
                {{ row.lastScanStatus }}
              </ElTag>
              <span v-else class="text-gray-400">未扫描</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="API 数" prop="apiAssetCount" width="90" />
          <ElTableColumn label="高危数" prop="highRiskCount" width="90">
            <template #default="{ row }">
              <span :class="row.highRiskCount > 0 ? 'text-red-500' : ''">
                {{ row.highRiskCount }}
              </span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <ElButton link type="primary" @click.stop="createScan(row)">
                发起扫描
              </ElButton>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else description="暂无仓库" />
      </ElCard>
    </div>
  </Page>
</template>
