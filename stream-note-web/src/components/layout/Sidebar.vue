<template>
  <aside class="sidebar glass-panel">
    <div class="brand">
      <span class="brand-dot" aria-hidden="true"></span>
      <div class="brand-copy">
        <strong>Stream Note</strong>
        <small>Workspace</small>
      </div>
    </div>

    <nav class="nav-list" aria-label="Primary">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge && item.badge > 0" class="nav-badge">{{ item.badge }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 18px;
  height: calc(100vh - 36px);
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
}

.brand-dot {
  width: 28px;
  height: 28px;
  border-radius: 9px;
  background: linear-gradient(140deg, var(--accent-main), rgba(79, 124, 255, 0.62));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68);
}

.brand-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-copy strong {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.brand-copy small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  min-height: 42px;
  gap: 10px;
  padding: 0 10px;
  border-radius: 12px;
  border: 1px solid transparent;
  text-decoration: none;
  color: var(--text-secondary);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  color: var(--text-primary);
  border-color: rgba(79, 124, 255, 0.18);
  background: rgba(255, 255, 255, 0.5);
}

.nav-item.active {
  color: var(--accent-main);
  border-color: rgba(79, 124, 255, 0.34);
  background: rgba(79, 124, 255, 0.1);
}

.nav-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-label {
  font-size: 13px;
  font-weight: 600;
}

.nav-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  border-radius: var(--radius-pill);
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: var(--accent-main);
}

@media (max-width: 900px) {
  .sidebar {
    top: 9px;
    height: calc(100vh - 18px);
    padding: 12px 10px;
  }

  .brand {
    justify-content: center;
    padding: 6px 0;
  }

  .brand-copy {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 0;
    min-height: 40px;
  }

  .nav-label,
  .nav-badge {
    display: none;
  }
}
</style>
