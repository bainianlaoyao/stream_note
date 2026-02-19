import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/services/api'
import type { Task } from '@/types/task'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const isLoading = ref(false)

  const pendingCount = computed(() => 
    tasks.value.filter(t => t.status === 'pending').length
  )

  const loadTasks = async () => {
    isLoading.value = true
    try {
      const result = await api.getTasks()
      tasks.value = result
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      isLoading.value = false
    }
  }

  const toggleTaskStatus = async (taskId: string) => {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task) return

    const newStatus = task.status === 'completed' ? 'pending' : 'completed'
    
    try {
      await api.updateTaskStatus(taskId, newStatus)
      task.status = newStatus
      
      await api.updateBlockCompleted(task.block_id, newStatus === 'completed')
    } catch (error) {
      console.error('Failed to update task status:', error)
    }
  }

  return {
    tasks,
    isLoading,
    pendingCount,
    loadTasks,
    toggleTaskStatus
  }
})
