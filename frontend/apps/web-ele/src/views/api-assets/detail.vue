<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElRow,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTree,
} from 'element-plus';

import type {
  ApiAsset,
  ApiCheck,
  CallEdge,
  ResourceAccess,
  SecurityControl,
  SecurityProfile,
} from '#/types/sail';

defineOptions({ name: 'ApiAssetDetail' });

const route = useRoute();
const assetId = computed(() => Number(route.params.id));

// mock 资产详情
const asset = ref<ApiAsset>({
  id: assetId.value,
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
  parameters: [
    { name: 'id', type: 'Long', source: 'path', required: true, validation: ['@NotNull'] },
  ],
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
});

// mock 安全画像
const profile = ref<SecurityProfile>({
  id: 1,
  apiAssetId: assetId.value,
  scanRunId: 1,
  overallScore: 72,
  overallLevel: 'HIGH_RISK',
  exposureScore: 60,
  callchainScore: 80,
  dataSensitivityScore: 40,
  codequalityScore: 20,
  checkCoverage: 85,
  blindSpots: ['CSRF', 'RATE_LIMIT'],
  riskFactorsJson: { topRisk: 'SQL Injection' },
  aiAssessment: '从入口到 UserDao.queryById 存在 SQL 注入，鉴权缺失加剧风险',
  assessedAt: '2026-08-06 10:40:00',
});

// mock 调用链（树形）
const callEdges = ref<CallEdge[]>([
  {
    id: 1,
    apiAssetId: assetId.value,
    scanRunId: 1,
    depth: 1,
    callerSymbol: 'UserController.getUser:44',
    callerFile: 'UserController.java',
    callerLine: 44,
    calleeSymbol: 'UserService.findById:78',
    calleeFile: 'UserService.java',
    calleeLine: 78,
    calleeType: 'INTERNAL',
    edgeKind: 'DIRECT_CALL',
    parentEdgeId: null,
    pathSignature: 'UserController.getUser;UserService.findById',
  },
  {
    id: 2,
    apiAssetId: assetId.value,
    scanRunId: 1,
    depth: 2,
    callerSymbol: 'UserService.findById:78',
    callerFile: 'UserService.java',
    callerLine: 78,
    calleeSymbol: 'UserDao.queryById:132',
    calleeFile: 'UserDao.java',
    calleeLine: 132,
    calleeType: 'INTERNAL',
    edgeKind: 'DIRECT_CALL',
    parentEdgeId: 1,
    pathSignature: 'UserController.getUser;UserService.findById;UserDao.queryById',
  },
  {
    id: 3,
    apiAssetId: assetId.value,
    scanRunId: 1,
    depth: 2,
    callerSymbol: 'UserService.findById:78',
    callerFile: 'UserService.java',
    callerLine: 78,
    calleeSymbol: 'AuditService.log:145',
    calleeFile: 'AuditService.java',
    calleeLine: 145,
    calleeType: 'INTERNAL',
    edgeKind: 'DIRECT_CALL',
    parentEdgeId: 1,
    pathSignature: 'UserController.getUser;UserService.findById;AuditService.log',
  },
]);

// mock 资源访问
const resources = ref<ResourceAccess[]>([
  {
    id: 1,
    apiAssetId: assetId.value,
    callEdgeId: 2,
    scanRunId: 1,
    sourceLayer: 'L2_CALLCHAIN',
    resourceType: 'DB_TABLE',
    resourceName: 't_user',
    operation: 'READ',
    detailJson: { sql: 'SELECT * FROM t_user WHERE id=?' },
    filePath: 'UserDao.java',
    line: 132,
    isSensitive: true,
  },
]);

// mock 安全控制
const controls = ref<SecurityControl[]>([
  {
    id: 1,
    apiAssetId: assetId.value,
    scanRunId: 1,
    controlType: 'AUTHZ',
    controlMethod: '@PreAuthorize',
    controlValue: "hasRole('ADMIN')",
    scope: 'METHOD',
    filePath: 'UserController.java',
    line: 43,
    enforced: true,
  },
  {
    id: 2,
    apiAssetId: assetId.value,
    scanRunId: 1,
    controlType: 'AUTHN',
    controlMethod: 'Spring Security Filter',
    controlValue: null,
    scope: 'GLOBAL',
    filePath: null,
    line: null,
    enforced: true,
  },
  {
    id: 3,
    apiAssetId: assetId.value,
    scanRunId: 1,
    controlType: 'PARAM_VALIDATION',
    controlMethod: '@NotNull',
    controlValue: 'id',
    scope: 'PARAM',
    filePath: 'UserController.java',
    line: 44,
    enforced: true,
  },
]);

