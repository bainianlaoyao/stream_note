<template>
  <div class="ui-stage">
    <div aria-hidden="true" class="ui-ambient-orb ui-ambient-orb-a"></div>
    <div aria-hidden="true" class="ui-ambient-orb ui-ambient-orb-b"></div>

    <div class="ui-shell">
      <Sidebar />
      <main class="ui-main">
        <div class="ui-main-layer" :class="{ 'is-overlay-mode': !isStreamRoute }">
          <div class="ui-stream-host">
            <StreamView />
          </div>

          <router-view v-slot="{ Component }">
            <transition name="overlay" mode="out-in">
              <div v-if="!isStreamRoute && Component" :key="route.fullPath" class="ui-overlay-pane">
                <component :is="Component" />
              </div>
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import StreamView from '@/views/StreamView.vue'

const route = useRoute()

const isStreamRoute = computed(() => route.path === '/stream')
</script>

<style scoped>
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease, filter 0.24s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.995);
  filter: blur(clamp(0px, calc(var(--overlay-blur) - 1px), 999px));
}
</style>
