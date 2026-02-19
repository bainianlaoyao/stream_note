import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { DocumentContent } from '@/types/document'

export const useDocumentStore = defineStore('document', () => {
  const content = ref<DocumentContent | null>(null)
  const documentId = ref<string | null>(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const lastSaved = ref<Date | null>(null)

  const loadDocument = async () => {
    isLoading.value = true
    try {
      const doc = await api.getDocument()
      if (doc) {
        documentId.value = doc.id
        content.value = doc.content
      }
    } catch (error) {
      console.error('Failed to load document:', error)
    } finally {
      isLoading.value = false
    }
  }

  const updateContent = (newContent: DocumentContent) => {
    content.value = newContent
  }

  const saveDocument = async (newContent?: DocumentContent) => {
    const contentToSave = newContent ?? content.value
    if (contentToSave == null) return

    isSaving.value = true
    try {
      if (!documentId.value) {
        const doc = await api.createDocument()
        documentId.value = doc.id
      }

      await api.updateDocument(documentId.value, contentToSave)
      lastSaved.value = new Date()
    } catch (error) {
      console.error('Failed to save document:', error)
    } finally {
      isSaving.value = false
    }
  }

  return {
    content,
    documentId,
    isLoading,
    isSaving,
    lastSaved,
    loadDocument,
    updateContent,
    saveDocument
  }
})
