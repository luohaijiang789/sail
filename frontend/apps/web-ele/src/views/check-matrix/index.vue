<script lang="ts" setup>
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElCard,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getCheckMatrixApi } from '#/api/sail/check-matrix';
import { getScansApi } from '#/api/sail/scans';
import { statusTagType } from '#/utils/status-colors';
import type { CheckMatrixData } from '#/api/sail/check-matrix';

defineOptions({ name: 'CheckMatrix' });

const matrix = ref<CheckMatrixData | null>(null);
const scans = ref<any[]>([]);
const scanRunId = ref<number>(0);
const loading = ref(false);

async function loadScans() {
  const data = await getScansApi({ page: 1, page_size: 50 });
  scans.value = (data as any)?.items ?? [];
  if (scans.value.length && !scanRunId.value)
    scanRunId.value = scans.value[0].id;
}

async function loadMatrix() {
  if (!scanRunId.value) return;
  loading.value = true;
  try {
    matrix.value = (await getCheckMatrixApi(scanRunId.value)) as any;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadScans();
  await loadMatrix();
});
</script>

<template>
  <Page description="API × 检查项 矩阵" title="check 矩阵">
    <div class="p-4">
      <ElCard shadow="never" class="mb-4">
        <ElSelect
          v-model="scanRunId"
          placeholder="选择扫描"
          style="width: 300px"
          @change="loadMatrix"
        >
          <ElOption
            v-for="s in scans"
            :key="s.id"
            :label="`#${s.id} ${s.repository_name} (${s.status})`"
            :value="s.id"
          />
        </ElSelect>
      </ElCard>
      <ElCard v-loading="loading" shadow="never">
        <ElTable
          v-if="matrix"
          :data="matrix.apis"
          stripe
          border
          height="600"
        >
          <ElTableColumn prop="name" label="API" fixed width="200" />
          <ElTableColumn
            v-for="chk in matrix.checks"
            :key="chk.key"
            :label="chk.name"
            :prop="`check_${chk.key}`"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <ElTag
                v-if="matrix.cells[row.id]?.[chk.key]"
                :type="statusTagType(matrix.cells[row.id][chk.key])"
                size="small"
              >
                {{ matrix.cells[row.id][chk.key] }}
              </ElTag>
              <span v-else class="text-gray-300">—</span>
            </template>
          </ElTableColumn>
        </ElTable>
      </ElCard>
    </div>
  </Page>
</template>
