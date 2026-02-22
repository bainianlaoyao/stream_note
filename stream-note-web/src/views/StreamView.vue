<template>
  <section ref="streamShellRef" class="ui-stream-shell">
    <div class="ui-stream-recovery">
      <button class="ui-btn ui-btn-ghost ui-stream-recovery-toggle" type="button" @click="toggleRecovery">
        {{ isRecoveryOpen ? t('streamRecoveryClose') : t('streamRecoveryOpen') }}
      </button>

      <div v-if="isRecoveryOpen" class="glass-panel ui-stream-recovery-panel">
        <header class="ui-stream-recovery-head">
          <h3 class="ui-heading ui-heading-sm">{{ t('streamRecoveryTitle') }}</h3>
          <p class="ui-text-muted">{{ t('streamRecoveryHint') }}</p>
        </header>

        <p v-if="documentStore.isLoadingRecovery" class="ui-text-muted">
          {{ t('streamRecoveryLoading') }}
        </p>
        <p v-else-if="documentStore.recoveryCandidates.length === 0" class="ui-text-muted">
          {{ t('streamRecoveryEmpty') }}
        </p>
        <div v-else class="ui-stream-recovery-list">
          <article
            v-for="candidate in documentStore.recoveryCandidates"
            :key="candidate.id"
            class="ui-stream-recovery-item"
          >
            <div class="ui-stream-recovery-meta">
              <strong>{{ recoveryKindLabel(candidate.kind) }}</strong>
              <span>{{ formatCandidateMeta(candidate.created_at, candidate.char_count) }}</span>
            </div>
            <button
              class="ui-btn ui-btn-ghost ui-stream-recovery-action"
              type="button"
              :disabled="documentStore.isRestoring"
              @click="restoreCandidate(candidate.id)"
            >
              {{ documentStore.isRestoring ? t('streamRecoveryRestoring') : t('streamRecoveryRestore') }}
            </button>
          </article>
        </div>

        <button
          v-if="documentStore.undoRevisionId != null"
          class="ui-btn ui-btn-ghost ui-stream-recovery-undo"
          type="button"
          :disabled="documentStore.isRestoring"
          @click="undoRestore"
        >
          {{ t('streamRecoveryUndo') }}
        </button>

        <p v-if="recoveryErrorMessage !== null" class="ui-stream-recovery-error">
          {{ recoveryErrorMessage }}
        </p>
      </div>
    </div>

    <EditorContent :editor="editor" class="ui-editor-surface" />

    <button
      v-if="showScrollToBottom"
      type="button"
      class="ui-btn ui-btn-ghost ui-btn-pill ui-stream-scroll-bottom"
      :aria-label="t('streamScrollToBottom')"
      :title="t('streamScrollToBottom')"
      @click="scrollToBottom"
    >
      <svg
        class="ui-stream-scroll-bottom-icon"
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M12 5v14" />
        <path d="m6 13 6 6 6-6" />
      </svg>
    </button>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { useDebounceFn } from '@vueuse/core'
import { useDocumentStore } from '@/stores/document'
import type { DocumentContent, DocumentRecoveryKind } from '@/types/document'
import { useI18n } from '@/composables/useI18n'

const documentStore = useDocumentStore()
const route = useRoute()
const { locale, t, getDateTimeLocale } = useI18n()
const streamShellRef = ref<HTMLElement | null>(null)
const editorSurfaceRef = ref<HTMLElement | null>(null)
const isRecoveryOpen = ref(false)
const showScrollToBottom = ref(false)
const BOTTOM_SCROLL_THRESHOLD = 24
let highlightRetryTimer: ReturnType<typeof setTimeout> | null = null

const recoveryErrorMessage = computed(() => {
  if (documentStore.recoveryError === 'load_candidates_failed') {
    return t('streamRecoveryLoadFailed')
  }
  if (documentStore.recoveryError === 'restore_failed') {
    return t('streamRecoveryRestoreFailed')
  }
  return null
})

const debouncedSave = useDebounceFn(async (json: DocumentContent) => {
  await documentStore.saveDocument(json)
}, 500)

const recoveryKindLabel = (kind: DocumentRecoveryKind): string => {
  if (kind === 'latest') {
    return t('streamRecoveryCandidateLatest')
  }
  if (kind === 'yesterday') {
    return t('streamRecoveryCandidateYesterday')
  }
  return t('streamRecoveryCandidateStable')
}

