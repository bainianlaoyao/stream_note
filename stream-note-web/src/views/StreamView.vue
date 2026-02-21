<template>
  <section class="ui-stream-shell">
    <EditorContent :editor="editor" class="ui-editor-surface" />
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { useDebounceFn } from '@vueuse/core'
import { useDocumentStore } from '@/stores/document'
import type { DocumentContent } from '@/types/document'
import { useI18n } from '@/composables/useI18n'

const documentStore = useDocumentStore()
const { t } = useI18n()

const debouncedSave = useDebounceFn(async (json: DocumentContent) => {
  await documentStore.saveDocument(json)
}, 500)

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

onMounted(async () => {
  await documentStore.loadDocument()
  if (editor.value != null && documentStore.content !== null) {
    editor.value.commands.setContent(documentStore.content)
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.ui-stream-shell {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
}

.ui-stream-shell :deep(.ui-editor-surface) {
  flex: 1 1 auto;
  min-height: 0;
}
</style>
