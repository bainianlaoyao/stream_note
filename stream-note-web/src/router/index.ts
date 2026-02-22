import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import StreamView from '@/views/StreamView.vue'
import SearchView from '@/views/SearchView.vue'
import TasksView from '@/views/TasksView.vue'
import SettingsView from '@/views/SettingsView.vue'
import AuthView from '@/views/AuthView.vue'
import { useAuthStore } from '@/stores/auth'
import { pinia } from '@/stores/pinia'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/stream'
    },
    {
      path: '/auth',
      name: 'auth',
      component: AuthView
    },
    {
      path: '/stream',
      name: 'stream',
      component: StreamView,
      meta: { requiresAuth: true }
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TasksView,
      meta: { requiresAuth: true }
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to: RouteLocationNormalized) => {
  const authStore = useAuthStore(pinia)
  await authStore.initialize()

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth === true)
  if (requiresAuth && !authStore.isAuthenticated) {
    return { name: 'auth' }
  }

  if (to.name === 'auth' && authStore.isAuthenticated) {
    return { name: 'stream' }
  }

  return true
})

export default router
