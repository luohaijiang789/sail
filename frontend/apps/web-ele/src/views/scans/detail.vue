<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElInput,
  ElScrollbar,
  ElTag,
  ElTimeline,
  ElTimelineItem,
} from 'element-plus';

import type { ScanLogLine, ScanRun, ScanStageRun } from '#/types/sail';

defineOptions({ name: 'ScanDetail' });

const route = useRoute();
const scanId = computed(() => Number(route.params.id));

// mock 扫描详情
const scan = ref<ScanRun>({
  id: scanId.value,
  repositoryId: 1,
  repositoryName: 'user-center',
  sourceRevisionId: 10,
  scanProfileId: 1,
  status: 'RUNNING',
  aiAnalysis: true,
  startedAt: '2026-08-06 10:23:00',
  finishedAt: null,
  highRiskCount: 2,
  apiAssetCount: 124,
  findingCount: 18,
  triggeredBy: 'admin',
  errorMessage: null,
});

// mock 阶段时间线（08-orchestration.md 阶段依赖）
const stages = ref<ScanStageRun[]>([
  {
    id: 1,
    scanRunId: scanId.value,
    stageType: 'FETCH_SOURCE',
    status: 'SUCCEEDED',
    attempt: 1,
    maxAttempts: 3,
    required: true,
    onFailure: 'ABORT',
    celeryTaskId: 'c1',
    inputFingerprint: null,
    outputArtifactId: 100,
    startedAt: '2026-08-06 10:23:05',
    finishedAt: '2026-08-06 10:23:42',
    heartbeatAt: '2026-08-06 10:23:42',
    retryable: false,
    errorCode: null,
    errorMessage: null,
  },
  {
    id: 2,
    scanRunId: scanId.value,
    stageType: 'PREFLIGHT',
    status: 'SUCCEEDED',
    attempt: 1,
    maxAttempts: 3,
    required: true,
    onFailure: 'ABORT',
    celeryTaskId: 'c2',
    inputFingerprint: null,
    outputArtifactId: 101,
    startedAt: '2026-08-06 10:23:45',
    finishedAt: '2026-08-06 10:24:10',
    heartbeatAt: '2026-08-06 10:24:10',
    retryable: false,
    errorCode: null,
    errorMessage: null,
  },
  {
    id: 3,
    scanRunId: scanId.value,
    stageType: 'BUILD_CODEQL_DATABASE',
    status: 'RUNNING',
    attempt: 1,
    maxAttempts: 3,
    required: true,
    onFailure: 'DEGRADE',
    celeryTaskId: 'c3',
    inputFingerprint: null,
    outputArtifactId: null,
    startedAt: '2026-08-06 10:24:12',
    finishedAt: null,
    heartbeatAt: '2026-08-06 10:30:00',
    retryable: true,
    errorCode: null,
    errorMessage: null,
  },
  {
    id: 4,
    scanRunId: scanId.value,
    stageType: 'EXTRACT_API_FACTS',
    status: 'PENDING',
    attempt: 0,
    maxAttempts: 3,
    required: true,
    onFailure: 'ABORT',
    celeryTaskId: null,
    inputFingerprint: null,
    outputArtifactId: null,
    startedAt: null,
    finishedAt: null,
    heartbeatAt: null,
    retryable: false,
    errorCode: null,
    errorMessage: null,
  },
]);

// mock 日志
const logs = ref<ScanLogLine[]>([
  { seq: 1, timestamp: '10:23:05', level: 'INFO', stage: 'FETCH_SOURCE', message: '开始拉取源码 a1b2c3d' },
  { seq: 2, timestamp: '10:23:42', level: 'INFO', stage: 'FETCH_SOURCE', message: '源码归档完成 source_artifact_id=100' },
  { seq: 3, timestamp: '10:23:45', level: 'INFO', stage: 'PREFLIGHT', message: '预检：识别构建方案 maven' },
  { seq: 4, timestamp: '10:24:10', level: 'INFO', stage: 'PREFLIGHT', message: 'BuildPlan 生成完成' },
  { seq: 5, timestamp: '10:24:12', level: 'INFO', stage: 'BUILD_CODEQL_DATABASE', message: '开始 CodeQL 建库' },
  { seq: 6, timestamp: '10:28:00', level: 'WARN', stage: 'BUILD_CODEQL_DATABASE', message: '内存使用 9.2GB / 12GB' },
]);

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

const stageStatusTagType: Record<string, TagType> = {
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED_FINAL: 'danger',
  FAILED_RETRYABLE: 'danger',
  PENDING: 'info',
  SKIPPED: 'info',
  CANCELLED: 'info',
  TIMEOUT: 'danger',
};

const logFilter = ref('');

const filteredLogs = computed(() =>
  logs.value.filter(
    (l) =>
      !logFilter.value ||
      l.message.includes(logFilter.value) ||
      l.stage?.includes(logFilter.value),
  ),
);

const isRunning = computed(() => scan.value.status === 'RUNNING');

