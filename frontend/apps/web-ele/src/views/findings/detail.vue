<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElScrollbar,
  ElTag,
  ElTimeline,
  ElTimelineItem,
} from 'element-plus';

import type { AiReview, DataflowNode, Finding, FindingInstance } from '#/types/sail';

defineOptions({ name: 'FindingDetail' });

const route = useRoute();
const findingId = computed(() => Number(route.params.id));

// mock 漏洞详情
const finding = ref<Finding>({
  id: findingId.value,
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
  description:
    '用户输入 id 经 UserController.getUser → UserService.findById 传递到 UserDao.queryById，在 SQL 拼接中未使用参数化查询。',
  remediation:
    '使用 PreparedStatement 或 MyBatis #{} 参数绑定，禁止字符串拼接 SQL。',
  createdAt: '2026-08-06 10:40:00',
  repositoryName: 'user-center',
  apiAssetLabel: 'GET /users/{id}',
  aiVerdict: 'LIKELY_TRUE_POSITIVE',
  aiConfidence: 0.88,
  riskScore: 82,
  instanceStatus: 'NEW',
});

// mock 数据流 Source → CallPath → Sink
const dataflow = ref<DataflowNode[]>([
  {
    step: 1,
    kind: 'SOURCE',
    symbol: 'UserController.getUser(Long id)',
    filePath: 'UserController.java',
    line: 44,
    snippet: '@GetMapping("/users/{id}")\npublic User getUser(@PathVariable Long id) {',
    description: '用户输入从 path 参数 id 进入',
  },
  {
    step: 2,
    kind: 'CALL_PATH',
    symbol: 'UserService.findById(Long id)',
    filePath: 'UserService.java',
    line: 78,
    snippet: 'public User findById(Long id) {\n  return userDao.queryById(id);\n}',
    description: 'id 原样传递到 DAO 层',
  },
  {
    step: 3,
    kind: 'SINK',
    symbol: 'UserDao.queryById(Long id)',
    filePath: 'UserDao.java',
    line: 132,
    snippet:
      'String sql = "SELECT * FROM t_user WHERE id=" + id;\nreturn jdbcTemplate.queryForList(sql);',
    description: 'id 直接拼接到 SQL 字符串，存在注入',
  },
]);

// mock AI Review（06-ai-analysis.md 结构化输出）
const aiReview = ref<AiReview>({
  id: 1,
  candidateId: 1,
  apiAssetId: 1,
  modelProvider: 'openai',
  modelName: 'gpt-4-turbo',
  promptVersion: 'v2.3',
  evidenceHash: 'h1',
  round: 0,
  verdict: 'LIKELY_TRUE_POSITIVE',
  confidence: 0.88,
  exploitability: 'HIGH',
  authRequired: true,
  authEnforced: false,
  reachableFromEndpoint: true,
  responseJson: {
    reasoning: {
      input_source: 'path 参数 id，无校验',
      path_reachability: '入口鉴权 @PreAuthorize 未生效，外网可达',
      sink_constraint: '字符串拼接 SQL，无参数化',
      dataflow_integrity: 'source→sink 完整，无 sanitizer',
    },
  },
  needRequestsJson: null,
  inputTokens: 4200,
  outputTokens: 800,
  costUsd: 0.12,
  durationSeconds: 14,
  status: 'COMPLETED',
});

// mock 历史实例
const instances = ref<FindingInstance[]>([
  {
    id: 1,
    findingId: findingId.value,
    scanRunId: 1,
    sourceRevisionId: 10,
    candidateId: 1,
    filePath: 'UserDao.java',
    startLine: 132,
    endLine: 133,
    symbol: 'UserDao.queryById',
    apiAssetId: 1,
    rawSeverity: 'HIGH',
    finalSeverity: 'HIGH',
    aiVerdict: 'LIKELY_TRUE_POSITIVE',
    aiConfidence: 0.88,
    riskScore: 82,
    status: 'NEW',
  },
]);

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const severityTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
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

const stepTagType: Record<string, TagType> = {
  SOURCE: 'warning',
  CALL_PATH: 'info',
  SINK: 'danger',
};

const reasoning = computed(
  () => aiReview.value.responseJson?.reasoning ?? {},
);
</script>

