<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-content">
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
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-base);
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width-collapsed);
  padding: 32px;
  transition: margin-left 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.view-enter-active,
.view-leave-active {
  transition: opacity 0.3s ease;
}

.view-enter-from,
.view-leave-to {
  opacity: 0;
}
</style>
