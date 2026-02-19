<template>
  <div class="tasks-view">
    <header class="tasks-head glass-panel">
      <div>
        <h1>Tasks</h1>
        <p>Items extracted from your stream notes.</p>
      </div>
      <span class="count-chip">{{ tasksStore.summary.pending_count }} pending</span>
    </header>

    <section v-if="tasksStore.tasks.length > 0" class="tasks-list">
      <TaskItem
        v-for="task in tasksStore.tasks"
        :key="task.id"
        :task="task"
      />
    </section>

    <section v-else class="tasks-empty glass-panel">
      <h2>No tasks yet</h2>
      <p>Create some notes in Stream and run analysis.</p>
    </section>
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
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-head {
  padding: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.tasks-head h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
}

.tasks-head p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.count-chip {
  min-height: 28px;
  padding: 0 10px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(79, 124, 255, 0.2);
  background: rgba(79, 124, 255, 0.12);
  color: var(--accent-main);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  display: inline-flex;
  align-items: center;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tasks-empty {
  text-align: center;
  padding: 38px 18px;
}

.tasks-empty h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 23px;
}

.tasks-empty p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

@media (max-width: 900px) {
  .tasks-head {
    padding: 12px;
    flex-direction: column;
    align-items: flex-start;
  }

  .tasks-head h1 {
    font-size: 24px;
  }

  .tasks-head p {
    font-size: 13px;
  }

  .count-chip {
    min-height: 26px;
    font-size: 11px;
  }

  .tasks-empty {
    padding: 30px 14px;
  }
}
</style>
