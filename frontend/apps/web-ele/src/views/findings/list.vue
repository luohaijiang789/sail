<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getFindingsApi } from '#/api/sail/findings';

defineOptions({ name: 'FindingList' });

const router = useRouter();

const findings = ref<any[]>([]);
const loading = ref(false);
const severity = ref('');

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const severityTagType: Record<string, TagType> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
};

async function load() {
  loading.value = true;
  try {
    const res: any = await getFindingsApi({
      repository_id: 2,
      page: 1,
      page_size: 20,
      severity: severity.value || undefined,
    } as any);
    findings.value = res?.items ?? [];
  } finally {
    loading.value = false;
  }
}

function goDetail(row: any) {
  router.push(`/findings/${row.id}`).catch(() => {});
}

onMounted(load);
</script>

<template>
  <Page description="CodeQL + AI 验证后的漏洞清单" title="漏洞清单">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <ElForm :inline="true">
          <ElFormItem label="严重度">
            <ElSelect
              v-model="severity"
              placeholder="全部"
              clearable
              style="width: 140px"
              @change="load"
            >
              <ElOption label="CRITICAL" value="CRITICAL" />
              <ElOption label="HIGH" value="HIGH" />
              <ElOption label="MEDIUM" value="MEDIUM" />
              <ElOption label="LOW" value="LOW" />
              <ElOption label="INFO" value="INFO" />
            </ElSelect>
          </ElFormItem>
        </ElForm>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>漏洞列表</template>
        <ElTable
          v-loading="loading"
          :data="findings"
          stripe
          @row-click="goDetail"
        >
          <ElTableColumn label="ID" prop="id" width="70" />
          <ElTableColumn label="标题" prop="title" min-width="240" />
          <ElTableColumn label="严重度" width="110">
            <template #default="{ row }">
              <ElTag size="small" :type="severityTagType[row.severity]">
                {{ row.severity }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" prop="status" width="120" />
          <ElTableColumn label="文件" prop="file_path" min-width="200" />
          <ElTableColumn label="发现时间" prop="created_at" width="180" />
          <template #empty>
            <ElEmpty description="暂无漏洞" />
          </template>
        </ElTable>
      </ElCard>
    </div>
  </Page>
</template>
