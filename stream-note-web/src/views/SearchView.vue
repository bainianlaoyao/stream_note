<template>
  <section class="ui-search-shell">
    <SharedLiquidGlass
      class="ui-search-glass"
      :liquid-glass="searchHeaderLiquidGlass"
      :tilt-sensitivity="0.42"
    >
      <header class="ui-search-head">
        <div>
          <h2 class="ui-heading ui-heading-sm">{{ t('searchTitle') }}</h2>
          <p class="ui-body ui-body-sm ui-search-subtitle">{{ t('searchSubtitle') }}</p>
        </div>
        <span class="ui-count-chip ui-search-count">{{ resultCountLabel }}</span>
      </header>

      <div class="ui-search-input-row">
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="search"
          class="ui-search-input"
          :placeholder="t('searchPlaceholder')"
          :aria-label="t('searchAriaLabel')"
          :disabled="isLoading"
        />
        <button
          v-if="hasSearchQuery"
          type="button"
          class="ui-search-clear"
          :aria-label="t('searchClear')"
          @click="clearSearch"
        >
          {{ t('searchClear') }}
        </button>
      </div>

      <div class="ui-search-source-row">
        <span class="ui-pill ui-search-source-pill">{{ t('searchSourceStream') }} {{ streamBlocks.length }}</span>
        <span class="ui-pill ui-search-source-pill">{{ t('searchSourceTasks') }} {{ tasksIndex.length }}</span>
      </div>
    </SharedLiquidGlass>

    <section v-if="errorMessage" class="ui-search-status">
      <p class="ui-pill ui-pill-strong">{{ errorMessage }}</p>
      <button type="button" class="ui-btn ui-btn-ghost ui-btn-pill ui-search-retry" @click="loadSearchSources">
        {{ t('searchRetry') }}
      </button>
    </section>

    <section v-if="isLoading" class="ui-list-stack ui-search-list">
      <article v-for="i in 3" :key="i" class="ui-search-skeleton"></article>
    </section>

    <section v-else-if="!hasSearchQuery" class="ui-surface-card ui-empty-state ui-search-empty">
      <h3 class="ui-heading ui-heading-lg">{{ t('searchStartTitle') }}</h3>
      <p class="ui-body ui-body-sm ui-empty-description">{{ t('searchStartDesc') }}</p>
    </section>

    <section v-else-if="results.length === 0" class="ui-surface-card ui-empty-state ui-search-empty">
      <h3 class="ui-heading ui-heading-lg">{{ t('searchEmptyTitle') }}</h3>
      <p class="ui-body ui-body-sm ui-empty-description">{{ t('searchEmptyDesc') }}</p>
    </section>

    <section v-else class="ui-list-stack ui-search-list">
      <button
        v-for="result in results"
        :key="result.id"
        type="button"
        class="ui-search-result"
        :aria-label="t('searchOpenItem')"
        @click="goToResult(result)"
      >
        <div class="ui-search-result-head">
          <span class="ui-pill ui-search-source-pill">
            {{ result.source === 'stream' ? t('searchSourceStream') : t('searchSourceTasks') }}
          </span>
          <span class="ui-caption ui-search-result-meta">{{ result.meta }}</span>
        </div>
        <p class="ui-body ui-body-sm ui-search-result-text">{{ result.snippet }}</p>
      </button>
    </section>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SharedLiquidGlass from '@/components/glass/SharedLiquidGlass.vue'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { useDocumentStore } from '@/stores/document'
import { useI18n } from '@/composables/useI18n'
import type { DocumentContent } from '@/types/document'
import type { Task } from '@/types/task'
import { getDocument, getTasks } from '@/services/api'

type SearchSource = 'stream' | 'tasks'

interface SearchResultBase {
  id: string
  source: SearchSource
  text: string
  snippet: string
  meta: string
  matchIndex: number
}

interface StreamSearchResult extends SearchResultBase {
  source: 'stream'
  blockIndex: number
}

interface TaskSearchResult extends SearchResultBase {
  source: 'tasks'
  taskId: string
}

type SearchResult = StreamSearchResult | TaskSearchResult
interface StreamBlockEntry {
  text: string
  blockIndex: number
}

const searchHeaderLiquidGlass: Partial<LiquidGlassProps> = {
  blurAmount: 0.24,
  displacementScale: 26,
  saturation: 104,
  aberrationIntensity: 0.74,
  cornerRadius: 16,
  padding: '12px'
}

const EMPTY_DOC_CONTENT: DocumentContent = { type: 'doc', content: [] }

const router = useRouter()
const route = useRoute()
const documentStore = useDocumentStore()
const { locale, t, getDateTimeLocale } = useI18n()

const searchInputRef = ref<HTMLInputElement | null>(null)
const searchQuery = ref('')
const tasksIndex = ref<Task[]>([])
const streamContent = ref<DocumentContent | null>(null)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

const normalizeSearchText = (value: string): string => value.trim().toLocaleLowerCase()
const normalizedSearchQuery = computed(() => normalizeSearchText(searchQuery.value))
const hasSearchQuery = computed(() => normalizedSearchQuery.value.length > 0)

