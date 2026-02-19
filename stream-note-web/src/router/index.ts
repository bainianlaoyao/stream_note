import { createRouter, createWebHistory } from 'vue-router'
import StreamView from '@/views/StreamView.vue'
import TasksView from '@/views/TasksView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/stream'
    },
    {
      path: '/stream',
      name: 'stream',
      component: StreamView
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TasksView
    }
  ]
})

export default router
