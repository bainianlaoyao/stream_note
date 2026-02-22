<template>
  <SharedLiquidGlass :liquid-glass="props.liquidGlass" @click="handleCardClick">
    <div :class="['ui-task-card', { 'is-completed': task.status === 'completed' }]">
      <div class="ui-task-content">
        <div v-if="taskContext.before" class="ui-task-context ui-task-context-before">
          {{ taskContext.before }}
        </div>
        <p :class="['ui-task-text', { 'is-completed': task.status === 'completed' }]">
          {{ task.text }}
        </p>
        <div v-if="taskContext.after" class="ui-task-context ui-task-context-after">
          {{ taskContext.after }}
        </div>

        <div class="ui-task-meta">
          <span v-if="task.due_date" class="ui-meta-pill">
            {{ formatDate(task.due_date) }}
          </span>
          <div class="ui-task-actions">
            <button
              type="button"
              class="ui-task-source"
              :title="t('taskJumpToSource')"
              :aria-label="t('taskJumpToSource')"
              :disabled="isDeleting || isDeleteConfirming"
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

            <button
              v-if="!isDeleteConfirming"
              type="button"
              class="ui-task-delete"
              :title="t('taskDeleteTask')"
              :aria-label="t('taskDeleteTask')"
              :disabled="isDeleting"
              @click="requestDeleteConfirm"
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
                <polyline points="3 6 5 6 21 6" />
                <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>

            <div v-else class="ui-task-delete-inline">
              <button
                type="button"
                class="ui-btn ui-btn-ghost ui-btn-pill ui-task-delete-cancel"
                :disabled="isDeleting"
                @click="cancelDeleteConfirm"
              >
                {{ t('taskCancel') }}
              </button>
              <button
                type="button"
                class="ui-btn ui-btn-pill ui-task-delete-confirm-btn"
                :disabled="isDeleting"
                @click="confirmDelete"
              >
                {{ isDeleting ? t('taskDeleting') : t('taskDelete') }}
              </button>
            </div>
          </div>
          <p v-if="deleteErrorMessage" class="ui-body ui-body-sm ui-task-delete-error">
            {{ deleteErrorMessage }}
          </p>
        </div>
      </div>
    </div>
  </SharedLiquidGlass>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import SharedLiquidGlass from '@/components/glass/SharedLiquidGlass.vue'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { useTasksStore } from '@/stores/tasks'
import { useDocumentStore } from '@/stores/document'
import type { Task } from '@/types/task'
import { useI18n } from '@/composables/useI18n'
import { getTaskContext } from '@/lib/document-utils'

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
const documentStore = useDocumentStore()
const { t, getDateTimeLocale } = useI18n()
const isDeleting = ref(false)
const isDeleteConfirming = ref(false)
const deleteErrorMessage = ref<string | null>(null)

const taskContext = computed(() => {
  return getTaskContext(documentStore.content, props.task.text)
})

const handleCardClick = (event: MouseEvent) => {
  // Ignore clicks on interactive elements like buttons
  const target = event.target as HTMLElement
  if (target.closest('button, a, input, select, textarea, [role="button"]')) {
    return
  }
  toggleStatus()
}

const toggleStatus = async () => {
  if (isDeleting.value) {
    return
  }
  await tasksStore.toggleTaskStatus(props.task.id)
}

const goToSource = () => {
  if (isDeleteConfirming.value || isDeleting.value) {
    return
  }
  router.push({
    path: '/stream',
    query: { blockId: props.task.block_id, text: props.task.text }
  })
}

const requestDeleteConfirm = () => {
  if (isDeleting.value) {
    return
  }
  deleteErrorMessage.value = null
  isDeleteConfirming.value = true
}

const cancelDeleteConfirm = () => {
  if (isDeleting.value) {
    return
  }
  isDeleteConfirming.value = false
  deleteErrorMessage.value = null
}

const formatDeleteError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
    return `${t('taskDeleteFailed')} (${error.response?.status ?? t('commonNetwork')})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return t('taskDeleteFailedRetry')
}

const confirmDelete = async () => {
  if (isDeleting.value) {
    return
  }

  isDeleting.value = true
  deleteErrorMessage.value = null
  try {
    await tasksStore.deleteTask(props.task.id)
    isDeleteConfirming.value = false
  } catch (error) {
    console.error('Delete task failed:', error)
    deleteErrorMessage.value = formatDeleteError(error)
  } finally {
    isDeleting.value = false
  }
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString(getDateTimeLocale(), {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.ui-task-actions {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ui-task-delete-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ui-task-delete-cancel,
.ui-task-delete-confirm-btn {
  min-height: 28px;
  padding: 0 10px;
  font-size: 11px;
}

.ui-task-delete-confirm-btn {
  color: #fff;
  border: 1px solid transparent;
  background: linear-gradient(145deg, #dc2626, #b91c1c);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    0 8px 18px -12px rgba(127, 29, 29, 0.66);
}

.ui-task-delete-confirm-btn:hover:not(:disabled) {
  background: linear-gradient(145deg, #ef4444, #dc2626);
}

.ui-task-delete-error {
  margin: 8px 0 0;
  color: #b91c1c;
  line-height: 1.45;
}
</style>
