import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/services/api'
import type { Task, TaskSummary } from '@/types/task'

const EMPTY_SUMMARY: TaskSummary = {
  pending_count: 0,
  completed_count: 0,
  total_count: 0
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const summary = ref<TaskSummary>(EMPTY_SUMMARY)
  const isLoading = ref(false)

  const loadTasks = async () => {
    isLoading.value = true
    try {
      const [taskResult, summaryResult] = await Promise.all([
        api.getTasks(),
        api.getTasksSummary()
      ])
      tasks.value = taskResult
      summary.value = summaryResult
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      isLoading.value = false
    }
  }

  const toggleTaskStatus = async (taskId: string) => {
    try {
      const result = await api.toggleTaskCommand(taskId)
      const taskIndex = tasks.value.findIndex(t => t.id === taskId)
      if (taskIndex >= 0) {
        tasks.value[taskIndex] = result.task
      } else {
        tasks.value.push(result.task)
      }
      summary.value = result.summary
    } catch (error) {
      console.error('Failed to update task status:', error)
    }
  }

  return {
    tasks,
    summary,
    isLoading,
    loadTasks,
    toggleTaskStatus
  }
})
