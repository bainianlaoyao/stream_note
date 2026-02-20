<template>
  <section v-if="tasksStore.tasks.length > 0" class="ui-list-stack">
    <TaskItem
      v-for="task in tasksStore.tasks"
      :key="task.id"
      :task="task"
    />
  </section>

  <section v-else class="ui-surface-card ui-empty-state">
    <h2 class="ui-heading ui-heading-lg">No tasks yet</h2>
    <p class="ui-body ui-body-sm ui-empty-description">Create some notes in Stream and run analysis.</p>
  </section>
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
