export interface Task {
  id: string
  block_id: string
  text: string
  status: 'pending' | 'completed'
  due_date: string | null
  raw_time_expr: string | null
  created_at: string
}
