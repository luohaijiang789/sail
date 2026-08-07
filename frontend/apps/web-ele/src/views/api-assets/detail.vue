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
} from 'element-plus';

import {
  getApiAssetApi,
  getApiAssetSecurityApi,
  getApiChecksApi,
} from '#/api/sail/api-assets';

defineOptions({ name: 'ApiAssetDetail' });

const route = useRoute();
const assetId = computed(() => Number(route.params.id));

const asset = ref<any>(null);
const checks = ref<any[]>([]);
const security = ref<{ profile: any | null; controls: any[] }>({
  profile: null,
  controls: [],
});
const loading = ref(false);

async function fetchDetail() {
  loading.value = true;
  try {
    const [a, c, s] = await Promise.all([
      getApiAssetApi(assetId.value),
      getApiChecksApi(assetId.value),
      getApiAssetSecurityApi(assetId.value),
    ]);
    asset.value = a;
    checks.value = (c as any[]) ?? [];
    security.value = s ?? { profile: null, controls: [] };
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDetail);

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const checkResultTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  PASS: 'success',
  NOT_CHECKED: 'info',
};

const levelTagType: Record<string, TagType> = {
  SAFE: 'success',
  LOW_RISK: 'success',
  MEDIUM_RISK: 'warning',
  HIGH_RISK: 'danger',
  CRITICAL: 'danger',
};

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
</script>

<template>
  <Page
    description="API 资产详情"
    :title="asset ? `${asset.http_method} ${asset.path}` : '加载中…'"
  >
    <div v-loading="loading" class="p-4">
      <template v-if="asset">
        <!-- 头部摘要 -->
        <ElCard shadow="never" class="mb-4">
          <template #header>
            <div class="flex flex-wrap items-center gap-2">
              <ElTag size="small">{{ asset.http_method }}</ElTag>
              <span class="font-mono">{{ asset.full_path || asset.path }}</span>
              <span class="text-gray-400">
                {{ asset.controller_class }}.{{ asset.handler_method }}
              </span>
              <ElTag
                v-if="profile && profile.overall_level"
                :type="levelTagType[profile.overall_level] ?? 'info'"
              >
                安全分 {{ profile.overall_score }} ·
                {{ profile.overall_level }}
              </ElTag>
            </div>
          </template>
        </ElCard>

        <ElRow :gutter="16">
          <!-- 左：基本信息 -->
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
                    · {{ asset.commit_time }}
                  </span>
                </ElDescriptionsItem>
              </ElDescriptions>
            </ElCard>
          </ElCol>

          <!-- 右：check 矩阵 + 安全画像 -->
          <ElCol :span="12">
            <ElCard shadow="never" class="mb-4">
              <template #header>check 矩阵</template>
              <ElTable :data="checks" stripe size="small">
                <ElTableColumn label="检查项" prop="check_item_name" />
                <ElTableColumn label="结果" width="120">
                  <template #default="{ row }">
                    <ElTag size="small" :type="checkResultTagType[row.result]">
                      {{ row.result }}
                    </ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="证据" prop="evidence_summary" />
                <template #empty>
                  <ElEmpty description="无 check 数据" />
                </template>
              </ElTable>
            </ElCard>

            <ElCard shadow="never">
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
                      :type="levelTagType[profile.overall_level] ?? 'info'"
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
          </ElCol>
        </ElRow>
      </template>
      <ElEmpty v-else-if="!loading" description="未找到资产" />
    </div>
  </Page>
</template>
