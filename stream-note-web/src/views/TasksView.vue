<template>
  <section class="ui-tasks-shell">
    <SharedLiquidGlass
      class="ui-tasks-manage-glass"
      :liquid-glass="tasksHeaderLiquidGlass"
      :tilt-sensitivity="0.46"
    >
      <header class="ui-tasks-manage-bar">
        <div class="ui-tasks-header-copy">
          <h2 class="ui-heading ui-heading-sm">{{ t('tasksTitle') }}</h2>
          <p class="ui-body ui-body-sm ui-tasks-subtitle">{{ t('tasksSubtitle') }}</p>
        </div>

        <div class="ui-tasks-controls">
          <div v-if="isDev" class="ui-tasks-dev-tools">
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runAnalyzeDocument"
            >
              {{ isExtracting ? t('tasksAnalyzingDoc') : t('tasksAnalyzeDoc') }}
            </button>
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runAnalyzePending"
            >
              {{ isAnalyzing ? t('tasksAnalyzingPending') : t('tasksAnalyzePending') }}
            </button>
            <button
              type="button"
              class="ui-btn ui-btn-ghost ui-btn-pill ui-tasks-dev-btn"
              :disabled="isExtracting || isAnalyzing || isResetting"
              @click="runResetAIState"
            >
              {{ isResetting ? t('tasksResettingAI') : t('tasksResetAI') }}
            </button>
          </div>

          <div class="ui-tasks-search">
            <input
              v-model="searchQuery"
              type="search"
              class="ui-tasks-search-input"
              :placeholder="t('tasksSearchPlaceholder')"
              :aria-label="t('tasksSearchAriaLabel')"
              :disabled="tasksStore.isLoading || isExtracting || isAnalyzing || isResetting"
            />
            <button
              v-if="hasSearchQuery"
              type="button"
              class="ui-tasks-search-clear"
              :aria-label="t('tasksSearchClear')"
              @click="clearSearch"
            >
              {{ t('tasksSearchClear') }}
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
      <p v-if="extractStatusLabel !== null" class="ui-pill">{{ extractStatusLabel }}</p>
      <p v-if="analyzeStatusLabel !== null" class="ui-pill">{{ analyzeStatusLabel }}</p>
      <p v-if="resetStatusLabel !== null" class="ui-pill">{{ resetStatusLabel }}</p>
      <p v-if="errorMessage" class="ui-pill ui-pill-strong">{{ errorMessage }}</p>
    </section>

    <section v-if="tasksStore.isLoading || isExtracting || isAnalyzing" class="ui-list-stack ui-tasks-list">
      <div v-for="i in 3" :key="i" class="ui-task-skeleton">
        <div class="ui-task-skeleton-content">
          <div class="ui-task-skeleton-line" style="width: 80%"></div>
          <div class="ui-task-skeleton-line" style="width: 60%"></div>
        </div>
        <div class="ui-task-skeleton-meta">
          <div class="ui-task-skeleton-pill"></div>
        </div>
      </div>
    </section>

    <section v-else-if="filteredTasks.length > 0" class="ui-list-stack ui-tasks-list">
      <div
        v-for="task in filteredTasks"
        :id="taskAnchorId(task.id)"
        :key="task.id"
        :class="['ui-tasks-item-anchor', { 'is-focused': focusedTaskId === task.id }]"
      >
        <TaskItem
          :task="task"
          class="ui-tasks-item"
        />
      </div>
    </section>

    <section v-else class="ui-surface-card ui-empty-state ui-tasks-empty">
      <h2 class="ui-heading ui-heading-lg">{{ emptyTitle }}</h2>
      <p class="ui-body ui-body-sm ui-empty-description">{{ emptyDescription }}</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useDocumentStore } from '@/stores/document'
import TaskItem from '@/components/tasks/TaskItem.vue'
import SharedLiquidGlass from '@/components/glass/SharedLiquidGlass.vue'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { useI18n } from '@/composables/useI18n'
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
const documentStore = useDocumentStore()
const route = useRoute()
const { locale, t } = useI18n()
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
const searchQuery = ref('')
const focusedTaskId = ref<string | null>(null)
let focusedTaskTimer: ReturnType<typeof setTimeout> | null = null

const normalizeSearchText = (value: string): string => value.trim().toLocaleLowerCase()
const normalizedSearchQuery = computed(() => normalizeSearchText(searchQuery.value))
const hasSearchQuery = computed(() => normalizedSearchQuery.value.length > 0)
const filteredTasks = computed(() => {
  const keyword = normalizedSearchQuery.value
  if (keyword === '') {
    return tasksStore.tasks
  }

  return tasksStore.tasks.filter(task => {
    const searchable = [task.text, task.due_date ?? '', task.raw_time_expr ?? '']
      .join(' ')
    return normalizeSearchText(searchable).includes(keyword)
  })
})

