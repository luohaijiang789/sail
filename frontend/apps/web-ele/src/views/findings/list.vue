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

import type { Finding } from '#/types/sail';

defineOptions({ name: 'FindingList' });

const router = useRouter();

// mock 漏洞列表
const findings = ref<Finding[]>([
  {
    id: 1,
    repositoryId: 1,
    fingerprint: 'f1',
    ruleId: 101,
    ruleName: 'SQL Injection',
    ruleKey: 'java/sql-injection',
    cwe: 'CWE-89',
    severity: 'HIGH',
    status: 'OPEN',
    firstSeenScanId: 1,
    lastSeenScanId: 1,
    firstSeenCommit: 'a1b2c3d',
    lastSeenCommit: 'a1b2c3d',
    apiAssetId: 1,
    title: 'SQL Injection in UserDao.queryById',
    description: '拼接 id 到 SQL 查询，未使用参数化查询',
    remediation: '使用 PreparedStatement 或 MyBatis 参数绑定',
    createdAt: '2026-08-06 10:40:00',
    repositoryName: 'user-center',
    apiAssetLabel: 'GET /users/{id}',
    aiVerdict: 'LIKELY_TRUE_POSITIVE',
    aiConfidence: 0.88,
    riskScore: 82,
    instanceStatus: 'NEW',
  },
  {
    id: 2,
    repositoryId: 1,
    fingerprint: 'f2',
    ruleId: 102,
    ruleName: 'Path Traversal',
    ruleKey: 'java/path-traversal',
    cwe: 'CWE-22',
    severity: 'MEDIUM',
    status: 'OPEN',
    firstSeenScanId: 1,
    lastSeenScanId: 1,
    firstSeenCommit: 'a1b2c3d',
    lastSeenCommit: 'a1b2c3d',
    apiAssetId: 2,
    title: 'Path Traversal in FileService.read',
    description: '用户输入拼接到文件路径',
    remediation: '校验并规范化路径',
    createdAt: '2026-08-06 10:40:00',
    repositoryName: 'user-center',
    apiAssetLabel: 'GET /files',
    aiVerdict: 'UNCERTAIN',
    aiConfidence: 0.5,
    riskScore: 55,
    instanceStatus: 'NEW',
  },
  {
    id: 3,
    repositoryId: 3,
    fingerprint: 'f3',
    ruleId: 103,
    ruleName: 'Hardcoded Credential',
    ruleKey: 'java/hardcoded-credential',
    cwe: 'CWE-798',
    severity: 'HIGH',
    status: 'REAPPEARED',
    firstSeenScanId: 2,
    lastSeenScanId: 4,
    firstSeenCommit: 'x1y2z3',
    lastSeenCommit: 'i7j8k9l',
    apiAssetId: null,
    title: 'Hardcoded DB password in Config.java',
    description: '配置类中硬编码数据库密码',
    remediation: '迁移到环境变量或密钥管理',
    createdAt: '2026-07-01 10:00:00',
    repositoryName: 'order-service',
    apiAssetLabel: null,
    aiVerdict: 'TRUE_POSITIVE',
    aiConfidence: 0.95,
    riskScore: 78,
    instanceStatus: 'REAPPEARED',
  },
]);

const queryForm = ref({
  keyword: '',
  severity: '',
  status: '',
  aiVerdict: '',
  cwe: '',
});

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const severityTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
};

const statusTagType: Record<string, TagType> = {
  OPEN: 'danger',
  FIXED: 'success',
  REAPPEARED: 'warning',
  FALSE_POSITIVE: 'info',
};

const aiVerdictTagType: Record<string, TagType> = {
  TRUE_POSITIVE: 'danger',
  LIKELY_TRUE_POSITIVE: 'danger',
  UNCERTAIN: 'warning',
  LIKELY_FALSE_POSITIVE: 'info',
  FALSE_POSITIVE: 'info',
  NEED_MORE_CONTEXT: 'warning',
  INSUFFICIENT_CONTEXT: 'info',
};