// mock check 矩阵
const checks = ref<ApiCheck[]>([
  {
    id: 1,
    apiAssetId: assetId.value,
    scanRunId: 1,
    sourceRevisionId: 10,
    checkItemKey: 'SQL_INJECTION',
    checkItemName: 'SQL 注入',
    checkCategory: '注入',
    checkSource: 'CODEQL',
    result: 'HIGH',
    findingCandidateId: 1,
    evidenceSummary: 'UserDao.queryById 拼接 SQL',
    detailJson: null,
    checkedAt: '2026-08-06 10:38:00',
  },
  {
    id: 2,
    apiAssetId: assetId.value,
    scanRunId: 1,
    sourceRevisionId: 10,
    checkItemKey: 'XSS',
    checkItemName: 'XSS',
    checkCategory: '客户端',
    checkSource: 'CODEQL',
    result: 'PASS',
    findingCandidateId: null,
    evidenceSummary: null,
    detailJson: null,
    checkedAt: '2026-08-06 10:38:00',
  },
  {
    id: 3,
    apiAssetId: assetId.value,
    scanRunId: 1,
    sourceRevisionId: 10,
    checkItemKey: 'AUTH_MISSING',
    checkItemName: '鉴权缺失',
    checkCategory: '访问控制',
    checkSource: 'API_ASSET',
    result: 'CRITICAL',
    findingCandidateId: null,
    evidenceSummary: '部分方法缺少 @PreAuthorize',
    detailJson: null,
    checkedAt: '2026-08-06 10:38:00',
  },
  {
    id: 4,
    apiAssetId: assetId.value,
    scanRunId: 1,
    sourceRevisionId: 10,
    checkItemKey: 'PARAM_VALIDATION',
    checkItemName: '参数校验缺失',
    checkCategory: '访问控制',
    checkSource: 'API_ASSET',
    result: 'MEDIUM',
    findingCandidateId: null,
    evidenceSummary: null,
    detailJson: null,
    checkedAt: '2026-08-06 10:38:00',
  },
]);

// mock 该 API 的漏洞
const assetFindings = ref([
  {
    id: 1,
    title: 'SQL Injection in UserDao.queryById',
    severity: 'HIGH',
    status: 'OPEN',
  },
]);

// mock 版本历史
const history = ref([
  {
    scanRunId: 1,
    commitSha: 'a1b2c3d',
    commitTime: '2026-08-05 18:00:00',
    securityScore: 72,
    securityLevel: 'HIGH_RISK',
    changeType: 'CHANGED',
  },
  {
    scanRunId: 2,
    commitSha: 'b2c3d4e',
    commitTime: '2026-07-20 18:00:00',
    securityScore: 45,
    securityLevel: 'LOW_RISK',
    changeType: 'CHANGED',
  },
  {
    scanRunId: 3,
    commitSha: 'c3d4e5f',
    commitTime: '2026-07-01 18:00:00',
    securityScore: 75,
    securityLevel: 'HIGH_RISK',
    changeType: 'NEW',
  },
]);

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const checkResultTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  PASS: 'success',
  NOT_CHECKED: 'info',
};

const severityTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
};

// 构建调用链树
interface CallTreeNode {
  label: string;
  children?: CallTreeNode[];
}

const callTreeData = computed<CallTreeNode[]>(() => {
  const rootEdges = callEdges.value.filter((e) => e.parentEdgeId === null);
  const buildChildren = (parentId: number): CallTreeNode[] =>
    callEdges.value
      .filter((e) => e.parentEdgeId === parentId)
      .map((e) => ({
        label: `${e.calleeSymbol} [${e.edgeKind}]`,
        children: buildChildren(e.id),
      }));
  return rootEdges.map((e) => ({
    label: `${e.callerSymbol} → ${e.calleeSymbol}`,
    children: buildChildren(e.id),
  }));
});
</script>

