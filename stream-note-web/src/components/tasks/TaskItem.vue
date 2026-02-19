<template>
  <div class="task-card" :class="{ completed: task.status === 'completed' }">
    <button
      class="task-check"
      :class="{ checked: task.status === 'completed' }"
      :aria-label="task.status === 'completed' ? 'Mark task pending' : 'Mark task completed'"
      @click="toggleStatus"
    >
      <svg
        v-if="task.status === 'completed'"
        class="check-icon"
        xmlns="http://www.w3.org/2000/svg"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
    </button>

    <div class="task-body">
      <p class="task-text">{{ task.text }}</p>
      <div class="task-meta">
        <span v-if="task.due_date" class="meta-pill">{{ formatDate(task.due_date) }}</span>
        <span class="meta-pill">Block {{ shortBlockId(task.block_id) }}</span>
      </div>
    </div>

    <button class="task-source glass-control" @click="goToSource" title="Go to source">
      Source
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

const shortBlockId = (blockId: string): string => {
  if (blockId.length <= 8) {
    return blockId
  }
  return blockId.slice(0, 8)
}

const formatDate = (dateStr: string): string => {
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
.task-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255, 255, 255, 0.86);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--glass-shadow-md);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.task-card:hover {
  border-color: rgba(79, 124, 255, 0.24);
  transform: translateY(-1px);
}

.task-check {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  border: 1px solid rgba(79, 124, 255, 0.24);
  background: rgba(255, 255, 255, 0.82);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.task-check:hover {
  border-color: var(--accent-main);
}

.task-check.checked {
  border-color: var(--accent-main);
  background: var(--accent-main);
}

.check-icon {
  width: 11px;
  height: 11px;
}

.task-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-text {
  margin: 0;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.44;
  word-break: break-word;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-pill {
  min-height: 22px;
  padding: 0 8px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(79, 124, 255, 0.16);
  background: rgba(79, 124, 255, 0.08);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
}

.task-source {
  min-height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.8);
}

.task-card.completed .task-text {
  color: var(--text-muted);
  text-decoration: line-through;
}

@media (max-width: 900px) {
  .task-card {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      'check body'
      'source source';
    gap: 10px;
  }

  .task-check {
    grid-area: check;
    align-self: start;
    margin-top: 1px;
  }

  .task-body {
    grid-area: body;
  }

  .task-source {
    grid-area: source;
    width: 100%;
    justify-content: center;
  }

  .task-text {
    font-size: 13px;
  }
}
</style>
