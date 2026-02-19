<template>
  <aside 
    class="sidebar glass-container" 
    :class="{ expanded: isExpanded }"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="sidebar-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="sidebar-icon" v-html="item.icon"></span>
        <span class="sidebar-label">{{ item.label }}</span>
        <span v-if="item.badge && item.badge > 0" class="sidebar-badge">
          {{ item.badge }}
        </span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'

const route = useRoute()
const tasksStore = useTasksStore()

const isExpanded = ref(false)

const navItems = computed(() => [
  {
    path: '/stream',
    label: 'Stream',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10z"/><path d="M12 2v20"/></svg>'
  },
  {
    path: '/tasks',
    label: 'Tasks',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    badge: tasksStore.summary.pending_count
  }
])

const isActive = (path: string) => {
  return route.path === path
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width-collapsed);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
  border-right: 1px solid var(--border-subtle);
}

.sidebar.expanded {
  width: var(--sidebar-width-expanded);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 4px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  height: var(--sidebar-item-height);
  padding: 0 12px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.sidebar-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: var(--accent-muted);
  color: var(--accent-primary);
}

.sidebar-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent-primary);
  border-radius: 0 2px 2px 0;
}

.sidebar-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-label {
  margin-left: 12px;
  font-size: 14px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar.expanded .sidebar-label {
  opacity: 1;
}

.sidebar-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--accent-primary);
  color: #000;
  font-size: 11px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar.expanded .sidebar-badge {
  opacity: 1;
}
</style>
