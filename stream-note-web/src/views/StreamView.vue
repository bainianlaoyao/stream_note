<template>
  <section class="ui-stream-shell">
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
const isRecoveryOpen = ref(false)

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

const highlightText = (text: string) => {
  if (!editor.value) return
  
  const doc = editor.value.state.doc
  let targetPos = -1
  
  doc.descendants((node, pos) => {
    if (node.isTextblock && node.textContent.includes(text)) {
      targetPos = pos
      return false // stop traversal
    }
  })

  if (targetPos !== -1) {
    editor.value.commands.setTextSelection(targetPos)
    editor.value.commands.scrollIntoView()
    
    // Add highlight animation class to the DOM node
    nextTick(() => {
      const domNode = editor.value?.view.nodeDOM(targetPos) as HTMLElement
      if (domNode && domNode.classList) {
        domNode.classList.add('ui-highlight-anim')
        setTimeout(() => {
          domNode.classList.remove('ui-highlight-anim')
        }, 2000)
      }
    })
  }
}

watch(
  () => route.query.text,
  (newText) => {
    if (newText && typeof newText === 'string') {
      highlightText(newText)
    }
  }
)

onMounted(async () => {
  await documentStore.loadDocument()
  await documentStore.loadRecoveryCandidates()
  if (editor.value != null && documentStore.content !== null) {
    editor.value.commands.setContent(documentStore.content)
    
    if (route.query.text && typeof route.query.text === 'string') {
      nextTick(() => {
        highlightText(route.query.text as string)
      })
    }
  }
})

onBeforeUnmount(() => {
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

@media (max-width: 900px) {
  .ui-stream-recovery-panel {
    width: min(340px, calc(100vw - 52px));
  }
}
</style>
