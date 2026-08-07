<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElMessage,
  ElOption,
  ElRow,
  ElSelect,
  ElTag,
  ElTimeline,
  ElTimelineItem,
} from 'element-plus';
import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn, SailFetcher } from '#/components/sail-pro-table/types';
import {
  getFindingApi,
  getFindingDataflowApi,
  getFindingEvidenceApi,
  getFindingInstancesApi,
  updateFindingStatusApi,
} from '#/api/sail/findings';
import { statusTagType } from '#/utils/status-colors';
import { fmtCommit, fmtTime } from '#/utils/formatters';

defineOptions({ name: 'FindingDetail' });

const route = useRoute();
const findingId = computed(() => Number(route.params.id));

const finding = ref<any>(null);
const dataflow = ref<any>(null);
const evidence = ref<any>(null);
const loading = ref(false);
const statusSaving = ref(false);

// 数据流是否完全缺失（source/sink/nodes 全空）
const hasFlow = computed(() => {
  const df = dataflow.value;
  return !!(df && (df.source || df.sink || (df.nodes && df.nodes.length)));
});

const instanceColumns: SailColumn[] = [
  { prop: 'id', label: '实例ID', width: 80 },
  { prop: 'file_path', label: '文件', minWidth: 200, showOverflowTooltip: true },
  { prop: 'start_line', label: '行', width: 70 },
  { prop: 'symbol', label: '符号', minWidth: 140, showOverflowTooltip: true },
  { prop: 'final_severity', label: '严重度', width: 90, tag: true },
  { prop: 'ai_verdict', label: 'AI结论', width: 130, tag: true },
  { prop: 'ai_confidence', label: '置信度', width: 90 },
  { prop: 'risk_score', label: '风险分', width: 80 },
  { prop: 'status', label: '实例状态', width: 100, tag: true },
  {
    prop: 'created_at',
    label: '扫描时间',
    width: 150,
    formatter: (r) => fmtTime(r.created_at),
  },
];

// 实例列表后端返回 bare array，包一层给 SailProTable
const loadInstances: SailFetcher = async () => {
  const items = (await getFindingInstancesApi(findingId.value)) ?? [];
  return { items, total: items.length };
};

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

async function updateStatus() {
  if (!finding.value) return;
  statusSaving.value = true;
  try {
    await updateFindingStatusApi(findingId.value, {
      status: finding.value.status,
    });
    ElMessage.success('状态已更新');
    // 刷新 finding（重拉 join 后的展示字段）
    finding.value = await getFindingApi(findingId.value);
  } catch (e: any) {
    ElMessage.error(e?.message || '状态更新失败');
    // 回滚：重新拉取以恢复 select 绑定值
    finding.value = await getFindingApi(findingId.value);
  } finally {
    statusSaving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <Page :title="finding?.title || '漏洞详情'">
    <div v-loading="loading" class="p-4 space-y-4">
      <ElRow v-if="finding" :gutter="16">
        <!-- 左：基本信息 -->
        <ElCol :span="8">
          <ElCard shadow="never">
            <template #header>基本信息</template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="严重度">
                <ElTag :type="statusTagType(finding.severity)">
                  {{ finding.severity }}
                </ElTag>
              </ElDescriptionsItem>
              <ElDescriptionsItem label="规则">
                {{ finding.rule_key || '—' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="CWE">
                {{ finding.cwe || '—' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="文件">
                {{ finding.file_path || '—' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="所属API">
                {{ finding.api_path || '—' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="首次commit">
                {{ fmtCommit(finding.first_seen_commit) }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="状态">
                <ElSelect
                  v-model="finding.status"
                  :loading="statusSaving"
                  size="small"
                  style="width: 160px"
                  @change="updateStatus"
                >
                  <ElOption label="OPEN" value="OPEN" />
                  <ElOption label="FIXED" value="FIXED" />
                  <ElOption label="REAPPEARED" value="REAPPEARED" />
                  <ElOption label="FALSE_POSITIVE" value="FALSE_POSITIVE" />
                </ElSelect>
              </ElDescriptionsItem>
            </ElDescriptions>
          </ElCard>
        </ElCol>

        <!-- 中：数据流 -->
        <ElCol :span="10">
          <ElCard shadow="never">
            <template #header>数据流 Source → Sink</template>
            <ElTimeline v-if="hasFlow">
              <ElTimelineItem
                v-if="dataflow?.source"
                type="warning"
                :timestamp="`L${dataflow.source.line ?? '?'}`"
              >
                <div class="font-mono text-xs">
                  Source: {{ dataflow.source.file }}
                </div>
                <div
                  v-if="dataflow.source.symbol"
                  class="mt-1 text-xs text-gray-500"
                >
                  {{ dataflow.source.symbol }}
                </div>
              </ElTimelineItem>
              <ElTimelineItem
                v-for="(node, i) in dataflow?.nodes || []"
                :key="i"
                type="primary"
                :timestamp="`L${node.line ?? '?'}`"
              >
                <div class="text-xs">{{ node.desc || node.file }}</div>
                <div class="mt-1 text-xs text-gray-500">{{ node.file }}</div>
              </ElTimelineItem>
              <ElTimelineItem
                v-if="dataflow?.sink"
                type="danger"
                :timestamp="`L${dataflow.sink.line ?? '?'}`"
              >
                <div class="font-mono text-xs">
                  Sink: {{ dataflow.sink.symbol || dataflow.sink.file }}
                </div>
                <div
                  v-if="dataflow.sink.file && dataflow.sink.symbol"
                  class="mt-1 text-xs text-gray-500"
                >
                  {{ dataflow.sink.file }}
                </div>
              </ElTimelineItem>
            </ElTimeline>
            <ElEmpty v-else description="无数据流数据" />
          </ElCard>
        </ElCol>

        <!-- 右：AI 分析 -->
        <ElCol :span="6">
          <ElCard shadow="never">
            <template #header>AI 分析</template>
            <ElDescriptions :column="1" border>
              <ElDescriptionsItem label="判定">
                <ElTag :type="statusTagType(evidence?.verdict)">
                  {{ evidence?.verdict || '—' }}
                </ElTag>
              </ElDescriptionsItem>
              <ElDescriptionsItem label="置信度">
                {{ evidence?.confidence ?? '—' }}
              </ElDescriptionsItem>
              <ElDescriptionsItem label="修复建议">
                {{ finding?.remediation || '—' }}
              </ElDescriptionsItem>
            </ElDescriptions>
          </ElCard>
        </ElCol>
      </ElRow>

      <!-- 底：历史实例 -->
      <ElCard shadow="never">
        <template #header>历史实例</template>
        <SailProTable :columns="instanceColumns" :fetcher="loadInstances" />
      </ElCard>
    </div>
  </Page>
</template>
