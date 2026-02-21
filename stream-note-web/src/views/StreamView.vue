<template>
  <EditorContent :editor="editor" class="ui-editor-surface" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { useDebounceFn } from '@vueuse/core'
import { useDocumentStore } from '@/stores/document'
import type { DocumentContent } from '@/types/document'

const documentStore = useDocumentStore()

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
