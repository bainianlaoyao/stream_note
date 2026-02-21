<template>
  <router-view v-if="isAuthRoute" />

  <div v-else-if="isMobile" class="ui-stage ui-stage-mobile">
    <div aria-hidden="true" class="ui-ambient-orb ui-ambient-orb-a"></div>
    <div aria-hidden="true" class="ui-ambient-orb ui-ambient-orb-b"></div>

    <div class="ui-mobile-shell">
      <header class="ui-mobile-topbar">
        <div class="ui-mobile-brand">
          <span aria-hidden="true" class="ui-sidebar-brand-dot"></span>
          <div class="ui-mobile-brand-copy">
            <strong class="ui-mobile-brand-title">Stream Note</strong>
            <span class="ui-mobile-brand-subtitle">{{ mobilePageTitle }}</span>
          </div>
        </div>
      </header>

      <main class="ui-main ui-mobile-main">
        <div class="ui-main-layer" :class="{ 'is-overlay-mode': !isStreamRoute }">
          <div class="ui-stream-host">
            <StreamView />
          </div>

          <router-view v-slot="{ Component }">
            <transition name="overlay" mode="out-in">
              <div
                v-if="!isStreamRoute && Component"
                :key="route.fullPath"
                class="ui-overlay-pane ui-overlay-pane-mobile"
              >
                <component :is="Component" />
              </div>
            </transition>
          </router-view>
        </div>
      </main>

      <MobileTabbar />
    </div>
  </div>

  <div v-else class="ui-stage">
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import MobileTabbar from '@/components/layout/MobileTabbar.vue'
import StreamView from '@/views/StreamView.vue'
import { useI18n } from '@/composables/useI18n'

const route = useRoute()
const { t } = useI18n()
const mobileMediaQuery = '(max-width: 900px)'
const isMobile = ref(
  typeof window !== 'undefined' ? window.matchMedia(mobileMediaQuery).matches : false
)
let mobileMediaQueryList: MediaQueryList | null = null

const handleViewportChange = (event: MediaQueryListEvent) => {
  isMobile.value = event.matches
}

onMounted(() => {
  mobileMediaQueryList = window.matchMedia(mobileMediaQuery)
  isMobile.value = mobileMediaQueryList.matches
  mobileMediaQueryList.addEventListener('change', handleViewportChange)
})

onBeforeUnmount(() => {
  mobileMediaQueryList?.removeEventListener('change', handleViewportChange)
})

const isStreamRoute = computed(() => route.path === '/stream')
const isAuthRoute = computed(() => route.path === '/auth')
const mobilePageTitle = computed(() => {
  if (route.path === '/tasks') {
    return t('appMobileTitleTasks')
  }

  if (route.path === '/settings') {
    return t('appMobileTitleSettings')
  }

  return t('appMobileTitleStream')
})
</script>

<style scoped>
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease, filter 0.24s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
  transform: translateY(10px);
  filter: blur(clamp(0px, calc(var(--overlay-blur) - 1px), 999px));
}
</style>