const formatDate = (value: Date | string): string => {
  const dateValue = typeof value === 'string' ? new Date(value) : value
  return new Intl.DateTimeFormat(getDateTimeLocale(), {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(dateValue)
}

const formatCandidateMeta = (createdAt: string, charCount: number): string => {
  const charUnit = locale.value === 'zh' ? '字' : 'chars'
  return `${formatDate(createdAt)} · ${charCount} ${charUnit}`
}

const toggleRecovery = async () => {
  isRecoveryOpen.value = !isRecoveryOpen.value
  if (isRecoveryOpen.value) {
    await documentStore.loadRecoveryCandidates()
  }
}

const restoreCandidate = async (revisionId: string) => {
  try {
    await documentStore.restoreFromRevision(revisionId)
  } catch (error) {
    console.error(error)
  }
}

const undoRestore = async () => {
  try {
    await documentStore.undoLastRestore()
  } catch (error) {
    console.error(error)
  }
}

const resolveEditorSurface = (): HTMLElement | null => {
  if (editorSurfaceRef.value !== null) {
    return editorSurfaceRef.value
  }

  const shell = streamShellRef.value
  if (shell === null) {
    return null
  }

  const surface = shell.querySelector('.ui-editor-surface')
  if (surface instanceof HTMLElement) {
    editorSurfaceRef.value = surface
    return surface
  }

  return null
}

const updateScrollToBottomVisibility = () => {
  const surface = resolveEditorSurface()
  if (surface === null) {
    showScrollToBottom.value = false
    return
  }

  const overflowDistance = surface.scrollHeight - surface.clientHeight
  const isScrollable = overflowDistance > BOTTOM_SCROLL_THRESHOLD
  const distanceToBottom = surface.scrollHeight - (surface.scrollTop + surface.clientHeight)
  showScrollToBottom.value = isScrollable && distanceToBottom > BOTTOM_SCROLL_THRESHOLD
}

const handleSurfaceScroll = () => {
  updateScrollToBottomVisibility()
}

const scrollToBottom = () => {
  const surface = resolveEditorSurface()
  if (surface === null) {
    return
  }

  surface.scrollTo({ top: surface.scrollHeight, behavior: 'smooth' })
  setTimeout(() => {
    updateScrollToBottomVisibility()
  }, 260)
}

const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: () => t('streamPlaceholder')
    })
  ],
  content: '',
  onUpdate: ({ editor }) => {
    const json = editor.getJSON()
    documentStore.updateContent(json)
    debouncedSave(json)
    nextTick(() => {
      updateScrollToBottomVisibility()
    })
  }
})

watch(
  () => documentStore.content,
  (newContent) => {
    if (editor.value == null || newContent === null) {
      return
    }

    const currentContent = editor.value.getJSON()
    if (JSON.stringify(currentContent) !== JSON.stringify(newContent)) {
      editor.value.commands.setContent(newContent)
    }
  },
  { deep: true }
)

const highlightNodeAtPos = (targetPos: number) => {
  if (!editor.value || targetPos < 0) {
    return false
  }

  const selectionPos = Math.min(targetPos + 1, editor.value.state.doc.content.size)
  editor.value.commands.focus()
  editor.value.commands.setTextSelection(selectionPos)
  editor.value.commands.scrollIntoView()

  nextTick(() => {
    const rawDomNode = editor.value?.view.nodeDOM(targetPos)
    const domNode =
      rawDomNode instanceof HTMLElement
        ? rawDomNode
        : rawDomNode instanceof Text
          ? rawDomNode.parentElement
          : null

    if (domNode !== null) {
      domNode.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' })
      domNode.classList.add('ui-highlight-anim')
      setTimeout(() => {
        domNode.classList.remove('ui-highlight-anim')
      }, 2000)
    }

    updateScrollToBottomVisibility()
  })

  return true
}

const highlightText = (text: string): boolean => {
  if (!editor.value) {
    return false
  }

  const doc = editor.value.state.doc
  let targetPos = -1

  doc.descendants((node, pos) => {
    if (node.isTextblock && node.textContent.includes(text)) {
      targetPos = pos
      return false
    }
  })

  if (targetPos < 0) {
    return false
  }

  return highlightNodeAtPos(targetPos)
}

const highlightBlockByIndex = (blockIndex: number): boolean => {
  if (!editor.value || !Number.isInteger(blockIndex) || blockIndex < 0) {
    return false
  }

  const doc = editor.value.state.doc
  let textBlockIndex = 0
  let targetPos = -1

  doc.descendants((node, pos) => {
    if (
      !node.isTextblock ||
      (node.type.name !== 'paragraph' &&
        node.type.name !== 'heading' &&
        node.type.name !== 'codeBlock') ||
      node.textContent.trim() === ''
    ) {
      return
    }

    if (textBlockIndex === blockIndex) {
      targetPos = pos
      return false
    }

    textBlockIndex += 1
  })

  if (targetPos < 0) {
    return false
  }

  return highlightNodeAtPos(targetPos)
}

