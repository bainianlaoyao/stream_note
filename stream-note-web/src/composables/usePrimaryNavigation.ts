import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { useI18n } from '@/composables/useI18n'

interface PrimaryNavBaseItem {
  path: '/stream' | '/tasks' | '/search' | '/settings'
  labelKey: 'navStream' | 'navTasks' | 'navSearch' | 'navSettings'
  icon: string
}

export interface PrimaryNavItem {
  path: '/stream' | '/tasks' | '/search' | '/settings'
  label: string
  icon: string
  badge?: number
}

const PRIMARY_NAV_BASE_ITEMS: PrimaryNavBaseItem[] = [
  {
    path: '/stream',
    labelKey: 'navStream',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"/><path d="M4 7h16"/><path d="M4 17h11"/></svg>'
  },
  {
    path: '/tasks',
    labelKey: 'navTasks',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M8 10h8"/><path d="M8 14h8"/><path d="M8 18h5"/></svg>'
  },
  {
    path: '/search',
    labelKey: 'navSearch',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
  },
  {
    path: '/settings',
    labelKey: 'navSettings',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.36.64.93 1 1.51 1H21a2 2 0 1 1 0 4h-.09c-.58 0-1.15.36-1.51 1z"/></svg>'
  }
]

export const usePrimaryNavigation = () => {
  const route = useRoute()
  const tasksStore = useTasksStore()
  const { t } = useI18n()

  const navItems = computed<PrimaryNavItem[]>(() =>
    PRIMARY_NAV_BASE_ITEMS.map(item => {
      const translatedLabel = t(item.labelKey)
      if (item.path !== '/tasks') {
        return {
          path: item.path,
          label: translatedLabel,
          icon: item.icon
        }
      }

      return {
        path: item.path,
        label: translatedLabel,
        icon: item.icon,
        badge: tasksStore.summary.pending_count
      }
    })
  )

  const isActive = (path: PrimaryNavItem['path']): boolean => route.path === path

  const refreshSummary = () => {
    void tasksStore.loadSummary(false)
  }

  const handleVisibilityChange = () => {
    if (!document.hidden) {
      refreshSummary()
    }
  }

  onMounted(async () => {
    await tasksStore.loadSummary(false)
    tasksStore.startSummaryAutoRefresh()
    window.addEventListener('focus', refreshSummary)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })

  onBeforeUnmount(() => {
    tasksStore.stopSummaryAutoRefresh()
    window.removeEventListener('focus', refreshSummary)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })

  return {
    navItems,
    isActive
  }
}
