export type TaskStatus = 'pending' | 'completed'

export interface Task {
  id: string
  block_id: string
  text: string
  status: TaskStatus
  due_date: string | null
  raw_time_expr: string | null
  created_at: string
}

export interface TaskSummary {
  pending_count: number
  completed_count: number
  total_count: number
}
