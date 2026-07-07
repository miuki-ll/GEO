<template>
  <div class="progress-chain">
    <div
      v-for="(step, idx) in steps"
      :key="step.key"
      class="step"
      :class="{
        done: Number(idx) < Number(active),
        active: Number(idx) === Number(active),
        disabled: Number(idx) > Number(active) && !clickable,
      }"
      @click="onClick(Number(idx))"
    >
      <div class="step-circle">
        <el-icon v-if="Number(idx) < Number(active)"><Check /></el-icon>
        <span v-else>{{ Number(idx) + 1 }}</span>
      </div>
      <div class="step-meta">
        <div class="step-title">{{ step.title }}</div>
        <div v-if="step.desc" class="step-desc">{{ step.desc }}</div>
      </div>
      <div v-if="Number(idx) < steps.length - 1" class="connector" :class="{ filled: Number(idx) < Number(active) }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check } from '@element-plus/icons-vue'

export interface ChainStep {
  key: string
  title: string
  desc?: string
}

defineProps<{
  steps: ChainStep[]
  active: number
  clickable?: boolean
}>()

const emit = defineEmits<{ (e: 'change', idx: number): void }>()

function onClick(idx: number) {
  emit('change', idx)
}
</script>

<style lang="scss" scoped>
.progress-chain {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 16px 8px;
  overflow-x: auto;
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1 1 0;
  min-width: 120px;
  cursor: pointer;
  user-select: none;
  .step-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 15px;
    background: #f0f2f5;
    color: #909399;
    border: 2px solid #dcdfe6;
    transition: all 0.25s ease;
    z-index: 1;
  }
  &.active .step-circle {
    background: #409eff;
    color: #fff;
    border-color: #409eff;
    box-shadow: 0 0 0 6px rgba(64, 158, 255, 0.12);
  }
  &.done .step-circle {
    background: #67c23a;
    color: #fff;
    border-color: #67c23a;
  }
  &.disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }
  .step-meta {
    text-align: center;
    margin-top: 10px;
    padding: 0 6px;
  }
  .step-title {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }
  &.disabled .step-title,
  &:not(.active):not(.done) .step-title {
    color: #909399;
  }
  .step-desc {
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
  }
  .connector {
    position: absolute;
    top: 21px;
    left: calc(50% + 22px);
    right: calc(-50% + 22px);
    height: 2px;
    background: #e4e7ed;
  }
  .connector.filled {
    background: #67c23a;
  }
}
</style>
