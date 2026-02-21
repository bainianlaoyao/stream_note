import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { DocumentContent, DocumentRecoveryCandidate } from '@/types/document'

export const useDocumentStore = defineStore('document', () => {
  const content = ref<DocumentContent | null>(null)
  const documentId = ref<string | null>(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const lastSaved = ref<Date | null>(null)
  const recoveryCandidates = ref<DocumentRecoveryCandidate[]>([])
  const isLoadingRecovery = ref(false)
  const isRestoring = ref(false)
  const recoveryError = ref<string | null>(null)
  const undoRevisionId = ref<string | null>(null)

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
      const doc = await api.upsertCurrentDocument(contentToSave)
      documentId.value = doc.id
      lastSaved.value = new Date()
    } catch (error) {
      console.error('Failed to save document:', error)
    } finally {
      isSaving.value = false
    }
  }

  const loadRecoveryCandidates = async () => {
    isLoadingRecovery.value = true
    recoveryError.value = null
    try {
      recoveryCandidates.value = await api.getDocumentRecoveryCandidates()
    } catch (error) {
      recoveryError.value = 'load_candidates_failed'
      console.error('Failed to load recovery candidates:', error)
    } finally {
      isLoadingRecovery.value = false
    }
  }

  const restoreFromRevision = async (revisionId: string) => {
    isRestoring.value = true
    recoveryError.value = null
    try {
      const result = await api.restoreDocumentRecoveryRevision(revisionId)
      documentId.value = result.document.id
      content.value = result.document.content
      lastSaved.value = new Date()
      undoRevisionId.value = result.undo_revision_id
      await loadRecoveryCandidates()
      return result
    } catch (error) {
      recoveryError.value = 'restore_failed'
      console.error('Failed to restore recovery revision:', error)
      throw error
    } finally {
      isRestoring.value = false
    }
  }

  const undoLastRestore = async () => {
    if (undoRevisionId.value == null) {
      return
    }
    const revisionId = undoRevisionId.value
    await restoreFromRevision(revisionId)
  }

  return {
    content,
    documentId,
    isLoading,
    isSaving,
    lastSaved,
    recoveryCandidates,
    isLoadingRecovery,
    isRestoring,
    recoveryError,
    undoRevisionId,
    loadDocument,
    updateContent,
    saveDocument,
    loadRecoveryCandidates,
    restoreFromRevision,
    undoLastRestore
  }
})
