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
  ElRow,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTree,
} from 'element-plus';

import SailProTable from '#/components/sail-pro-table/index.vue';
import type { SailColumn } from '#/components/sail-pro-table/types';
import {
  getApiAssetApi,
  getApiAssetFindingsApi,
  getApiAssetHistoryApi,
  getApiAssetSecurityApi,
  getApiChecksApi,
  getCallTreeApi,
} from '#/api/sail/api-assets';
import { statusTagType } from '#/utils/status-colors';
import { fmtCommit, fmtTime } from '#/utils/formatters';

defineOptions({ name: 'ApiAssetDetail' });

const route = useRoute();
const assetId = computed(() => Number(route.params.id));

const asset = ref<any>(null);
const callEdges = ref<any[]>([]);
const checks = ref<any[]>([]);
const security = ref<{ profile: any | null; controls: any[] }>({
  profile: null,
  controls: [],
});
const history = ref<any[]>([]);
const loading = ref(false);

async function fetchDetail() {
  loading.value = true;
  try {
    const [a, tree, c, s, h] = await Promise.all([
      getApiAssetApi(assetId.value),
      getCallTreeApi(assetId.value),
      getApiChecksApi(assetId.value),
      getApiAssetSecurityApi(assetId.value),
      getApiAssetHistoryApi(assetId.value),
    ]);
    asset.value = a;
    callEdges.value = (tree as any[]) ?? [];
    checks.value = (c as any[]) ?? [];
    security.value = s ?? { profile: null, controls: [] };
    history.value = (h as any[]) ?? [];
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDetail);

const profile = computed(() => security.value.profile);

const scoreDimensions = computed(() => {
  const p = profile.value;
  if (!p) return [];
  return [
    { label: '暴露面', value: p.exposure_score },
    { label: '调用链', value: p.callchain_score },
    { label: '数据敏感度', value: p.data_sensitivity_score },
    { label: '代码质量', value: p.codequality_score },
  ];
});

const parametersText = computed(() => {
  const pj = asset.value?.parameters_json;
  if (!pj) return '-';
  if (typeof pj === 'string') return pj;
  try {
    return JSON.stringify(pj, null, 2);
  } catch {
    return '-';
  }
});

// ponytail: CallEdgeOut 无 parent_edge_id，按 depth 用栈重建树。
// stack[d] = 当前 depth d-1 的节点；边按 depth,id 升序保证拓扑序。
interface TreeNode {
  label: string;
  file?: string | null;
  line?: number | null;
  kind?: string;
  children?: TreeNode[];
}
const callTreeData = computed<TreeNode[]>(() => {
  const edges = callEdges.value;
  if (!edges?.length) return [];
  const root: TreeNode = {
    label: asset.value?.handler_method || edges[0].caller || 'ENTRY',
    kind: 'ENTRY',
    children: [],
  };
  const stack: TreeNode[] = [root];
  for (const e of edges) {
    const d = e.depth ?? 0;
    const node: TreeNode = {
      label: e.callee || '?',
      file: e.file,
      line: e.line,
      kind: e.edge_kind,
      children: [],
    };
    while (stack.length > d + 1) stack.pop();
    const parent = stack[stack.length - 1] || root;
    parent.children!.push(node);
    stack.push(node);
  }
  return [root];
});

// findings: 后端返回 list（非 PageResult），包一层给 SailProTable。
async function findingsFetcher(_params: Record<string, any>) {
  const items = (await getApiAssetFindingsApi(assetId.value)) ?? [];
  return { items, total: items.length };
}

const findingColumns: SailColumn[] = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'title', label: '标题', minWidth: 160 },
  { prop: 'severity', label: '严重度', width: 90, tag: true },
  { prop: 'status', label: '状态', width: 90, tag: true },
  { prop: 'rule_key', label: '规则', width: 120, showOverflowTooltip: true },
  { prop: 'cwe', label: 'CWE', width: 90 },
  { prop: 'ai_verdict', label: 'AI', width: 120, tag: true },
];

