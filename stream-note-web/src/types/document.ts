import type { JSONContent } from '@tiptap/core'

export type DocumentContent = JSONContent

export interface Document {
  id: string
  content: DocumentContent
  created_at: string
  updated_at: string
}

export type DocumentRecoveryKind = 'latest' | 'yesterday' | 'stable'

export interface DocumentRecoveryCandidate {
  id: string
  kind: DocumentRecoveryKind
  created_at: string
  char_count: number
  revision_no: number
  reason: string
}

export interface DocumentRecoveryCandidatesResponse {
  candidates: DocumentRecoveryCandidate[]
}

export interface DocumentRecoveryRestoreResult {
  document: Document
  restored_revision_id: string | null
  undo_revision_id: string | null
}