<template>
  <Page
    description="API 资产详情"
    :title="`${asset.httpMethod} ${asset.path}`"
  >
    <div class="p-4">
      <!-- 头部摘要 -->
      <ElCard shadow="never" class="mb-4">
        <template #header>
          <div class="flex items-center gap-2">
            <ElTag size="small">{{ asset.httpMethod }}</ElTag>
            <span class="font-mono">{{ asset.fullPath }}</span>
            <span class="text-gray-400">
              {{ asset.controllerClass }}.{{ asset.handlerMethod }}
            </span>
            <ElTag
              v-if="asset.securityLevel"
              :type="
                asset.securityLevel === 'HIGH_RISK' ||
                asset.securityLevel === 'CRITICAL'
                  ? 'danger'
                  : asset.securityLevel === 'MEDIUM_RISK'
                    ? 'warning'
                    : 'success'
              "
            >
              安全分 {{ asset.securityScore }} · {{ asset.securityLevel }}
            </ElTag>
          </div>
        </template>
      </ElCard>

      <ElRow :gutter="16">
        <!-- 左：入口信息 + 调用链 -->
        <ElCol :span="12">
          <ElCard shadow="never" class="mb-4">
            <template #header>入口信息</template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="Method">
                {{ asset.httpMethod }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="Path">
                {{ asset.fullPath }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="Controller">
                {{ asset.controllerClass }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="Handler">
                {{ asset.handlerSignature }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="文件位置">
                {{ asset.filePath }}:{{ asset.startLine }}-{{ asset.endLine }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="参数">
                <div
                  v-for="p in asset.parameters"
                  :key="p.name"
                  class="text-xs"
                >
                  {{ p.name }} ({{ p.source }}) : {{ p.type }}
                  <span v-if="p.required" class="text-red-500">*</span>
                  <span v-if="p.validation.length" class="text-gray-400">
                    [{{ p.validation.join(', ') }}]
                  </span>
                </div>
              </ElDescriptionsItem>
              <ElDescriptionsItem label="produces">
                {{ asset.produces || '-' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="返回类型">
                {{ asset.responseType || '-' }}
              </ElDescriptionsItem>
            </ElDescriptions>
          </ElCard>

          <ElCard shadow="never">
            <template #header>
              调用链（深度 {{ asset.callChainDepth ?? '-' }}）
            </template>
            <ElTree
              :data="callTreeData"
              default-expand-all
              :props="{ label: 'label' }"
            >
              <template #default="{ node }">
                <span class="font-mono text-xs">{{ node.label }}</span>
              </template>
            </ElTree>
            <ElEmpty
              v-if="callEdges.length === 0"
              description="无调用链数据（未富化）"
            />
          </ElCard>
        </ElCol>

        <!-- 右：check 矩阵 + 安全控制 + 资源访问 -->
        <ElCol :span="12">
          <ElCard shadow="never" class="mb-4">
            <template #header>
              <div class="flex items-center justify-between">
                <span>check 矩阵</span>
                <span class="text-xs text-gray-400">
                  覆盖率 {{ profile.checkCoverage }}% · 盲区
                  {{ profile.blindSpots.join(', ') || '无' }}
                </span>
              </div>
            </template>
            <ElTable :data="checks" stripe size="small">
              <ElTableColumn label="检查项" prop="checkItemName" />
              <ElTableColumn label="类别" prop="checkCategory" width="100" />
              <ElTableColumn label="来源" prop="checkSource" width="100" />
              <ElTableColumn label="结果" width="110">
                <template #default="{ row }">
                  <ElTag size="small" :type="checkResultTagType[row.result]">
                    {{ row.result }}
                  </ElTag>
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCard>

          <ElCard shadow="never" class="mb-4">
            <template #header>安全控制</template>
            <ElTable :data="controls" stripe size="small">
              <ElTableColumn label="类型" prop="controlType" width="120" />
              <ElTableColumn label="方法" prop="controlMethod" />
              <ElTableColumn label="值" prop="controlValue" />
              <ElTableColumn label="作用域" prop="scope" width="100" />
              <ElTableColumn label="生效" width="80">
                <template #default="{ row }">
                  <ElTag
                    size="small"
                    :type="row.enforced ? 'success' : 'info'"
                  >
                    {{ row.enforced ? '是' : '否' }}
                  </ElTag>
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCard>

          <ElCard shadow="never">
            <template #header>资源访问</template>
            <ElTable :data="resources" stripe size="small">
              <ElTableColumn label="类型" prop="resourceType" width="120" />
              <ElTableColumn label="资源" prop="resourceName" />
              <ElTableColumn label="操作" prop="operation" width="80" />
              <ElTableColumn label="来源层" prop="sourceLayer" width="140" />
              <ElTableColumn label="敏感" width="80">
                <template #default="{ row }">
                  <ElTag
                    v-if="row.isSensitive"
                    size="small"
                    type="danger"
                  >
                    是
                  </ElTag>
                  <span v-else>否</span>
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCard>
        </ElCol>
      </ElRow>

      <!-- 该 API 的漏洞 -->
      <ElCard shadow="never" class="mt-4">
        <template #header>
          该 API 的漏洞：{{ assetFindings.length }} 个
        </template>
        <ElTable :data="assetFindings" stripe size="small">
          <ElTableColumn label="ID" prop="id" width="60" />
          <ElTableColumn label="标题" prop="title" />
          <ElTableColumn label="严重度" width="100">
            <template #default="{ row }">
              <ElTag size="small" :type="severityTagType[row.severity]">
                {{ row.severity }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" prop="status" width="100" />
        </ElTable>
        <ElEmpty
          v-if="assetFindings.length === 0"
          description="无漏洞"
        />
      </ElCard>

      <!-- 版本历史 -->
      <ElCard shadow="never" class="mt-4">
        <template #header>版本历史</template>
        <ElTimeline>
          <ElTimelineItem
            v-for="(h, idx) in history"
            :key="idx"
            :timestamp="h.commitTime"
          >
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs">{{ h.commitSha.slice(0, 7) }}</span>
              <ElTag size="small" :type="h.changeType === 'NEW' ? 'success' : 'info'">
                {{ h.changeType }}
              </ElTag>
              <span>
                安全分 {{ h.securityScore }} · {{ h.securityLevel }}
              </span>
            </div>
          </ElTimelineItem>
        </ElTimeline>
      </ElCard>
    </div>
  </Page>
</template>