<template>
  <Page description="漏洞详情" :title="finding.title">
    <div class="p-4">
      <!-- 顶部基本信息 -->
      <ElCard shadow="never" class="mb-4">
        <template #header>基本信息</template>
        <ElDescriptions :column="3" border>
          <ElDescriptionsItem label="严重度">
            <ElTag :type="severityTagType[finding.severity]">
              {{ finding.severity }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="风险分">
            {{ finding.riskScore }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag>{{ finding.status }}</ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="规则">
            {{ finding.ruleName }} ({{ finding.ruleKey }})
          </ElDescriptionsItem>
          <ElDescriptionsItem label="CWE">
            {{ finding.cwe }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="所属 API">
            {{ finding.apiAssetLabel || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="仓库">
            {{ finding.repositoryName }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="首次发现">
            {{ finding.firstSeenCommit.slice(0, 7) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="最近发现">
            {{ finding.lastSeenCommit.slice(0, 7) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="描述" :span="3">
            {{ finding.description }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 三栏：数据流 / AI 分析 / 修复建议 -->
      <div class="md:flex">
        <!-- 左：Source → CallPath → Sink -->
        <ElCard shadow="never" class="mb-4 md:mr-4 md:w-1/3">
          <template #header>Source → CallPath → Sink</template>
          <ElTimeline v-if="dataflow.length > 0">
            <ElTimelineItem
              v-for="node in dataflow"
              :key="node.step"
              :type="
                node.kind === 'SINK'
                  ? 'danger'
                  : node.kind === 'SOURCE'
                    ? 'warning'
                    : 'primary'
              "
            >
              <div class="flex items-center gap-2">
                <ElTag size="small" :type="stepTagType[node.kind]">
                  {{ node.kind }}
                </ElTag>
                <span class="font-mono text-xs">
                  {{ node.symbol }}
                </span>
              </div>
              <div class="mt-1 text-xs text-gray-500">
                {{ node.filePath }}:{{ node.line }}
              </div>
              <pre
                v-if="node.snippet"
                class="mt-2 overflow-x-auto rounded bg-gray-50 p-2 text-xs"
                >{{ node.snippet }}</pre
              >
              <div class="mt-1 text-xs text-gray-600">
                {{ node.description }}
              </div>
            </ElTimelineItem>
          </ElTimeline>
          <ElEmpty v-else description="无数据流" />
        </ElCard>

        <!-- 中：AI 分析 -->
        <ElCard shadow="never" class="mb-4 md:mr-4 md:w-1/3">
          <template #header>
            <div class="flex items-center justify-between">
              <span>AI 分析</span>
              <ElTag
                v-if="aiReview.verdict"
                size="small"
                :type="aiVerdictTagType[aiReview.verdict]"
              >
                {{ aiReview.verdict }}
              </ElTag>
            </div>
          </template>
          <ElDescriptions :column="1" size="small" border>
            <ElDescriptionsItem label="置信度">
              {{ aiReview.confidence }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="可利用性">
              {{ aiReview.exploitability }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="需要鉴权">
              {{ aiReview.authRequired ? '是' : '否' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="鉴权生效">
              <ElTag
                size="small"
                :type="aiReview.authEnforced ? 'success' : 'danger'"
              >
                {{ aiReview.authEnforced ? '是' : '否' }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem label="入口可达">
              {{ aiReview.reachableFromEndpoint ? '是' : '否' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="模型">
              {{ aiReview.modelName }} ({{ aiReview.promptVersion }})
            </ElDescriptionsItem>
            <ElDescriptionsItem label="Token / 耗时">
              {{ aiReview.inputTokens }} + {{ aiReview.outputTokens }} ·
              {{ aiReview.durationSeconds }}s · ${{ aiReview.costUsd }}
            </ElDescriptionsItem>
          </ElDescriptions>

          <div class="mt-3">
            <div class="mb-1 text-xs font-medium text-gray-500">
              引导式提问推理
            </div>
            <ElScrollbar height="220px">
              <div class="space-y-2 text-xs">
                <div>
                  <span class="text-blue-500">输入来源：</span>
                  {{ reasoning.input_source }}
                </div>
                <div>
                  <span class="text-blue-500">路径可达性：</span>
                  {{ reasoning.path_reachability }}
                </div>
                <div>
                  <span class="text-blue-500">Sink 约束：</span>
                  {{ reasoning.sink_constraint }}
                </div>
                <div>
                  <span class="text-blue-500">数据流完整性：</span>
                  {{ reasoning.dataflow_integrity }}
                </div>
              </div>
            </ElScrollbar>
          </div>
        </ElCard>

        <!-- 右：修复建议 + 证据 -->
        <ElCard shadow="never" class="mb-4 md:w-1/3">
          <template #header>修复建议</template>
          <div class="text-sm leading-6">
            {{ finding.remediation || '暂无修复建议' }}
          </div>
          <div class="mt-4">
            <div class="mb-2 text-xs font-medium text-gray-500">证据片段</div>
            <ElScrollbar height="320px">
              <div class="space-y-3">
                <div
                  v-for="node in dataflow"
                  :key="node.step"
                  class="rounded border border-gray-200 p-2"
                >
                  <div class="mb-1 flex items-center justify-between">
                    <span class="font-mono text-xs">{{ node.symbol }}</span>
                    <span class="text-xs text-gray-400">
                      {{ node.filePath }}:{{ node.line }}
                    </span>
                  </div>
                  <pre
                    v-if="node.snippet"
                    class="overflow-x-auto rounded bg-gray-50 p-2 text-xs"
                    >{{ node.snippet }}</pre
                  >
                </div>
              </div>
            </ElScrollbar>
          </div>
        </ElCard>
      </div>

      <!-- 底部：历史实例 -->
      <ElCard shadow="never" class="mt-4">
        <template #header>历史实例</template>
        <ElTimeline v-if="instances.length > 0">
          <ElTimelineItem
            v-for="inst in instances"
            :key="inst.id"
            :timestamp="`scan #${inst.scanRunId}`"
            type="danger"
          >
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs">
                {{ inst.filePath }}:{{ inst.startLine }}-{{ inst.endLine }}
              </span>
              <ElTag size="small" :type="severityTagType[inst.finalSeverity]">
                {{ inst.finalSeverity }}
              </ElTag>
              <ElTag
                size="small"
                :type="inst.status === 'NEW' ? 'danger' : 'info'"
              >
                {{ inst.status }}
              </ElTag>
              <span class="text-xs text-gray-400">
                AI: {{ inst.aiVerdict }} ({{ inst.aiConfidence }}) · 风险
                {{ inst.riskScore }}
              </span>
            </div>
          </ElTimelineItem>
        </ElTimeline>
        <ElEmpty v-else description="无历史实例" />
      </ElCard>
    </div>
  </Page>
</template>
