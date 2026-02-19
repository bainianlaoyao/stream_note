<template>
  <div class="tasks-view">
    <header class="tasks-header">
      <h1 class="title">Tasks</h1>
      <span class="count">{{ tasksStore.pendingCount }} pending</span>
    </header>
    
    <div class="tasks-list" v-if="tasksStore.tasks.length > 0">
      <TaskItem 
        v-for="task in tasksStore.tasks" 
        :key="task.id" 
        :task="task"
      />
    </div>
    
    <div class="empty-state" v-else>
      <p>No tasks yet. Start writing in Stream!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import TaskItem from '@/components/tasks/TaskItem.vue'

const tasksStore = useTasksStore()

onMounted(async () => {
  await tasksStore.loadTasks()
})
</script>

<style scoped>
.tasks-view {
  max-width: 640px;
  margin: 0 auto;
}

.tasks-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.title {
  font-family: var(--font-sans);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.count {
  font-size: 14px;
  color: var(--text-secondary);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--text-tertiary);
}
</style>
