<template>
  <div class="task-item" :class="{ completed: task.status === 'completed' }">
    <button 
      class="task-checkbox"
      :class="{ checked: task.status === 'completed' }"
      @click="toggleStatus"
    >
      <svg v-if="task.status === 'completed'" class="check-icon" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
    </button>
    
    <div class="task-content">
      <span class="task-text">{{ task.text }}</span>
      <span v-if="task.due_date" class="task-due">
        {{ formatDate(task.due_date) }}
      </span>
    </div>
    
    <button class="task-source" @click="goToSource" title="Go to source">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
        <polyline points="15 3 21 3 21 9"></polyline>
        <line x1="10" y1="14" x2="21" y2="3"></line>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import type { Task } from '@/types/task'

const props = defineProps<{
  task: Task
}>()

const router = useRouter()
const tasksStore = useTasksStore()

const toggleStatus = async () => {
  await tasksStore.toggleTaskStatus(props.task.id)
}

const goToSource = () => {
  router.push({ 
    path: '/stream', 
    query: { blockId: props.task.block_id }
  })
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  border-radius: 8px;
  background: var(--glass-surface);
  transition: background 0.15s ease;
}

.task-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.task-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid var(--border-default);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.task-checkbox:hover {
  border-color: var(--accent-primary);
}

.task-checkbox.checked {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

.check-icon {
  color: #000;
}

.task-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-text {
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--text-primary);
}

.task-item.completed .task-text {
  color: var(--text-tertiary);
  text-decoration: line-through;
}

.task-due {
  font-size: 12px;
  color: var(--text-secondary);
}

.task-source {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.2s ease;
}

.task-item:hover .task-source {
  opacity: 1;
}

.task-source:hover {
  color: var(--accent-primary);
  background: var(--accent-muted);
}
</style>
