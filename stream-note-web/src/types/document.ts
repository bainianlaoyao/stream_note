import type { JSONContent } from '@tiptap/core'

export type DocumentContent = JSONContent

export interface Document {
  id: string
  content: DocumentContent
  created_at: string
  updated_at: string
}