const changeTagType: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  NEW: 'primary',
  CHANGED: 'warning',
  REMOVED: 'danger',
  UNCHANGED: 'info',
  ACTIVE: 'success',
};
</script>

<template>
  <Page
    description="API 资产详情"
    :title="asset ? `${asset.http_method} ${asset.full_path || asset.path}` : '加载中…'"
  >
    <div v-loading="loading" class="p-4">
      <template v-if="asset">
        <!-- 区块0: 标题栏 + 安全分标签 -->
        <ElCard shadow="never" class="mb-4">
          <div class="flex flex-wrap items-center gap-2">
            <ElTag size="small">{{ asset.http_method }}</ElTag>
            <span class="font-mono">{{ asset.full_path || asset.path }}</span>
            <span class="text-gray-400">
              {{ asset.controller_class }}.{{ asset.handler_method }}
            </span>
            <ElTag
              v-if="profile && profile.overall_level"
              :type="statusTagType(profile.overall_level)"
            >
              安全分 {{ profile.overall_score }} · {{ profile.overall_level }}
            </ElTag>
            <ElTag v-else-if="asset.overall_score != null" type="info">
              安全分 {{ asset.overall_score }}
            </ElTag>
          </div>
        </ElCard>

        <!-- 区块1: 左入口信息 + 右调用链树 -->
        <ElRow :gutter="16">
          <ElCol :span="12">
            <ElCard shadow="never" class="mb-4">
              <template #header>基本信息</template>
              <ElDescriptions :column="1" border>
                <ElDescriptionsItem label="Method">
                  {{ asset.http_method }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="Path">
                  {{ asset.full_path || asset.path }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="Controller">
                  {{ asset.controller_class }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="Handler">
                  {{ asset.handler_signature || asset.handler_method }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="文件位置">
                  {{ asset.file_path }}<span v-if="asset.start_line">:{{ asset.start_line }}<span v-if="asset.end_line">-{{ asset.end_line }}</span></span>
                </ElDescriptionsItem>
                <ElDescriptionsItem label="参数">
                  <pre class="m-0 text-xs whitespace-pre-wrap">{{ parametersText }}</pre>
                </ElDescriptionsItem>
                <ElDescriptionsItem label="返回类型">
                  {{ asset.response_type || '-' }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="Module">
                  {{ asset.module || '-' }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="API Group">
                  {{ asset.api_group || '-' }}
                </ElDescriptionsItem>
                <ElDescriptionsItem label="Commit">
                  {{ asset.commit_author || '-' }}
                  <span v-if="asset.commit_time" class="text-gray-400">
                    · {{ fmtTime(asset.commit_time) }}
                  </span>
                </ElDescriptionsItem>
              </ElDescriptions>
            </ElCard>
          </ElCol>

          <ElCol :span="12">
            <ElCard shadow="never" class="mb-4">
              <template #header>调用链树</template>
              <ElTree
                v-if="callTreeData.length"
                :data="callTreeData"
                :props="{ label: 'label', children: 'children' }"
                default-expand-all
                :expand-on-click-node="true"
              >
                <template #default="{ data }">
                  <span class="flex items-center gap-2">
                    <span class="font-mono">{{ data.label }}</span>
                    <ElTag
                      v-if="data.kind && data.kind !== 'ENTRY' && data.kind !== 'DIRECT_CALL'"
                      size="small"
                      type="info"
                    >
                      {{ data.kind }}
                    </ElTag>
                    <span v-if="data.file" class="text-xs text-gray-400">
                      {{ data.file }}<span v-if="data.line">:{{ data.line }}</span>
                    </span>
                  </span>
                </template>
              </ElTree>
              <ElEmpty v-else description="暂无调用链数据" />
            </ElCard>
          </ElCol>
        </ElRow>

        <!-- 区块2: 左check矩阵 + 右安全画像/控制 -->
        <ElRow :gutter="16">
          <ElCol :span="12">
            <ElCard shadow="never" class="mb-4">
              <template #header>check 矩阵</template>
              <ElTable :data="checks" stripe size="small">
                <ElTableColumn label="检查项" prop="check_item_name" />
                <ElTableColumn label="结果" width="120">
                  <template #default="{ row }">
                    <ElTag size="small" :type="statusTagType(row.result)">
                      {{ row.result }}
                    </ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="证据" prop="evidence_summary" show-overflow-tooltip />
                <template #empty>
                  <ElEmpty description="无 check 数据" />
                </template>
              </ElTable>
            </ElCard>
          </ElCol>

          <ElCol :span="12">
            <ElCard shadow="never" class="mb-4">
              <template #header>安全画像</template>
              <template v-if="profile">
                <ElDescriptions :column="2" border>
                  <ElDescriptionsItem label="总分">
                    {{ profile.overall_score }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="级别">
                    <ElTag
                      v-if="profile.overall_level"
                      size="small"
                      :type="statusTagType(profile.overall_level)"
                    >
                      {{ profile.overall_level }}
                    </ElTag>
                  </ElDescriptionsItem>
                  <ElDescriptionsItem
                    v-for="d in scoreDimensions"
                    :key="d.label"
                    :label="d.label"
                  >
                    {{ d.value }}
                  </ElDescriptionsItem>
                  <ElDescriptionsItem label="覆盖率">
                    {{ profile.check_coverage }}%
                  </ElDescriptionsItem>
                </ElDescriptions>
                <div class="mt-3">
                  <div class="mb-1 text-xs text-gray-500">盲区</div>
                  <div v-if="profile.blind_spots?.length" class="flex flex-wrap gap-1">
                    <ElTag
                      v-for="b in profile.blind_spots"
                      :key="b"
                      size="small"
                      type="warning"
                    >
                      {{ b }}
                    </ElTag>
                  </div>
                  <span v-else class="text-gray-400">无</span>
                </div>
              </template>
              <ElEmpty v-else description="无安全画像" />
            </ElCard>

            <ElCard shadow="never">
              <template #header>安全控制</template>
              <ElTable
                v-if="security.controls?.length"
                :data="security.controls"
                stripe
                size="small"
              >
                <ElTableColumn label="类型" prop="control_type" width="120" />
                <ElTableColumn label="方法" prop="control_method" />
                <ElTableColumn label="作用域" prop="scope" width="90" />
                <ElTableColumn label="生效" width="70">
                  <template #default="{ row }">
                    <ElTag size="small" :type="row.enforced ? 'success' : 'danger'">
                      {{ row.enforced ? '是' : '否' }}
                    </ElTag>
                  </template>
                </ElTableColumn>
              </ElTable>
              <ElEmpty v-else description="无安全控制" />
            </ElCard>
          </ElCol>
        </ElRow>

        <!-- 区块3: 该API漏洞 -->
        <ElCard shadow="never" class="mb-4">
          <template #header>该 API 漏洞</template>
          <SailProTable :columns="findingColumns" :fetcher="findingsFetcher" />
        </ElCard>

        <!-- 区块4: 版本历史 -->
        <ElCard shadow="never">
          <template #header>版本历史</template>
          <ElTimeline v-if="history.length">
            <ElTimelineItem
              v-for="(h, i) in history"
              :key="i"
              :timestamp="fmtTime(h.commit_time || h.commitTime)"
              :type="changeTagType[h.change_type || h.changeType] || 'info'"
            >
              <div class="flex items-center gap-2">
                <ElTag size="small" :type="statusTagType(h.overall_level || h.securityLevel)">
                  {{ h.overall_level || h.securityLevel || '—' }}
                </ElTag>
                <span>安全分 {{ h.overall_score ?? h.securityScore ?? '—' }}</span>
                <span class="font-mono text-xs text-gray-500">
                  {{ fmtCommit(h.commit_sha || h.commitSha) }}
                </span>
                <ElTag size="small" type="info">
                  {{ h.change_type || h.changeType || '—' }}
                </ElTag>
              </div>
            </ElTimelineItem>
          </ElTimeline>
          <ElEmpty v-else description="暂无版本历史" />
        </ElCard>
      </template>
      <ElEmpty v-else-if="!loading" description="未找到资产" />
    </div>
  </Page>
</template>
