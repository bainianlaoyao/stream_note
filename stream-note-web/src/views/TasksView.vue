<template>
  <section class="ui-tasks-shell">
    <SharedLiquidGlass
      class="ui-tasks-manage-glass"
      :liquid-glass="tasksHeaderLiquidGlass"
      :tilt-sensitivity="0.46"
    >
      <header class="ui-tasks-manage-bar">
        <div class="ui-tasks-header-copy">
          <h2 class="ui-heading ui-heading-sm">Tasks</h2>
          <p class="ui-body ui-body-sm ui-tasks-subtitle">Completed tasks auto-hide after 24 hours.</p>
        </div>

        <div class="ui-tasks-controls">
          <div v-if="isDev" class="ui-tasks-dev-tools">
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runAnalyzeDocument"
            >
              {{ isExtracting ? 'Analyzing Doc...' : 'Analyze Doc' }}
            </button>
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runAnalyzePending"
            >
              {{ isAnalyzing ? 'Analyzing Pending...' : 'Analyze Pending' }}
            </button>
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runResetAIState"
            >
              {{ isResetting ? 'Resetting...' : 'Reset AI' }}
            </button>
          </div>

          <span class="ui-count-chip ui-tasks-count">{{ totalCountLabel }}</span>
          <button
            type="button"
            :class="['ui-tasks-toggle', { 'is-active': tasksStore.showHiddenTasks }]"
            :aria-label="toggleAriaLabel"
            :aria-pressed="tasksStore.showHiddenTasks"
            :disabled="tasksStore.isLoading"
            @click="toggleHiddenTasks"
          >
            <span class="ui-tasks-toggle-dot" aria-hidden="true"></span>
            <span class="ui-tasks-toggle-text">{{ toggleLabel }}</span>
          </button>
        </div>
      </header>
    </SharedLiquidGlass>

    <section v-if="isDev && (extractResult || analyzeResult || resetResult || errorMessage)" class="ui-tasks-dev-status">
      <p v-if="extractResult" class="ui-pill">Found {{ extractResult.tasks_found }} task(s)</p>
      <p v-if="analyzeResult" class="ui-pill">
        Analyzed {{ analyzeResult.analyzed_count }} block(s), {{ analyzeResult.tasks_found }} task(s)
      </p>
      <p v-if="resetResult" class="ui-pill">
        Reset {{ resetResult.deleted_tasks }} task(s), {{ resetResult.reset_blocks }} block(s)
      </p>
      <p v-if="errorMessage" class="ui-pill ui-pill-strong">{{ errorMessage }}</p>
    </section>

    <section v-if="tasksStore.tasks.length > 0" class="ui-list-stack ui-tasks-list">
      <TaskItem
        v-for="task in tasksStore.tasks"
        :key="task.id"
        :task="task"
        class="ui-tasks-item"
      />
    </section>

    <section v-else class="ui-surface-card ui-empty-state ui-tasks-empty">
      <h2 class="ui-heading ui-heading-lg">{{ emptyTitle }}</h2>
      <p class="ui-body ui-body-sm ui-empty-description">{{ emptyDescription }}</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import TaskItem from '@/components/tasks/TaskItem.vue'
import SharedLiquidGlass from '@/components/glass/SharedLiquidGlass.vue'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { ref } from 'vue'
import {
  analyzePendingBlocks,
  extractTasksFromContent,
  getDocument,
  resetDebugState,
  type AnalyzeResult,
  type ExtractResult,
  type ResetDebugStateResult
} from '@/services/api'

const tasksStore = useTasksStore()
const isDev = import.meta.env.DEV
const tasksHeaderLiquidGlass: Partial<LiquidGlassProps> = {
  blurAmount: 0.26,
  displacementScale: 28,
  saturation: 104,
  aberrationIntensity: 0.8,
  cornerRadius: 16,
  padding: '0'
}

const isExtracting = ref(false)
const isAnalyzing = ref(false)
const isResetting = ref(false)
const extractResult = ref<ExtractResult | null>(null)
const analyzeResult = ref<AnalyzeResult | null>(null)
const resetResult = ref<ResetDebugStateResult | null>(null)
const errorMessage = ref<string | null>(null)

const totalCountLabel = computed(() => {
  const count = tasksStore.summary.total_count
  return `${count} ${count === 1 ? 'task' : 'tasks'}`
})
const toggleLabel = computed(() =>
  tasksStore.showHiddenTasks ? 'Showing hidden completed' : 'Hiding hidden completed'
)
const toggleAriaLabel = computed(() =>
  tasksStore.showHiddenTasks ? 'Hide completed tasks hidden for over 24 hours' : 'Show completed tasks hidden for over 24 hours'
)
const emptyTitle = computed(() =>
  tasksStore.showHiddenTasks ? 'No tasks in this view' : 'All clear for now'
)
const emptyDescription = computed(() =>
  tasksStore.showHiddenTasks
    ? 'There are no pending or completed tasks right now.'
    : 'Create notes in Stream and run analysis to generate more tasks.'
)

