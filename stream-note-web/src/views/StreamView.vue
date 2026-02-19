<template>
  <div class="stream-view">
    <div class="debug-bar">
      <button @click="runAIExtract" :disabled="isExtracting" class="debug-btn">
        {{ isExtracting ? 'Analyzing...' : '🔍 Analyze Current' }}
      </button>
      <button @click="analyzePending" :disabled="isAnalyzing" class="debug-btn secondary">
        {{ isAnalyzing ? 'Processing...' : '📊 Analyze Pending (10)' }}
      </button>
      <button @click="resetAIState" :disabled="isResetting" class="debug-btn danger">
        {{ isResetting ? 'Resetting...' : '♻️ Reset AI State' }}
      </button>
      <span v-if="extractResult" class="extract-result">
        Found {{ extractResult.tasks_found }} task(s)
      </span>
      <span v-if="analyzeResult" class="extract-result">
        Analyzed {{ analyzeResult.analyzed_count }} block(s), {{ analyzeResult.tasks_found }} task(s)
      </span>
      <span v-if="resetResult" class="extract-result warning">
        Reset {{ resetResult.deleted_tasks }} task(s), {{ resetResult.reset_blocks }} block(s)
      </span>
    </div>
    <div class="stream-editor-container glass-container">
      <EditorContent :editor="editor" class="editor" />
    </div>
  </div>
</template>

<script setup lang="ts">
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
  analyzeResult.value = null
  resetResult.value = null
  try {
    const content = editor.value.getJSON()
    extractResult.value = await extractTasksFromContent(content)
    
    await tasksStore.loadTasks()
  } catch (error) {
    console.error('AI extract failed:', error)
  } finally {
    isExtracting.value = false
  }
}

const analyzePending = async () => {
  isAnalyzing.value = true
  extractResult.value = null
  resetResult.value = null
  try {
    analyzeResult.value = await analyzePendingBlocks()
    await tasksStore.loadTasks()
  } catch (error) {
    console.error('Analyze pending failed:', error)
  } finally {
    isAnalyzing.value = false
  }
}

const resetAIState = async () => {
  isResetting.value = true
  extractResult.value = null
  analyzeResult.value = null
  try {
    resetResult.value = await resetDebugState()
    await tasksStore.loadTasks()
  } catch (error) {
    console.error('Reset debug state failed:', error)
  } finally {
    isResetting.value = false
  }
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
  max-width: 720px;
  margin: 0 auto;
}

.debug-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.debug-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-default);
  background: var(--glass-surface);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.debug-btn.secondary {
  background: var(--accent-muted);
  border-color: var(--accent-primary);
}

.debug-btn.danger {
  border-color: var(--color-error);
  color: var(--color-error);
}

.debug-btn:hover:not(:disabled) {
  background: var(--accent-muted);
  border-color: var(--accent-primary);
}

.debug-btn.danger:hover:not(:disabled) {
  background: rgba(255, 69, 58, 0.12);
  border-color: var(--color-error);
}

.debug-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.extract-result {
  font-size: 13px;
  color: var(--accent-primary);
}

.extract-result.warning {
  color: var(--color-warning);
}

.stream-editor-container {
  border-radius: 16px;
  min-height: 60vh;
  overflow: hidden;
}

.editor {
  min-height: 60vh;
}
</style>