function goDetail(row: Finding) {
  router.push(`/findings/${row.id}`).catch(() => {});
}
</script>

<template>
  <Page description="CodeQL + AI 验证后的漏洞清单" title="漏洞清单">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <ElForm :inline="true" :model="queryForm">
          <ElFormItem label="关键字">
            <ElInput
              v-model="queryForm.keyword"
              placeholder="标题 / 文件 / 符号"
              clearable
            />
          </ElFormItem>
          <ElFormItem label="严重度">
            <ElSelect
              v-model="queryForm.severity"
              placeholder="全部"
              clearable
              style="width: 120px"
            >
              <ElOption label="CRITICAL" value="CRITICAL" />
              <ElOption label="HIGH" value="HIGH" />
              <ElOption label="MEDIUM" value="MEDIUM" />
              <ElOption label="LOW" value="LOW" />
              <ElOption label="INFO" value="INFO" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="状态">
            <ElSelect
              v-model="queryForm.status"
              placeholder="全部"
              clearable
              style="width: 140px"
            >
              <ElOption label="OPEN" value="OPEN" />
              <ElOption label="FIXED" value="FIXED" />
              <ElOption label="REAPPEARED" value="REAPPEARED" />
              <ElOption label="FALSE_POSITIVE" value="FALSE_POSITIVE" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="CWE">
            <ElInput
              v-model="queryForm.cwe"
              placeholder="CWE-89"
              clearable
              style="width: 120px"
            />
          </ElFormItem>
          <ElFormItem label="AI 结论">
            <ElSelect
              v-model="queryForm.aiVerdict"
              placeholder="全部"
              clearable
              style="width: 180px"
            >
              <ElOption label="TRUE_POSITIVE" value="TRUE_POSITIVE" />
              <ElOption
                label="LIKELY_TRUE_POSITIVE"
                value="LIKELY_TRUE_POSITIVE"
              />
              <ElOption label="UNCERTAIN" value="UNCERTAIN" />
              <ElOption
                label="LIKELY_FALSE_POSITIVE"
                value="LIKELY_FALSE_POSITIVE"
              />
              <ElOption label="FALSE_POSITIVE" value="FALSE_POSITIVE" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem>
            <ElButton type="primary">查询</ElButton>
          </ElFormItem>
        </ElForm>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>漏洞列表</template>
        <ElTable
          v-if="findings.length > 0"
          :data="findings"
          stripe
          @row-click="goDetail"
        >
          <ElTableColumn label="ID" prop="id" width="60" />
          <ElTableColumn label="标题" prop="title" min-width="220" />
          <ElTableColumn label="严重度" width="100">
            <template #default="{ row }">
              <ElTag size="small" :type="severityTagType[row.severity]">
                {{ row.severity }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="规则" prop="ruleName" width="160" />
          <ElTableColumn label="CWE" prop="cwe" width="100" />
          <ElTableColumn label="所属 API" width="160">
            <template #default="{ row }">
              {{ row.apiAssetLabel || '-' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="AI 结论" width="180">
            <template #default="{ row }">
              <ElTag
                v-if="row.aiVerdict"
                size="small"
                :type="aiVerdictTagType[row.aiVerdict]"
              >
                {{ row.aiVerdict }}
              </ElTag>
              <span v-else>-</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="风险分" prop="riskScore" width="90" />
          <ElTableColumn label="状态" width="120">
            <template #default="{ row }">
              <ElTag :type="statusTagType[row.status]">
                {{ row.status }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="实例状态" prop="instanceStatus" width="110">
            <template #default="{ row }">
              <ElTag size="small" :type="row.instanceStatus === 'NEW' ? 'danger' : 'info'">
                {{ row.instanceStatus }}
              </ElTag>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else description="暂无漏洞" />
      </ElCard>
    </div>
  </Page>
</template>
