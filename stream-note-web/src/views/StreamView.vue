<template>
  <div class="stream-view">
    <section class="stream-toolbar glass-panel">
      <div class="toolbar-head">
        <h1>Stream</h1>
        <p>Write naturally, then run AI analysis when needed.</p>
      </div>

      <div class="toolbar-actions">
        <button @click="runAIExtract" :disabled="isExtracting" class="glass-control action-btn primary">
          {{ isExtracting ? 'Analyzing...' : 'Analyze Current' }}
        </button>
        <button @click="analyzePending" :disabled="isAnalyzing" class="glass-control action-btn secondary">
          {{ isAnalyzing ? 'Processing...' : 'Analyze Pending (10)' }}
        </button>
        <button @click="resetAIState" :disabled="isResetting" class="glass-control action-btn ghost">
          {{ isResetting ? 'Resetting...' : 'Reset AI State' }}
        </button>
      </div>

      <div v-if="extractResult || analyzeResult || resetResult || errorMessage" class="toolbar-feedback">
        <p v-if="extractResult" class="feedback">Found {{ extractResult.tasks_found }} task(s)</p>
        <p v-if="analyzeResult" class="feedback">
          Analyzed {{ analyzeResult.analyzed_count }} block(s), {{ analyzeResult.tasks_found }} task(s)
        </p>
        <p v-if="resetResult" class="feedback">
          Reset {{ resetResult.deleted_tasks }} task(s), {{ resetResult.reset_blocks }} block(s)
        </p>
        <p v-if="errorMessage" class="feedback error">{{ errorMessage }}</p>
      </div>
    </section>

    <section class="editor-shell glass-panel">
      <header class="editor-header">
        <div class="editor-title-wrap">
          <h2>Document</h2>
          <p>Autosave On</p>
        </div>
        <span class="glass-chip">Live</span>
      </header>
      <EditorContent :editor="editor" class="editor" />
    </section>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import type { DocumentContent } from '@/types/document'
import { useDocumentStore } from '@/stores/document'
import { useTasksStore } from '@/stores/tasks'
import { useDebounceFn } from '@vueuse/core'
import {
  analyzePendingBlocks,
  extractTasksFromContent,
  resetDebugState,
  type AnalyzeResult,
  type ExtractResult,
  type ResetDebugStateResult
} from '@/services/api'

const documentStore = useDocumentStore()
const tasksStore = useTasksStore()

const isExtracting = ref(false)
const isAnalyzing = ref(false)
const isResetting = ref(false)
const extractResult = ref<ExtractResult | null>(null)
const analyzeResult = ref<AnalyzeResult | null>(null)
const resetResult = ref<ResetDebugStateResult | null>(null)
const errorMessage = ref<string | null>(null)

const debouncedSave = useDebounceFn(async (json: DocumentContent) => {
  await documentStore.saveDocument(json)
}, 500)

const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: 'Start writing... Try "todo: something" or "记得明天开会"'
    })
  ],
  content: '',
  onUpdate: ({ editor }) => {
    const json = editor.getJSON()
    documentStore.updateContent(json)
    debouncedSave(json)
  }
})

const runAIExtract = async () => {
  if (!editor.value) return

  isExtracting.value = true
  errorMessage.value = null
  analyzeResult.value = null
  resetResult.value = null
  try {
    const content = editor.value.getJSON()
    extractResult.value = await extractTasksFromContent(content)

    await tasksStore.loadTasks()
  } catch (error) {
    console.error('AI extract failed:', error)
    errorMessage.value = formatError(error)
  } finally {
    isExtracting.value = false
  }
}

const analyzePending = async () => {
  isAnalyzing.value = true
  errorMessage.value = null
  extractResult.value = null
  resetResult.value = null
  try {
    if (editor.value) {
      const content = editor.value.getJSON()
      documentStore.updateContent(content)
      await documentStore.saveDocument(content)
    }
    analyzeResult.value = await analyzePendingBlocks(true)
    await tasksStore.loadTasks()
  } catch (error) {
    console.error('Analyze pending failed:', error)
    errorMessage.value = formatError(error)
  } finally {
    isAnalyzing.value = false
  }
}

const resetAIState = async () => {
  isResetting.value = true
  errorMessage.value = null
  extractResult.value = null
  analyzeResult.value = null
  try {
    resetResult.value = await resetDebugState()
    await tasksStore.loadTasks()
  } catch (error) {
    console.error('Reset debug state failed:', error)
    errorMessage.value = formatError(error)
  } finally {
    isResetting.value = false
  }
}

const formatError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
    return `Request failed (${error.response?.status ?? 'network'})`
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Unknown error'
}

watch(() => documentStore.content, (newContent) => {
  if (editor.value && newContent) {
    const currentContent = editor.value.getJSON()
    if (JSON.stringify(currentContent) !== JSON.stringify(newContent)) {
      editor.value.commands.setContent(newContent)
    }
  }
}, { deep: true })

onMounted(async () => {
  await documentStore.loadDocument()
  if (editor.value && documentStore.content) {
    editor.value.commands.setContent(documentStore.content)
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.stream-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.stream-toolbar {
  padding: 16px;
}

.toolbar-head h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  color: var(--text-primary);
}

.toolbar-head p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.toolbar-actions {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-btn {
  min-height: 38px;
}

.action-btn.primary {
  border-color: var(--accent-main);
  background: var(--accent-main);
  color: #fff;
}

.action-btn.primary:hover:not(:disabled) {
  border-color: var(--accent-main-strong);
  background: var(--accent-main-strong);
}

.action-btn.secondary,
.action-btn.ghost {
  background: rgba(255, 255, 255, 0.72);
}

.toolbar-feedback {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feedback {
  margin: 0;
  padding: 5px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(79, 124, 255, 0.18);
  background: rgba(79, 124, 255, 0.08);
  color: var(--accent-main);
  font-size: 12px;
  font-weight: 600;
}

.feedback.error {
  border-color: rgba(79, 124, 255, 0.26);
  background: rgba(79, 124, 255, 0.12);
  color: var(--accent-main-strong);
}

.editor-shell {
  padding: 10px;
}

.editor-header {
  padding: 6px 8px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.editor-title-wrap h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
}

.editor-title-wrap p {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.editor {
  border-radius: var(--radius-md);
  border: 1px solid rgba(79, 124, 255, 0.12);
  background: rgba(255, 255, 255, 0.62);
  min-height: 56vh;
}

@media (max-width: 900px) {
  .stream-view {
    gap: 10px;
  }

  .stream-toolbar {
    padding: 13px;
  }

  .toolbar-head h1 {
    font-size: 24px;
  }

  .toolbar-head p {
    font-size: 13px;
  }

  .action-btn {
    flex: 1 1 calc(50% - 8px);
    justify-content: center;
    font-size: 12px;
    min-height: 36px;
    padding: 8px 10px;
  }

  .editor-header {
    padding: 4px 6px 8px;
  }

  .editor {
    min-height: 50vh;
  }
}
</style>
