<template>
  <div class="app-shell">
    <Sidebar />
    <main class="page-shell">
      <router-view v-slot="{ Component }">
        <transition name="view" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
</script>

<style scoped>
.app-shell {
  width: min(var(--shell-max-width), calc(100vw - 34px));
  margin: 0 auto;
  min-height: 100vh;
  padding: 18px 0;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  gap: 16px;
}

.page-shell {
  min-width: 0;
  padding: 8px 6px 8px 0;
}

.view-enter-active,
.view-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.view-enter-from,
.view-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 900px) {
  .app-shell {
    width: calc(100vw - 18px);
    padding: 9px 0;
    grid-template-columns: var(--sidebar-width-compact) minmax(0, 1fr);
    gap: 10px;
  }

  .page-shell {
    padding: 0;
  }
}
</style>