const SEARCHABLE_STREAM_NODE_TYPES = new Set(['paragraph', 'heading', 'codeBlock'])

const collectNodeText = (node: unknown): string => {
  if (Array.isArray(node)) {
    return node.map(item => collectNodeText(item)).join('')
  }

  if (node === null || typeof node !== 'object') {
    return ''
  }

  const candidate = node as {
    type?: unknown
    text?: unknown
    content?: unknown
  }

  if (candidate.type === 'hardBreak') {
    return ' '
  }

  const ownText = typeof candidate.text === 'string' ? candidate.text : ''
  const childText = collectNodeText(candidate.content)
  return `${ownText}${childText}`
}

const extractSearchableStreamBlocks = (content: DocumentContent): string[] => {
  const blocks: string[] = []

  const visit = (node: unknown): void => {
    if (Array.isArray(node)) {
      for (const item of node) {
        visit(item)
      }
      return
    }

    if (node === null || typeof node !== 'object') {
      return
    }

    const candidate = node as {
      type?: unknown
      content?: unknown
    }
    const nodeType = typeof candidate.type === 'string' ? candidate.type : ''

    if (SEARCHABLE_STREAM_NODE_TYPES.has(nodeType)) {
      const text = collectNodeText(candidate).replace(/\s+/g, ' ').trim()
      if (text !== '') {
        blocks.push(text)
      }
    }

    visit(candidate.content)
  }

  visit(content.content)
  return blocks
}

const streamBlocks = computed<StreamBlockEntry[]>(() => {
  const source = streamContent.value ?? EMPTY_DOC_CONTENT
  return extractSearchableStreamBlocks(source).map((text, blockIndex) => ({
    text,
    blockIndex
  }))
})

const buildSnippet = (text: string, keyword: string): string => {
  const cleanText = text.replace(/\s+/g, ' ').trim()
  if (cleanText === '' || keyword === '') {
    return cleanText
  }

  const matchIndex = cleanText.toLocaleLowerCase().indexOf(keyword)
  if (matchIndex < 0 || cleanText.length <= 120) {
    return cleanText
  }

  const radius = 54
  const start = Math.max(0, matchIndex - radius)
  const end = Math.min(cleanText.length, matchIndex + keyword.length + radius)
  const prefix = start > 0 ? '...' : ''
  const suffix = end < cleanText.length ? '...' : ''
  return `${prefix}${cleanText.slice(start, end)}${suffix}`
}

const formatTaskMeta = (task: Task): string => {
  const baseLabel = t('searchSourceTasks')
  if (task.due_date === null) {
    return baseLabel
  }

  const dueDate = new Date(task.due_date)
  if (Number.isNaN(dueDate.getTime())) {
    return baseLabel
  }

  const formatted = dueDate.toLocaleDateString(getDateTimeLocale(), {
    month: 'short',
    day: 'numeric'
  })
  return `${baseLabel} · ${formatted}`
}

const streamResults = computed<StreamSearchResult[]>(() => {
  const keyword = normalizedSearchQuery.value
  if (keyword === '') {
    return []
  }

  return streamBlocks.value
    .map(({ text, blockIndex }) => {
      const normalizedBlock = normalizeSearchText(text)
      const matchIndex = normalizedBlock.indexOf(keyword)
      if (matchIndex < 0) {
        return null
      }

      return {
        id: `stream-${blockIndex}-${matchIndex}`,
        source: 'stream',
        text,
        snippet: buildSnippet(text, keyword),
        meta: `${t('searchSourceStream')} #${blockIndex + 1}`,
        blockIndex,
        matchIndex
      }
    })
    .filter((result): result is StreamSearchResult => result !== null)
})

const taskResults = computed<TaskSearchResult[]>(() => {
  const keyword = normalizedSearchQuery.value
  if (keyword === '') {
    return []
  }

  return tasksIndex.value
    .map(task => {
      const searchableText = [task.text, task.raw_time_expr ?? '', task.due_date ?? ''].join(' ')
      const normalized = normalizeSearchText(searchableText)
      const matchIndex = normalized.indexOf(keyword)
      if (matchIndex < 0) {
        return null
      }

      return {
        id: `task-${task.id}-${matchIndex}`,
        source: 'tasks',
        text: task.text,
        snippet: buildSnippet(task.text, keyword),
        meta: formatTaskMeta(task),
        taskId: task.id,
        matchIndex
      }
    })
    .filter((result): result is TaskSearchResult => result !== null)
})

const results = computed<SearchResult[]>(() =>
  [...streamResults.value, ...taskResults.value].sort((a, b) => {
    if (a.matchIndex !== b.matchIndex) {
      return a.matchIndex - b.matchIndex
    }

    if (a.source !== b.source) {
      return a.source === 'stream' ? -1 : 1
    }

    return a.id.localeCompare(b.id)
  })
)

const resultCountLabel = computed(() => {
  if (isLoading.value) {
    return t('searchLoading')
  }

  if (!hasSearchQuery.value) {
    const count = streamBlocks.value.length + tasksIndex.value.length
    return `${t('searchIndexedPrefix')} ${count} ${t('searchIndexedSuffix')}`
  }

  if (locale.value === 'zh') {
    return `${t('searchResultsPrefix')} ${results.value.length} ${t('searchResultsSuffix')}`
  }

  return `${results.value.length} ${t('searchResultsSuffix')}`
})