const toggleHiddenTasks = async () => {
  await tasksStore.setShowHiddenTasks(!tasksStore.showHiddenTasks)
}

const clearStatus = () => {
  extractResult.value = null
  analyzeResult.value = null
  resetResult.value = null
  errorMessage.value = null
}

const formatError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
    return `Request failed (${error.response?.status ?? 'network'})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return 'Unknown error'
}

const runAnalyzeDocument = async () => {
  if (!isDev || isExtracting.value || isAnalyzing.value || isResetting.value) {
    return
  }

  isExtracting.value = true
  clearStatus()
  try {
    const document = await getDocument()
    if (document === null) {
      errorMessage.value = 'No document found. Open Stream and type something first.'
      return
    }

    extractResult.value = await extractTasksFromContent(document.content)
    await tasksStore.loadTasks(tasksStore.showHiddenTasks)
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isExtracting.value = false
  }
}

const runAnalyzePending = async () => {
  if (!isDev || isExtracting.value || isAnalyzing.value || isResetting.value) {
    return
  }

  isAnalyzing.value = true
  clearStatus()
  try {
    analyzeResult.value = await analyzePendingBlocks(true)
    await tasksStore.loadTasks(tasksStore.showHiddenTasks)
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isAnalyzing.value = false
  }
}

const runResetAIState = async () => {
  if (!isDev || isExtracting.value || isAnalyzing.value || isResetting.value) {
    return
  }

  isResetting.value = true
  clearStatus()
  try {
    resetResult.value = await resetDebugState()
    await tasksStore.loadTasks(tasksStore.showHiddenTasks)
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isResetting.value = false
  }
}

onMounted(async () => {
  await tasksStore.loadTasks()
})
</script>

<style scoped>
.ui-tasks-shell {
  width: min(920px, 100%);
  margin-inline: auto;
  padding: 4px 4px 6px;
}

.ui-tasks-manage-glass {
  margin-bottom: 10px;
}

.ui-tasks-manage-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 12px;
}

.ui-tasks-header-copy {
  min-width: 0;
}

.ui-tasks-subtitle {
  margin-top: 2px;
  line-height: 1.45;
}

.ui-tasks-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex-shrink: 0;
}

.ui-tasks-dev-tools {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.ui-tasks-dev-btn {
  min-height: 30px;
  padding-inline: 10px;
  font-size: 12px;
}

.ui-tasks-dev-status {
  margin: 0 2px 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.ui-tasks-count {
  min-height: 30px;
  padding-inline: 11px;
  text-transform: none;
  letter-spacing: 0.01em;
}

.ui-tasks-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  border-radius: 999px;
  padding: 0 11px 0 8px;
  border: 1px solid rgba(214, 211, 209, 0.48);
  background: rgba(255, 255, 255, 0.68);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.ui-tasks-toggle:hover:not(:disabled) {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.84);
  border-color: rgba(214, 211, 209, 0.62);
}

.ui-tasks-toggle:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.ui-tasks-toggle.is-active {
  border-color: rgba(var(--color-accent), 0.44);
  background: rgba(250, 237, 205, 0.52);
  color: var(--color-accent-primary);
}

.ui-tasks-toggle-dot {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: rgba(168, 162, 158, 0.34);
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.86),
    0 2px 6px -4px rgba(41, 37, 36, 0.52);
  transition: background-color 0.18s ease, box-shadow 0.18s ease;
}

.ui-tasks-toggle.is-active .ui-tasks-toggle-dot {
  background: rgba(var(--color-accent), 0.92);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    0 2px 7px -4px rgba(var(--color-accent-dim), 0.66);
}

.ui-tasks-toggle-text {
  white-space: nowrap;
}

.ui-tasks-list {
  gap: 10px;
}

.ui-tasks-item {
  margin: 0;
}

.ui-tasks-empty {
  margin-top: 2px;
}

.ui-tasks-empty .ui-empty-description {
  max-width: 32ch;
  margin: 8px auto 0;
}

@media (max-width: 900px) {
  .ui-tasks-shell {
    width: 100%;
    padding: 2px 0 4px;
  }

  .ui-tasks-manage-glass {
    margin-bottom: 8px;
  }

  .ui-tasks-manage-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .ui-tasks-controls {
    width: 100%;
    justify-content: flex-start;
    gap: 6px;
  }

  .ui-tasks-dev-tools {
    width: 100%;
    justify-content: flex-start;
  }

  .ui-tasks-dev-btn {
    flex: 1 1 auto;
    min-height: 28px;
  }

  .ui-tasks-dev-status {
    margin: 0 0 8px;
  }

  .ui-tasks-count {
    min-height: 28px;
  }

  .ui-tasks-toggle {
    min-height: 28px;
  }

  .ui-tasks-list {
    gap: 8px;
  }
}
</style>
