import axios from 'axios'
import type { Document, DocumentContent } from '@/types/document'
import type { Task, TaskSummary } from '@/types/task'

const AUTH_TOKEN_KEY = 'stream-note-auth-token'
const DEFAULT_API_BASE_URL = '/api/v1'

const resolveApiBaseURL = (): string => {
  const envBaseURL = import.meta.env.VITE_API_BASE_URL
  if (typeof envBaseURL !== 'string' || envBaseURL.trim() === '') {
    return DEFAULT_API_BASE_URL
  }

  return envBaseURL.trim().replace(/\/+$/, '')
}

const apiClient = axios.create({
  baseURL: resolveApiBaseURL(),
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface AuthUser {
  id: string
  username: string
  created_at: string
}

export interface AuthCredentialsPayload {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  user: AuthUser
}

export const getStoredAuthToken = (): string | null => window.localStorage.getItem(AUTH_TOKEN_KEY)

export const saveAuthToken = (token: string): void => {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token)
}

export const clearAuthToken = (): void => {
  window.localStorage.removeItem(AUTH_TOKEN_KEY)
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredAuthToken()
  if (token && config.headers !== undefined) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  response => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearAuthToken()
    }
    return Promise.reject(error)
  }
)

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

export async function registerAccount(payload: AuthCredentialsPayload): Promise<AuthResponse> {
  const response = await apiClient.post('/auth/register', payload)
  return response.data
}

export async function loginAccount(payload: AuthCredentialsPayload): Promise<AuthResponse> {
  const response = await apiClient.post('/auth/login', payload)
  return response.data
}

export async function getCurrentAccount(): Promise<AuthUser> {
  const response = await apiClient.get('/auth/me')
  return response.data
}

export async function upsertCurrentDocument(content: DocumentContent): Promise<Document> {
  const response = await apiClient.put('/documents/current', { content })
  return response.data
}

export interface TasksQueryOptions {
  includeHidden?: boolean
}

const toTaskQueryParams = (options?: TasksQueryOptions): { include_hidden?: boolean } => ({
  include_hidden: options?.includeHidden === true ? true : undefined
})

export async function getTasks(options?: TasksQueryOptions): Promise<Task[]> {
  const response = await apiClient.get('/tasks', {
    params: toTaskQueryParams(options)
  })
  return response.data
}

export async function getTasksSummary(options?: TasksQueryOptions): Promise<TaskSummary> {
  const response = await apiClient.get('/tasks/summary', {
    params: toTaskQueryParams(options)
  })
  return response.data
}

export interface ToggleTaskCommandResult {
  task: Task
  summary: TaskSummary
}

export async function toggleTaskCommand(
  taskId: string,
  options?: TasksQueryOptions
): Promise<ToggleTaskCommandResult> {
  const response = await apiClient.post(`/tasks/${taskId}/commands/toggle`, null, {
    params: toTaskQueryParams(options)
  })
  return response.data
}

export interface DeleteTaskCommandResult {
  deleted_task_id: string
  summary: TaskSummary
}

export async function deleteTaskCommand(
  taskId: string,
  options?: TasksQueryOptions
): Promise<DeleteTaskCommandResult> {
  const response = await apiClient.delete(`/tasks/${taskId}`, {
    params: toTaskQueryParams(options)
  })
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