const clearSearch = () => {
  searchQuery.value = ''
  searchInputRef.value?.focus()
}

const formatError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
    return `${t('searchLoadFailed')} (${error.response?.status ?? t('commonNetwork')})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return t('searchLoadFailed')
}

const loadSearchSources = async () => {
  isLoading.value = true
  errorMessage.value = null
  try {
    if (documentStore.content === null) {
      await documentStore.loadDocument()
    }

    streamContent.value = documentStore.content
    if (streamBlocks.value.length === 0) {
      const remoteDocument = await getDocument()
      if (remoteDocument !== null) {
        streamContent.value = remoteDocument.content
      }
    }

    tasksIndex.value = await getTasks()
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isLoading.value = false
  }
}

const goToResult = async (result: SearchResult) => {
  if (result.source === 'stream') {
    await router.push({
      path: '/stream',
      query: {
        text: result.text,
        blockIndex: String(result.blockIndex)
      }
    })
    return
  }

  await router.push({
    path: '/tasks',
    query: {
      focusTask: result.taskId,
      text: result.text
    }
  })
}

onMounted(async () => {
  const routeQuery = route.query.q
  if (typeof routeQuery === 'string') {
    searchQuery.value = routeQuery
  }
  await loadSearchSources()
  searchInputRef.value?.focus()
})

watch(
  () => documentStore.content,
  (nextContent) => {
    if (nextContent !== null) {
      streamContent.value = nextContent
    }
  }
)
</script>

<style scoped>
.ui-search-shell {
  width: min(920px, 100%);
  margin-inline: auto;
  padding: 4px 4px 8px;
}

.ui-search-glass {
  margin-bottom: 10px;
}

.ui-search-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ui-search-subtitle {
  margin-top: 2px;
  line-height: 1.45;
}

.ui-search-count {
  min-height: 30px;
  text-transform: none;
}

.ui-search-input-row {
  position: relative;
  margin-top: 10px;
}

.ui-search-input {
  width: 100%;
  min-height: 38px;
  border-radius: 11px;
  border: 1px solid rgba(214, 211, 209, 0.56);
  background: rgba(255, 255, 255, 0.82);
  color: var(--text-primary);
  font-size: 13px;
  padding: 0 64px 0 12px;
  outline: none;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.ui-search-input::placeholder {
  color: var(--text-tertiary);
}

.ui-search-input:focus-visible {
  border-color: rgba(var(--color-accent), 0.56);
  box-shadow: 0 0 0 3px rgba(var(--color-accent), 0.18);
  background: rgba(255, 255, 255, 0.92);
}

.ui-search-input:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}

.ui-search-clear {
  position: absolute;
  top: 4px;
  right: 4px;
  min-height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(214, 211, 209, 0.46);
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  padding: 0 10px;
  cursor: pointer;
  transition: color 0.18s ease, background-color 0.18s ease, border-color 0.18s ease;
}

.ui-search-clear:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.94);
  border-color: rgba(214, 211, 209, 0.62);
}

.ui-search-source-row {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ui-search-source-pill {
  text-transform: none;
  letter-spacing: 0.01em;
}

.ui-search-status {
  margin: 0 2px 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.ui-search-retry {
  min-height: 30px;
  padding-inline: 12px;
}

.ui-search-list {
  gap: 8px;
}

.ui-search-skeleton {
  height: 74px;
  border-radius: 12px;
  border: 1px solid rgba(214, 211, 209, 0.44);
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.5), rgba(250, 250, 249, 0.8), rgba(255, 255, 255, 0.5));
  animation: ui-search-pulse 1.25s ease-in-out infinite;
}

.ui-search-result {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(214, 211, 209, 0.44);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  padding: 12px;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.ui-search-result:hover {
  border-color: rgba(var(--color-accent), 0.38);
  background: rgba(255, 255, 255, 0.88);
  transform: translateY(-1px);
  box-shadow: 0 10px 22px -18px rgba(41, 37, 36, 0.42);
}

.ui-search-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ui-search-result-meta {
  text-transform: none;
}

.ui-search-result-text {
  margin: 8px 0 0;
  line-height: 1.58;
  color: var(--text-primary);
  word-break: break-word;
}

.ui-search-empty {
  margin-top: 2px;
}

@keyframes ui-search-pulse {
  0% {
    opacity: 0.46;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.46;
  }
}

@media (max-width: 900px) {
  .ui-search-shell {
    width: 100%;
    padding: 2px 0 6px;
  }

  .ui-search-glass {
    margin-bottom: 8px;
  }

  .ui-search-head {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .ui-search-count {
    align-self: flex-start;
    min-height: 28px;
  }

  .ui-search-input {
    min-height: 36px;
  }

  .ui-search-clear {
    min-height: 28px;
  }

  .ui-search-status {
    margin: 0 0 8px;
    gap: 6px;
  }
}
</style>