const totalCountLabel = computed(() => {
  if (hasSearchQuery.value) {
    return `${t('tasksSearchResultsPrefix')} ${filteredTasks.value.length}/${tasksStore.tasks.length} ${t('tasksSearchResultsSuffix')}`
  }

  const count = tasksStore.summary.total_count
  if (locale.value === 'zh') {
    return `${count}${t('tasksUnitPlural')}`
  }
  return `${count} ${count === 1 ? t('tasksUnitSingular') : t('tasksUnitPlural')}`
})
const toggleLabel = computed(() =>
  tasksStore.showHiddenTasks ? t('tasksToggleShowingHidden') : t('tasksToggleHidingHidden')
)
const toggleAriaLabel = computed(() =>
  tasksStore.showHiddenTasks ? t('tasksToggleAriaHide') : t('tasksToggleAriaShow')
)
const emptyTitle = computed(() =>
  hasSearchQuery.value
    ? t('tasksSearchEmptyTitle')
    : tasksStore.showHiddenTasks
      ? t('tasksEmptyWithHidden')
      : t('tasksEmptyDefault')
)
const emptyDescription = computed(() =>
  hasSearchQuery.value
    ? t('tasksSearchEmptyDesc')
    : tasksStore.showHiddenTasks
      ? t('tasksEmptyWithHiddenDesc')
      : t('tasksEmptyDefaultDesc')
)
const extractStatusLabel = computed<string | null>(() => {
  if (extractResult.value === null) {
    return null
  }
  return `${t('tasksFoundPrefix')} ${extractResult.value.tasks_found} ${t('tasksFoundSuffix')}`
})
const analyzeStatusLabel = computed<string | null>(() => {
  if (analyzeResult.value === null) {
    return null
  }
  return `${t('tasksAnalyzedPrefix')} ${analyzeResult.value.analyzed_count} ${t('tasksAnalyzedMiddle')} ${analyzeResult.value.tasks_found} ${t('tasksAnalyzedSuffix')}`
})
const resetStatusLabel = computed<string | null>(() => {
  if (resetResult.value === null) {
    return null
  }
  return `${t('tasksResetPrefix')} ${resetResult.value.deleted_tasks} ${t('tasksResetMiddle')} ${resetResult.value.reset_blocks} ${t('tasksResetSuffix')}`
})

const toggleHiddenTasks = async () => {
  await tasksStore.setShowHiddenTasks(!tasksStore.showHiddenTasks)
}

const taskAnchorId = (taskId: string): string => `task-item-${taskId}`

const resolveFocusTaskId = (): string | null => {
  const queryValue = route.query.focusTask
  if (typeof queryValue !== 'string') {
    return null
  }

  const value = queryValue.trim()
  return value === '' ? null : value
}

const scrollToFocusedTask = async (taskId: string) => {
  await nextTick()
  const target = document.getElementById(taskAnchorId(taskId))
  if (target !== null) {
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  focusedTaskId.value = taskId
  if (focusedTaskTimer !== null) {
    clearTimeout(focusedTaskTimer)
  }

  focusedTaskTimer = setTimeout(() => {
    focusedTaskId.value = null
    focusedTaskTimer = null
  }, 1800)
}

const clearSearch = () => {
  searchQuery.value = ''
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
    return `${t('commonRequestFailed')} (${error.response?.status ?? t('commonNetwork')})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return t('commonUnknownError')
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
      errorMessage.value = t('tasksNoDocumentFound')
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
  if (!documentStore.content) {
    await documentStore.loadDocument()
  }

  const taskId = resolveFocusTaskId()
  if (taskId !== null) {
    await scrollToFocusedTask(taskId)
  }
})

watch(
  () => [route.query.focusTask, filteredTasks.value.length],
  async () => {
    const taskId = resolveFocusTaskId()
    if (taskId === null) {
      focusedTaskId.value = null
      return
    }

    if (filteredTasks.value.some(task => task.id === taskId)) {
      await scrollToFocusedTask(taskId)
    }
  }
)

onBeforeUnmount(() => {
  if (focusedTaskTimer !== null) {
    clearTimeout(focusedTaskTimer)
    focusedTaskTimer = null
  }
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

.ui-tasks-search {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.ui-tasks-search-input {
  min-height: 30px;
  width: 180px;
  border-radius: 999px;
  border: 1px solid rgba(214, 211, 209, 0.54);
  background: rgba(255, 255, 255, 0.72);
  color: var(--text-primary);
  font-size: 12px;
  padding: 0 58px 0 12px;
  outline: none;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.ui-tasks-search-input::placeholder {
  color: var(--text-tertiary);
}

.ui-tasks-search-input:focus-visible {
  border-color: rgba(var(--color-accent), 0.56);
  box-shadow: 0 0 0 3px rgba(var(--color-accent), 0.18);
  background: rgba(255, 255, 255, 0.88);
}

.ui-tasks-search-input:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}

.ui-tasks-search-clear {
  position: absolute;
  right: 3px;
  top: 3px;
  min-height: 24px;
  border: 0;
  border-radius: 999px;
  background: rgba(245, 245, 244, 0.92);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  padding: 0 10px;
  line-height: 1;
  cursor: pointer;
}

.ui-tasks-search-clear:hover {
  color: var(--text-primary);
  background: rgba(231, 229, 228, 0.95);
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

.ui-tasks-item-anchor {
  border-radius: 18px;
  transition: box-shadow 0.2s ease, background-color 0.2s ease;
}

.ui-tasks-item-anchor.is-focused {
  box-shadow: 0 0 0 2px rgba(var(--color-accent), 0.38);
  background: rgba(255, 255, 255, 0.24);
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

  .ui-tasks-search {
    width: 100%;
  }

  .ui-tasks-search-input {
    width: 100%;
    min-height: 28px;
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
