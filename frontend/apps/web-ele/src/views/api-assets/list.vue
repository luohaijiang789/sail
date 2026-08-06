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

import type { ApiAsset } from '#/types/sail';

defineOptions({ name: 'ApiAssetList' });

const router = useRouter();

// mock 数据
const apiAssets = ref<ApiAsset[]>([
  {
    id: 1,
    repositoryId: 1,
    sourceRevisionId: 10,
    scanRunId: 1,
    fingerprint: 'abc1',
    httpMethod: 'GET',
    path: '/users/{id}',
    fullPath: '/api/v1/users/{id}',
    framework: 'spring',
    controllerClass: 'UserController',
    handlerMethod: 'getUser',
    handlerSignature: 'getUser(Long id)',
    filePath: 'src/main/java/com/sail/UserController.java',
    startLine: 44,
    endLine: 60,
    consumes: null,
    produces: 'application/json',
    responseType: 'User',
    parameters: [],
    module: 'user',
    apiGroup: '用户中心',
    commitAuthor: 'alice',
    commitTime: '2026-08-05 18:00:00',
    callChainDepth: 3,
    enrichmentStatus: 'ENRICHED',
    firstSeenScanId: 1,
    lastSeenScanId: 1,
    status: 'ACTIVE',
    createdAt: '2026-08-06 10:30:00',
    findingCount: 1,
    securityScore: 72,
    securityLevel: 'HIGH_RISK',
    checkCoverage: 85,
  },
  {
    id: 2,
    repositoryId: 1,
    sourceRevisionId: 10,
    scanRunId: 1,
    fingerprint: 'abc2',
    httpMethod: 'POST',
    path: '/login',
    fullPath: '/api/v1/login',
    framework: 'spring',
    controllerClass: 'AuthController',
    handlerMethod: 'login',
    handlerSignature: 'login(LoginDTO dto)',
    filePath: 'src/main/java/com/sail/AuthController.java',
    startLine: 30,
    endLine: 48,
    consumes: 'application/json',
    produces: 'application/json',
    responseType: 'Token',
    parameters: [],
    module: 'auth',
    apiGroup: '认证',
    commitAuthor: 'bob',
    commitTime: '2026-08-05 17:00:00',
    callChainDepth: 2,
    enrichmentStatus: 'ENRICHED',
    firstSeenScanId: 1,
    lastSeenScanId: 1,
    status: 'ACTIVE',
    createdAt: '2026-08-06 10:30:00',
    findingCount: 0,
    securityScore: 30,
    securityLevel: 'LOW_RISK',
    checkCoverage: 100,
  },
]);

const queryForm = ref({
  keyword: '',
  httpMethod: '',
  securityLevel: '',
  hasFindings: '',
});

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const methodTagType: Record<string, TagType> = {
  GET: 'success',
  POST: 'warning',
  PUT: 'info',
  DELETE: 'danger',
  PATCH: 'info',
  HEAD: 'info',
  OPTIONS: 'info',
  CONNECT: 'info',
  TRACE: 'info',
};

const levelTagType: Record<string, TagType> = {
  SAFE: 'success',
  LOW_RISK: 'success',
  MEDIUM_RISK: 'warning',
  HIGH_RISK: 'danger',
  CRITICAL: 'danger',
};

function goDetail(row: ApiAsset) {
  router.push(`/api-assets/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="已扫描出的 HTTP 接口资产" title="API 资产">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <ElForm :inline="true" :model="queryForm">
          <ElFormItem label="关键字">
            <ElInput
              v-model="queryForm.keyword"
              placeholder="Path / Controller / Handler"
              clearable
            />
          </ElFormItem>
          <ElFormItem label="方法">
            <ElSelect
              v-model="queryForm.httpMethod"
              placeholder="全部"
              clearable
              style="width: 120px"
            >
              <ElOption label="GET" value="GET" />
              <ElOption label="POST" value="POST" />
              <ElOption label="PUT" value="PUT" />
              <ElOption label="DELETE" value="DELETE" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="安全等级">
            <ElSelect
              v-model="queryForm.securityLevel"
              placeholder="全部"
              clearable
              style="width: 140px"
            >
              <ElOption label="SAFE" value="SAFE" />
              <ElOption label="LOW_RISK" value="LOW_RISK" />
              <ElOption label="MEDIUM_RISK" value="MEDIUM_RISK" />
              <ElOption label="HIGH_RISK" value="HIGH_RISK" />
              <ElOption label="CRITICAL" value="CRITICAL" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="仅看有漏洞">
            <ElSelect
              v-model="queryForm.hasFindings"
              placeholder="全部"
              clearable
              style="width: 100px"
            >
              <ElOption label="是" value="true" />
              <ElOption label="否" value="false" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem>
            <ElButton type="primary">查询</ElButton>
          </ElFormItem>
        </ElForm>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>API 资产列表</template>
        <ElTable
          v-if="apiAssets.length > 0"
          :data="apiAssets"
          stripe
          @row-click="goDetail"
        >
          <ElTableColumn label="方法" width="80">
            <template #default="{ row }">
              <ElTag size="small" :type="methodTagType[row.httpMethod]">
                {{ row.httpMethod }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="Path" prop="path" min-width="180" />
          <ElTableColumn
            label="Controller"
            prop="controllerClass"
            width="180"
          />
          <ElTableColumn
            label="Handler"
            prop="handlerMethod"
            width="140"
          />
          <ElTableColumn label="调用链深度" prop="callChainDepth" width="100">
            <template #default="{ row }">
              {{ row.callChainDepth ?? '-' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="漏洞数" prop="findingCount" width="90">
            <template #default="{ row }">
              <span :class="row.findingCount > 0 ? 'text-red-500' : ''">
                {{ row.findingCount }}
              </span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="安全分" width="90">
            <template #default="{ row }">
              {{ row.securityScore ?? '-' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="安全等级" width="120">
            <template #default="{ row }">
              <ElTag
                v-if="row.securityLevel"
                size="small"
                :type="levelTagType[row.securityLevel]"
              >
                {{ row.securityLevel }}
              </ElTag>
              <span v-else>-</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="覆盖率" width="90">
            <template #default="{ row }">
              {{ row.checkCoverage != null ? `${row.checkCoverage}%` : '-' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" prop="status" width="100">
            <template #default="{ row }">
              <ElTag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else description="暂无 API 资产" />
      </ElCard>
    </div>
  </Page>
</template>