const hasRouteHighlightTarget = (): boolean => {
  const blockIndexValue = route.query.blockIndex
  const textValue = route.query.text
  return typeof blockIndexValue === 'string' || typeof textValue === 'string'
}

const highlightFromRoute = (): boolean => {
  const blockIndexValue = route.query.blockIndex
  const textValue = route.query.text
  const blockIndex =
    typeof blockIndexValue === 'string' ? Number.parseInt(blockIndexValue, 10) : Number.NaN
  const text = typeof textValue === 'string' ? textValue : null

  const matchedBlock = Number.isInteger(blockIndex) ? highlightBlockByIndex(blockIndex) : false
  if (!matchedBlock && text !== null && text.trim() !== '') {
    return highlightText(text)
  }

  return matchedBlock
}

const clearHighlightRetryTimer = () => {
  if (highlightRetryTimer !== null) {
    clearTimeout(highlightRetryTimer)
    highlightRetryTimer = null
  }
}

const highlightFromRouteWithRetry = (attempt = 0) => {
  const maxAttempts = 4
  if (!hasRouteHighlightTarget()) {
    clearHighlightRetryTimer()
    return
  }

  const matched = highlightFromRoute()
  if (matched || attempt >= maxAttempts) {
    clearHighlightRetryTimer()
    return
  }

  clearHighlightRetryTimer()
  highlightRetryTimer = setTimeout(() => {
    highlightRetryTimer = null
    highlightFromRouteWithRetry(attempt + 1)
  }, 120)
}

watch(
  () => [route.query.blockIndex, route.query.text],
  () => {
    highlightFromRouteWithRetry()
    nextTick(() => {
      updateScrollToBottomVisibility()
    })
  }
)

watch(
  () => documentStore.content,
  () => {
    highlightFromRouteWithRetry()
    nextTick(() => {
      updateScrollToBottomVisibility()
    })
  }
)

onMounted(async () => {
  await nextTick()
  const surface = resolveEditorSurface()
  surface?.addEventListener('scroll', handleSurfaceScroll, { passive: true })
  updateScrollToBottomVisibility()

  await documentStore.loadDocument()
  await documentStore.loadRecoveryCandidates()
  if (editor.value != null && documentStore.content !== null) {
    editor.value.commands.setContent(documentStore.content)

    nextTick(() => {
      highlightFromRouteWithRetry()
      updateScrollToBottomVisibility()
    })
  }
})

onBeforeUnmount(() => {
  clearHighlightRetryTimer()
  const surface = resolveEditorSurface()
  surface?.removeEventListener('scroll', handleSurfaceScroll)
  editor.value?.destroy()
})
</script>

<style scoped>
.ui-stream-shell {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
}

.ui-stream-recovery {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.ui-stream-recovery-toggle {
  min-height: 32px;
  padding: 0 12px;
  font-size: 12px;
}

.ui-stream-recovery-panel {
  width: min(360px, calc(100vw - 40px));
  padding: 12px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ui-stream-recovery-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ui-stream-recovery-head h3 {
  margin: 0;
  font-size: 14px;
  line-height: 1.2;
}

.ui-stream-recovery-head p {
  margin: 0;
  font-size: 12px;
}

.ui-stream-recovery-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ui-stream-recovery-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.42);
  background: rgba(255, 255, 255, 0.6);
}

.ui-stream-recovery-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ui-stream-recovery-meta strong {
  font-size: 12px;
  color: var(--text-primary);
}

.ui-stream-recovery-meta span {
  font-size: 11px;
  color: var(--text-tertiary);
}

.ui-stream-recovery-action {
  min-height: 30px;
  padding: 0 10px;
  font-size: 12px;
  white-space: nowrap;
}

.ui-stream-recovery-undo {
  width: 100%;
  min-height: 32px;
  font-size: 12px;
}

.ui-stream-recovery-error {
  margin: 0;
  color: #dc2626;
  font-size: 12px;
}

.ui-stream-shell :deep(.ui-editor-surface) {
  flex: 1 1 auto;
  min-height: 0;
}

.ui-stream-scroll-bottom {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 6;
  min-height: 34px;
  min-width: 34px;
  padding: 0;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.88),
    0 10px 22px -16px rgba(41, 37, 36, 0.46);
}

.ui-stream-scroll-bottom-icon {
  width: 16px;
  height: 16px;
}

@media (max-width: 900px) {
  .ui-stream-recovery-panel {
    width: min(340px, calc(100vw - 52px));
  }

  .ui-stream-scroll-bottom {
    right: calc(10px + var(--safe-right));
    bottom: calc(10px + var(--safe-bottom));
    min-height: 32px;
    min-width: 32px;
  }
}
</style>
