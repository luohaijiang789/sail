<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElRadio,
  ElRadioGroup,
  ElSelect,
  ElSwitch,
} from 'element-plus';

import { getRepositoriesApi } from '#/api/sail/repositories';
import { createScanApi } from '#/api/sail/scans';

import type { ScanCreatePayload } from '#/types/sail';

defineOptions({ name: 'ScanCreate' });

const route = useRoute();
const router = useRouter();

const repositories = ref<any[]>([]);

const scanProfiles = ref([
  { id: 1, name: '标准扫描（含 CodeQL + AI）' },
  { id: 2, name: '快速扫描（无 AI）' },
  { id: 3, name: '深度扫描（含调用链富化）' },
]);

const form = reactive<ScanCreatePayload>({
  repositoryId: Number(route.query.repositoryId) || 0,
  revision: {
    type: 'branch',
    value: 'main',
  },
  scanProfileId: 1,
  aiAnalysis: true,
});

const submitting = ref(false);

async function loadRepositories() {
  try {
    const data = await getRepositoriesApi({ page: 1, pageSize: 50 });
    repositories.value = (data as any)?.items ?? [];
    // 若从仓库列表跳来带了 repositoryId，选中它；否则默认第一个
    if (form.repositoryId === 0 && repositories.value.length > 0) {
      form.repositoryId = repositories.value[0].id;
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '加载仓库失败');
  }
}

onMounted(() => {
  loadRepositories();
});

async function submit() {
  if (!form.repositoryId) {
    ElMessage.warning('请选择仓库');
    return;
  }
  if (!form.revision.value) {
    ElMessage.warning('请填写分支/Tag/Commit');
    return;
  }
  submitting.value = true;
  try {
    const scan = await createScanApi(form);
    ElMessage.success('扫描已创建，开始执行');
    router.push(`/scans/${(scan as any)?.id ?? ''}`).catch(() => {});
  } catch (error: any) {
    ElMessage.error(error?.message || '创建扫描失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <Page description="选择仓库与版本，发起一次扫描" title="创建扫描">
    <div class="p-4">
      <ElCard shadow="never" class="max-w-3xl">
        <ElForm :model="form" label-width="120px">
          <ElFormItem label="仓库" required>
            <ElSelect
              v-model="form.repositoryId"
              placeholder="选择仓库"
              style="width: 320px"
            >
              <ElOption
                v-for="r in repositories"
                :key="r.id"
                :label="r.name"
                :value="r.id"
              />
            </ElSelect>
          </ElFormItem>

          <ElFormItem label="版本类型" required>
            <ElRadioGroup v-model="form.revision.type">
              <ElRadio value="branch">分支</ElRadio>
              <ElRadio value="tag">Tag</ElRadio>
              <ElRadio value="commit">Commit</ElRadio>
            </ElRadioGroup>
          </ElFormItem>

          <ElFormItem
            :label="
              form.revision.type === 'branch'
                ? '分支'
                : form.revision.type === 'tag'
                  ? 'Tag'
                  : 'Commit SHA'
            "
            required
          >
            <ElInput
              v-model="form.revision.value"
              :placeholder="`请输入${
                form.revision.type === 'branch'
                  ? '分支名'
                  : form.revision.type === 'tag'
                    ? 'Tag 名'
                    : '完整 Commit SHA'
              }`"
              style="width: 320px"
            />
          </ElFormItem>

          <ElFormItem label="扫描方案" required>
            <ElSelect
              v-model="form.scanProfileId"
              placeholder="选择扫描方案"
              style="width: 360px"
            >
              <ElOption
                v-for="p in scanProfiles"
                :key="p.id"
                :label="p.name"
                :value="p.id"
              />
            </ElSelect>
          </ElFormItem>

          <ElFormItem label="AI 分析">
            <ElSwitch v-model="form.aiAnalysis" />
            <span class="ml-2 text-xs text-gray-400">
              开启后对 CodeQL 候选做漏斗式验证，剔除误报
            </span>
          </ElFormItem>

          <ElFormItem>
            <ElButton type="primary" :loading="submitting" @click="submit">
              创建扫描
            </ElButton>
            <ElButton @click="router.back()">取消</ElButton>
          </ElFormItem>
        </ElForm>
      </ElCard>
    </div>
  </Page>
</template>
