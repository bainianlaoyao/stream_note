import axios from 'axios'
import type { Document, DocumentContent } from '@/types/document'
import type { Task, TaskSummary } from '@/types/task'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

export type AIProvider = 'openai_compatible' | 'openai' | 'ollama' | 'siliconflow'

export interface AIProviderSettingsPayload {
  provider: AIProvider
  api_base: string
  api_key: string
  model: string
  timeout_seconds: number
  max_attempts: number
  disable_thinking: boolean
}

export interface AIProviderSettings extends AIProviderSettingsPayload {
  supported_providers: AIProvider[]
  updated_at: string | null
}

export interface AIProviderTestResult {
  ok: boolean
  latency_ms: number
  message: string
}

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

export async function upsertCurrentDocument(content: DocumentContent): Promise<Document> {
  const response = await apiClient.put('/documents/current', { content })
  return response.data
}

export async function getTasks(): Promise<Task[]> {
  const response = await apiClient.get('/tasks')
  return response.data
}

export async function getTasksSummary(): Promise<TaskSummary> {
  const response = await apiClient.get('/tasks/summary')
  return response.data
}

export interface ToggleTaskCommandResult {
  task: Task
  summary: TaskSummary
}

export async function toggleTaskCommand(taskId: string): Promise<ToggleTaskCommandResult> {
  const response = await apiClient.post(`/tasks/${taskId}/commands/toggle`)
  return response.data
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

export async function analyzePendingBlocks(force = false): Promise<AnalyzeResult> {
  const response = await apiClient.post('/ai/analyze-pending', null, {
    params: { force }
  })
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

export async function getAIProviderSettings(): Promise<AIProviderSettings> {
  const response = await apiClient.get('/ai/provider-settings')
  return response.data
}

export async function updateAIProviderSettings(
  payload: AIProviderSettingsPayload
): Promise<AIProviderSettings> {
  const response = await apiClient.put('/ai/provider-settings', payload)
  return response.data
}

export async function testAIProviderSettings(
  payload: AIProviderSettingsPayload
): Promise<AIProviderTestResult> {
  const response = await apiClient.post('/ai/provider-settings/test', payload)
  return response.data
}
