<!-- frontend/apps/web-ele/src/components/sail-pro-table/filter-bar.vue -->
<script lang="ts" setup>
import { reactive, watch } from 'vue';
import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton } from 'element-plus';
import type { SailFilter } from './types';

const props = defineProps<{
  filters: SailFilter[];
  modelValue: Record<string, any>;
}>();
const emit = defineEmits<{ 'update:modelValue': [val: Record<string, any>]; change: [] }>();

const form = reactive<Record<string, any>>({ ...props.modelValue });

// 同步外部初始值变化
watch(() => props.modelValue, (v) => {
  Object.assign(form, v);
}, { deep: true });

let timer: any = null;
function emitChange() {
  clearTimeout(timer);
  timer = setTimeout(() => {
    emit('update:modelValue', { ...form });
    emit('change');
  }, 300);  // 防抖 300ms
}

function reset() {
  for (const f of props.filters) {
    form[f.field] = f.type === 'numberRange' ? { min: undefined, max: undefined } : (f.multiple ? [] : '');
  }
  emitChange();
}
</script>

<template>
  <ElForm :inline="true" :model="form" class="mb-4">
    <ElFormItem v-for="f in filters" :key="f.field" :label="f.label">
      <!-- 关键字 -->
      <ElInput
        v-if="f.type === 'keyword'"
        v-model="form[f.field]"
        :placeholder="f.placeholder || '搜索'"
        clearable
        style="width: 200px"
        @input="emitChange"
      />
      <!-- 多选/单选下拉 -->
      <ElSelect
        v-else-if="f.type === 'select'"
        v-model="form[f.field]"
        :multiple="f.multiple"
        :placeholder="f.placeholder || '全部'"
        clearable
        collapse-tags
        collapse-tags-tooltip
        style="width: 200px"
        @change="emitChange"
      >
        <ElOption
          v-for="opt in f.options"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </ElSelect>
      <!-- 数值范围 -->
      <template v-else-if="f.type === 'numberRange'">
        <ElInput
          v-model.number="form[f.field].min"
          placeholder="最小"
          style="width: 90px"
          @input="emitChange"
        />
        <span class="mx-1">-</span>
        <ElInput
          v-model.number="form[f.field].max"
          placeholder="最大"
          style="width: 90px"
          @input="emitChange"
        />
      </template>
    </ElFormItem>
    <ElFormItem>
      <ElButton @click="reset">重置</ElButton>
    </ElFormItem>
  </ElForm>
</template>
