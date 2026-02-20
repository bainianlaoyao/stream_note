<template>
  <LiquidGlass class="ui-task-glass-host" v-bind="resolvedLiquidGlassProps">
    <div :class="['ui-task-card', { 'is-completed': task.status === 'completed' }]">
      <button
        type="button"
        :class="['ui-task-check', { 'is-checked': task.status === 'completed' }]"
        :aria-label="task.status === 'completed' ? 'Mark task pending' : 'Mark task completed'"
        @click="toggleStatus"
      >
        <svg
          v-if="task.status === 'completed'"
          xmlns="http://www.w3.org/2000/svg"
          width="10"
          height="10"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </button>

      <div class="ui-task-content">
        <p :class="['ui-task-text', { 'is-completed': task.status === 'completed' }]">
          {{ task.text }}
        </p>

        <div class="ui-task-meta">
          <span v-if="task.due_date" class="ui-meta-pill">
            {{ formatDate(task.due_date) }}
          </span>
          <button
            type="button"
            class="ui-task-source"
            title="Jump to source"
            aria-label="Jump to source"
            @click="goToSource"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M7 17L17 7" />
              <path d="M8 7h9v9" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </LiquidGlass>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { LiquidGlass } from '@/lib/liquid-glass'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { taskLiquidGlassPreset } from '@/config/task-liquid-glass'
import { useTasksStore } from '@/stores/tasks'
import type { Task } from '@/types/task'

const props = withDefaults(
  defineProps<{
    task: Task
    liquidGlass?: Partial<LiquidGlassProps>
  }>(),
  {
    liquidGlass: () => ({})
  }
)

const router = useRouter()
const tasksStore = useTasksStore()

const resolvedLiquidGlassProps = computed<Partial<LiquidGlassProps>>(() => {
  const preset = taskLiquidGlassPreset
  const input = props.liquidGlass ?? {}
  const merged: Partial<LiquidGlassProps> = {
    ...preset,
    ...input,
    centered: input.centered ?? preset.centered ?? false,
    style: {
      width: '100%',
      ...(preset.style ?? {}),
      ...(input.style ?? {})
    }
  }
  return merged
})

const toggleStatus = async () => {
  await tasksStore.toggleTaskStatus(props.task.id)
}

const goToSource = () => {
  router.push({
    path: '/stream',
    query: { blockId: props.task.block_id }
  })
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
