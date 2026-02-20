<template>
  <aside class="ui-sidebar-surface">
    <div class="ui-sidebar-brand">
      <span aria-hidden="true" class="ui-sidebar-brand-dot"></span>
      <div class="ui-sidebar-brand-copy">
        <strong class="ui-sidebar-brand-title">Stream Note</strong>
      </div>
    </div>

    <div aria-hidden="true" class="ui-sidebar-divider"></div>

    <nav class="ui-sidebar-nav" aria-label="Primary">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="['ui-nav-item', { 'is-active': isActive(item.path) }]"
      >
        <span class="ui-nav-icon" v-html="item.icon"></span>
        <span class="ui-nav-label">{{ item.label }}</span>
        <span
          v-if="item.badge && item.badge > 0"
          class="ui-nav-badge"
        >
          {{ item.badge }}
        </span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const tasksStore = useTasksStore()

const navItems = computed(() => [
  {
    path: '/stream',
    label: 'Stream',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/><path d="M4 7h16"/><path d="M4 17h11"/></svg>'
  },
  {
    path: '/tasks',
    label: 'Tasks',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M8 10h8"/><path d="M8 14h8"/><path d="M8 18h5"/></svg>',
    badge: tasksStore.summary.pending_count
  }
])

const isActive = (path: string): boolean => route.path === path

onMounted(async () => {
  await tasksStore.loadSummary()
})
</script>
