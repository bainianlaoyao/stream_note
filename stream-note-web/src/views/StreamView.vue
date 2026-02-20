<template>
  <section class="ui-surface-card ui-card-pad-tight ui-stream-canvas">
    <EditorContent :editor="editor" class="ui-editor-surface" />

    <div class="ui-command-dock">
      <div class="ui-command-island">
        <button @click="runAIExtract" :disabled="isExtracting" class="ui-btn ui-btn-primary ui-command-btn">
          {{ isExtracting ? 'Analyzing...' : 'Analyze Current' }}
        </button>
        <button @click="analyzePending" :disabled="isAnalyzing" class="ui-btn ui-btn-ghost ui-command-btn">
          {{ isAnalyzing ? 'Processing...' : 'Analyze Pending (10)' }}
        </button>
        <button @click="resetAIState" :disabled="isResetting" class="ui-btn ui-btn-ghost ui-command-btn">
          {{ isResetting ? 'Resetting...' : 'Reset AI State' }}
        </button>
      </div>

      <div v-if="extractResult || analyzeResult || resetResult || errorMessage" class="ui-command-feedback">
        <p v-if="extractResult" class="ui-pill">Found {{ extractResult.tasks_found }} task(s)</p>
        <p v-if="analyzeResult" class="ui-pill">
          Analyzed {{ analyzeResult.analyzed_count }} block(s), {{ analyzeResult.tasks_found }} task(s)
        </p>
        <p v-if="resetResult" class="ui-pill">
          Reset {{ resetResult.deleted_tasks }} task(s), {{ resetResult.reset_blocks }} block(s)
        </p>
        <p v-if="errorMessage" class="ui-pill ui-pill-strong">{{ errorMessage }}</p>
      </div>
    </div>
  </section>
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