function cancelScan() {
  // TODO: cancelScanApi(scanId)
}

function retryScan() {
  // TODO: retryScanApi(scanId)
}

function retryStage(stage: ScanStageRun) {
  // TODO: retryStageApi(scanId, stage.id)
  void stage;
}
</script>

<template>
  <Page description="扫描执行详情" :title="`扫描 #${scanId}`">
    <div class="p-4">
      <!-- 基本信息 -->
      <ElCard shadow="never" class="mb-4">
        <template #header>
          <div class="flex items-center justify-between">
            <span>基本信息</span>
            <div>
              <ElTag :type="statusTagType[scan.status]" class="mr-2">
                {{ scan.status }}
              </ElTag>
              <ElButton
                v-if="isRunning"
                type="danger"
                size="small"
                @click="cancelScan"
              >
                取消扫描
              </ElButton>
              <ElButton
                v-if="scan.status === 'FAILED' || scan.status === 'CANCELLED'"
                type="primary"
                size="small"
                @click="retryScan"
              >
                重试扫描
              </ElButton>
            </div>
          </div>
        </template>
        <ElDescriptions :column="3" border>
          <ElDescriptionsItem label="仓库">
            {{ scan.repositoryName }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="扫描方案">
            profile #{{ scan.scanProfileId }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="AI 分析">
            <ElTag :type="scan.aiAnalysis ? 'success' : 'info'">
              {{ scan.aiAnalysis ? '已开启' : '未开启' }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="开始时间">
            {{ scan.startedAt }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="结束时间">
            {{ scan.finishedAt || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="触发人">
            {{ scan.triggeredBy }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="API 数">
            {{ scan.apiAssetCount }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="漏洞数">
            {{ scan.findingCount }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="高危数">
            <span :class="scan.highRiskCount ? 'text-red-500' : ''">
              {{ scan.highRiskCount }}
            </span>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <ElCol :span="24">
        <div class="md:flex">
          <!-- 阶段时间线 -->
          <ElCard shadow="never" class="mb-4 md:mr-4 md:w-1/2">
            <template #header>阶段时间线</template>
            <ElTimeline v-if="stages.length > 0">
              <ElTimelineItem
                v-for="stage in stages"
                :key="stage.id"
                :timestamp="stage.startedAt || '待执行'"
                :type="
                  stageStatusTagType[stage.status] === 'success'
                    ? 'success'
                    : stageStatusTagType[stage.status] === 'danger'
                      ? 'danger'
                      : stageStatusTagType[stage.status] === 'warning'
                        ? 'warning'
                        : 'primary'
                "
              >
                <div class="flex items-center justify-between">
                  <span class="font-medium">{{ stage.stageType }}</span>
                  <ElTag
                    size="small"
                    :type="stageStatusTagType[stage.status]"
                  >
                    {{ stage.status }}
                  </ElTag>
                </div>
                <div class="mt-1 text-xs text-gray-500">
                  第 {{ stage.attempt }}/{{ stage.maxAttempts }} 次 ·
                  {{ stage.required ? '必需' : '可选' }} ·
                  on_failure={{ stage.onFailure }}
                </div>
                <div v-if="stage.errorMessage" class="mt-1 text-xs text-red-500">
                  {{ stage.errorMessage }}
                </div>
                <div v-if="stage.status === 'FAILED_RETRYABLE'" class="mt-2">
                  <ElButton
                    size="small"
                    type="primary"
                    @click="retryStage(stage)"
                  >
                    重试阶段
                  </ElButton>
                </div>
              </ElTimelineItem>
            </ElTimeline>
            <ElEmpty v-else description="暂无阶段数据" />
          </ElCard>

          <!-- 实时日志 -->
          <ElCard shadow="never" class="mb-4 md:w-1/2">
            <template #header>
              <div class="flex items-center justify-between">
                <span>实时日志</span>
                <ElInput
                  v-model="logFilter"
                  size="small"
                  placeholder="过滤日志"
                  style="width: 200px"
                  clearable
                />
              </div>
            </template>
            <ElScrollbar height="420px">
              <div class="font-mono text-xs leading-6">
                <div
                  v-for="line in filteredLogs"
                  :key="line.seq"
                  class="whitespace-pre-wrap border-b border-gray-100 py-1"
                >
                  <span class="text-gray-400">{{ line.timestamp }}</span>
                  <ElTag
                    size="small"
                    class="mx-2"
                    :type="
                      line.level === 'ERROR'
                        ? 'danger'
                        : line.level === 'WARN'
                          ? 'warning'
                          : 'info'
                    "
                  >
                    {{ line.level }}
                  </ElTag>
                  <span v-if="line.stage" class="text-blue-500">
                    [{{ line.stage }}]
                  </span>
                  <span>{{ line.message }}</span>
                </div>
                <ElEmpty
                  v-if="filteredLogs.length === 0"
                  description="无日志"
                />
              </div>
            </ElScrollbar>
          </ElCard>
        </div>
      </ElCol>
    </div>
  </Page>
</template>
