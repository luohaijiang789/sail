<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getRepositoriesApi } from '#/api/sail/repositories';

defineOptions({ name: 'RepositoryList' });

const router = useRouter();

// 后端返回 snake_case 字段，直接用 any 避免类型摩擦
const repositories = ref<any[]>([]);
const loading = ref(false);

const queryForm = ref({
  keyword: '',
  repositoryType: '',
  lastScanStatus: '',
});

async function loadRepositories() {
  loading.value = true;
  try {
    const data = await getRepositoriesApi({
      page: 1,
      pageSize: 50,
    });
    // 后端返回 { items, total }（经 response wrapper 后 data 即该对象）
    repositories.value = (data as any)?.items ?? [];
  } catch (error: any) {
    ElMessage.error(error?.message || '加载仓库列表失败');
    repositories.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadRepositories();
});

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const statusTagType: Record<string, TagType> = {
  ACTIVE: 'success',
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED: 'danger',
  PARTIAL_SUCCEEDED: 'info',
  CANCELLED: 'info',
  CREATED: 'info',
  QUEUED: 'info',
};

function createScan(row: any) {
  router.push(`/scans/create?repositoryId=${row.id}`).catch(() => {});
}

function viewRepository(row: any) {
  router.push(`/repositories/${row.id}`).catch(() => {});
}

function refresh() {
  loadRepositories();
}
</script>

<template>
  <Page description="管理受扫描的代码仓库" title="仓库管理">
    <div class="p-4">
      <!-- 筛选 -->
      <ElCard shadow="never" class="mb-4">
        <ElForm :inline="true" :model="queryForm">
          <ElFormItem label="关键字">
            <ElInput
              v-model="queryForm.keyword"
              placeholder="仓库名 / Git URL"
              clearable
            />
          </ElFormItem>
          <ElFormItem label="仓库类型">
            <ElSelect
              v-model="queryForm.repositoryType"
              placeholder="全部"
              clearable
              style="width: 160px"
            >
              <ElOption label="Java Spring" value="java-spring" />
              <ElOption label="JAX-RS" value="java-jaxrs" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="最近扫描状态">
            <ElSelect
              v-model="queryForm.lastScanStatus"
              placeholder="全部"
              clearable
              style="width: 160px"
            >
              <ElOption label="成功" value="SUCCEEDED" />
              <ElOption label="进行中" value="RUNNING" />
              <ElOption label="失败" value="FAILED" />
              <ElOption label="部分成功" value="PARTIAL_SUCCEEDED" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem>
            <ElButton type="primary" @click="refresh">查询</ElButton>
          </ElFormItem>
        </ElForm>
      </ElCard>

      <!-- 列表 -->
      <ElCard shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>仓库列表</span>
            <ElButton type="primary">新增仓库</ElButton>
          </div>
        </template>
        <ElTable
          v-if="repositories.length > 0"
          v-loading="loading"
          :data="repositories"
          stripe
          @row-click="viewRepository"
        >
          <ElTableColumn label="ID" prop="id" width="60" />
          <ElTableColumn label="仓库名" prop="name" min-width="140" />
          <ElTableColumn label="Git URL" prop="git_url" min-width="260" show-overflow-tooltip />
          <ElTableColumn label="默认分支" prop="default_branch" width="110" />
          <ElTableColumn label="类型" prop="repository_type" width="110" />
          <ElTableColumn
            label="最近 commit"
            prop="last_scanned_commit"
            width="140"
          >
            <template #default="{ row }">
              {{ row.last_scanned_commit ? row.last_scanned_commit.slice(0, 12) : '—' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" width="110">
            <template #default="{ row }">
              <ElTag :type="statusTagType[row.status] || 'info'">
                {{ row.status || '—' }}
              </ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <ElButton link type="primary" @click.stop="createScan(row)">
                发起扫描
              </ElButton>
            </template>
          </ElTableColumn>
        </ElTable>
        <ElEmpty v-else description="暂无仓库" />
      </ElCard>
    </div>
  </Page>
</template>
