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
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.36.64.93 1 1.51 1H21a2 2 0 1 1 0 4h-.09c-.58 0-1.15.36-1.51 1z"/></svg>'
  }
])

const isActive = (path: string): boolean => route.path === path

onMounted(async () => {
  await tasksStore.loadSummary()
})
</script>
