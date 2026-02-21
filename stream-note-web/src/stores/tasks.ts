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
  const isSummaryLoading = ref(false)
  const showHiddenTasks = ref(false)
  const summaryPollTimer = ref<ReturnType<typeof setInterval> | null>(null)

  const loadSummary = async (includeHidden = showHiddenTasks.value) => {
    if (isSummaryLoading.value) {
      return
    }

    isSummaryLoading.value = true
    try {
      summary.value = await api.getTasksSummary({ includeHidden })
    } catch (error) {
      console.error('Failed to load task summary:', error)
    } finally {
      isSummaryLoading.value = false
    }
  }

  const loadTasks = async (includeHidden = showHiddenTasks.value) => {
    isLoading.value = true
    showHiddenTasks.value = includeHidden
    try {
      const [taskResult, summaryResult] = await Promise.all([
        api.getTasks({ includeHidden }),
        api.getTasksSummary({ includeHidden })
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
      const result = await api.toggleTaskCommand(taskId, {
        includeHidden: showHiddenTasks.value
      })
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

  const deleteTask = async (taskId: string) => {
    const result = await api.deleteTaskCommand(taskId, {
      includeHidden: showHiddenTasks.value
    })

    tasks.value = tasks.value.filter(task => task.id !== taskId)
    summary.value = result.summary

    // Keep local list consistent with server-side visibility rules.
    await loadTasks(showHiddenTasks.value)
  }

  const setShowHiddenTasks = async (value: boolean) => {
    await loadTasks(value)
  }

  const startSummaryAutoRefresh = (intervalMs = 10000) => {
    if (summaryPollTimer.value != null) {
      return
    }

    summaryPollTimer.value = setInterval(() => {
      void loadSummary(false)
    }, intervalMs)
  }

  const stopSummaryAutoRefresh = () => {
    if (summaryPollTimer.value == null) {
      return
    }

    clearInterval(summaryPollTimer.value)
    summaryPollTimer.value = null
  }

  return {
    tasks,
    summary,
    isLoading,
    isSummaryLoading,
    showHiddenTasks,
    loadSummary,
    loadTasks,
    toggleTaskStatus,
    deleteTask,
    setShowHiddenTasks,
    startSummaryAutoRefresh,
    stopSummaryAutoRefresh
  }
})
