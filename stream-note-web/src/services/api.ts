import axios from 'axios'
import type { Document, DocumentContent } from '@/types/document'
import type { Task } from '@/types/task'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

export async function getDocument(): Promise<Document | null> {
  try {
    const response = await apiClient.get('/documents')
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

export async function createDocument(): Promise<Document> {
  const response = await apiClient.post('/documents', {
    content: { type: 'doc', content: [] }
  })
  return response.data
}

export async function updateDocument(id: string, content: DocumentContent): Promise<Document> {
  const response = await apiClient.patch(`/documents/${id}`, { content })
  return response.data
}

export async function getTasks(): Promise<Task[]> {
  const response = await apiClient.get('/tasks')
  return response.data
}

export async function updateTaskStatus(taskId: string, status: string): Promise<Task> {
  const response = await apiClient.patch(`/tasks/${taskId}`, { status })
  return response.data
}

export async function updateBlockCompleted(blockId: string, isCompleted: boolean): Promise<void> {
  await apiClient.patch(`/blocks/${blockId}`, { is_completed: isCompleted })
}

export interface ExtractResult {
  tasks_found: number
  tasks: Array<{
    text: string
    due_date: string | null
    time_expr: string | null
  }>
}

export async function extractTasksFromContent(content: DocumentContent): Promise<ExtractResult> {
  const response = await apiClient.post('/ai/extract', { content })
  return response.data
}

export interface AnalyzeResult {
  analyzed_count: number
  tasks_found: number
  tasks: Array<{
    text: string
    due_date: string | null
    time_expr: string | null
    block_content: string
  }>
}

export async function analyzePendingBlocks(): Promise<AnalyzeResult> {
  const response = await apiClient.post('/ai/analyze-pending')
  return response.data
}

export interface ResetDebugStateResult {
  deleted_tasks: number
  reset_blocks: number
}

export async function resetDebugState(): Promise<ResetDebugStateResult> {
  const response = await apiClient.post('/ai/reset-debug-state')
  return response.data
}
