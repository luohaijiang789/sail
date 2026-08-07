<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
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

import {
  getFindingApi,
  getFindingDataflowApi,
  getFindingEvidenceApi,
} from '#/api/sail/findings';

defineOptions({ name: 'FindingDetail' });

const route = useRoute();
const findingId = computed(() => Number(route.params.id));

const finding = ref<any>(null);
const dataflow = ref<any>(null);
const evidence = ref<any>(null);
const loading = ref(false);

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const severityTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
};

const verdictTagType: Record<string, TagType> = {
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

// 统一成展示用的步骤列表：source → nodes → sink
const flowSteps = computed(() => {
  const df = dataflow.value;
  if (!df) return [];
  const steps: any[] = [];
  if (df.source) {
    steps.push({
      step: 0,
      kind: 'SOURCE',
      symbol: df.source.symbol,
      file: df.source.file,
      line: df.source.line,
      desc: 'Source',
    });
  }
  for (const n of df.nodes ?? []) {
    steps.push({
      step: n.step,
      kind: 'CALL_PATH',
      symbol: '',
      file: n.file,
      line: n.line,
      desc: n.desc,
    });
  }
  if (df.sink) {
    steps.push({
      step: (df.nodes?.length ?? 0) + 1,
      kind: 'SINK',
      symbol: df.sink.symbol,
      file: df.sink.file,
      line: df.sink.line,
      desc: 'Sink',
    });
  }
  return steps;
});

const reasoning = computed(() => evidence.value?.ai_review?.reasoning ?? null);

const filePath = computed(
  () =>
    evidence.value?.candidate?.file_path ??
    dataflow.value?.source?.file ??
    '-',
);

async function load() {
  loading.value = true;
  try {
    const [f, df, ev] = await Promise.all([
      getFindingApi(findingId.value),
      getFindingDataflowApi(findingId.value),
      getFindingEvidenceApi(findingId.value),
    ]);
    finding.value = f;
    dataflow.value = df;
    evidence.value = ev;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <Page description="漏洞详情" :title="finding?.title ?? '加载中...'">
    <div v-loading="loading" class="p-4">
      <!-- 基本信息 -->
      <ElCard v-if="finding" shadow="never" class="mb-4">
        <template #header>基本信息</template>
        <ElDescriptions :column="3" border>
          <ElDescriptionsItem label="严重度">
            <ElTag :type="severityTagType[finding.severity]">
              {{ finding.severity }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag>{{ finding.status }}</ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="规则 ID">
            {{ finding.rule_id }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="文件">
            {{ filePath }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="首次提交">
            {{ finding.first_seen_commit }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="最近提交">
            {{ finding.last_seen_commit }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="发现时间">
            {{ finding.created_at }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="描述" :span="2">
            {{ finding.description || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="修复建议" :span="3">
            {{ finding.remediation || '暂无修复建议' }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 数据流 + AI Review -->
      <div class="md:flex">
        <!-- 数据流可视化 -->
        <ElCard shadow="never" class="mb-4 md:mr-4 md:w-1/2">
          <template #header>数据流 Source → CallPath → Sink</template>
          <ElTimeline v-if="flowSteps.length > 0">
            <ElTimelineItem
              v-for="node in flowSteps"
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
                <ElTag size="small" :type="stepTagType[node.kind] ?? 'info'">
                  {{ node.kind }}
                </ElTag>
                <span v-if="node.symbol" class="font-mono text-xs">
                  {{ node.symbol }}
                </span>
              </div>
              <div class="mt-1 text-xs text-gray-500">
                {{ node.file }}:{{ node.line }}
              </div>
              <div v-if="node.desc" class="mt-1 text-xs text-gray-600">
                {{ node.desc }}
              </div>
            </ElTimelineItem>
          </ElTimeline>
          <ElEmpty v-else description="无数据流" />
        </ElCard>

        <!-- AI Review -->
        <ElCard shadow="never" class="mb-4 md:w-1/2">
          <template #header>
            <div class="flex items-center justify-between">
              <span>AI Review</span>
              <ElTag
                v-if="evidence?.verdict"
                size="small"
                :type="verdictTagType[evidence.verdict] ?? 'info'"
              >
                {{ evidence.verdict }}
              </ElTag>
            </div>
          </template>
          <ElDescriptions :column="1" size="small" border>
            <ElDescriptionsItem label="置信度">
              {{ evidence?.confidence ?? '-' }}
            </ElDescriptionsItem>
          </ElDescriptions>

          <div class="mt-3">
            <div class="mb-1 text-xs font-medium text-gray-500">推理过程</div>
            <ElScrollbar height="240px">
              <div v-if="reasoning" class="space-y-2 text-xs">
                <div v-for="(v, k) in reasoning" :key="k">
                  <span class="text-blue-500">{{ k }}：</span>
                  {{ v }}
                </div>
              </div>
              <ElEmpty v-else description="暂无推理信息" />
            </ElScrollbar>
          </div>
        </ElCard>
      </div>
    </div>
  </Page>
</template>
