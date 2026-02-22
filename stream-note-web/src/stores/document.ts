import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { DocumentContent, DocumentRecoveryCandidate } from '@/types/document'
import localforage from 'localforage'

const LOCAL_DOC_KEY = 'stream_note_local_document'

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
      // 1. Try to load from local storage first (Offline-First)
      const localDoc = await localforage.getItem<DocumentContent>(LOCAL_DOC_KEY)
      if (localDoc) {
        content.value = localDoc
      }

      // 2. Fetch from server
      const doc = await api.getDocument()
      if (doc) {
        documentId.value = doc.id
        // Only overwrite if server has newer content or local is empty
        // For a true offline-first, we'd need a timestamp comparison.
        // For now, we'll just update local with server if we didn't have local,
        // or we'll let the next save sync local to server.
        if (!localDoc) {
          content.value = doc.content
          await localforage.setItem(LOCAL_DOC_KEY, doc.content)
        }
      }
    } catch (error) {
      console.error('Failed to load document:', error)
    } finally {
      isLoading.value = false
    }
  }

  const updateContent = (newContent: DocumentContent) => {
    content.value = newContent
    // Save to local immediately on update
    localforage.setItem(LOCAL_DOC_KEY, newContent).catch(console.error)
  }

  const saveDocument = async (newContent?: DocumentContent) => {
    const contentToSave = newContent ?? content.value
    if (contentToSave == null) return

    isSaving.value = true
    try {
      // Save to local first
      await localforage.setItem(LOCAL_DOC_KEY, contentToSave)
      
      // Then sync to server
      const doc = await api.upsertCurrentDocument(contentToSave)
      documentId.value = doc.id
      lastSaved.value = new Date()
    } catch (error) {
      console.error('Failed to save document to server (saved locally):', error)
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
