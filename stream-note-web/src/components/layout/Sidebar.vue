<template>
  <aside class="ui-sidebar-surface">
    <div class="ui-sidebar-brand">
      <span aria-hidden="true" class="ui-sidebar-brand-dot"></span>
      <div class="ui-sidebar-brand-copy">
        <strong class="ui-sidebar-brand-title">Stream Note</strong>
      </div>
    </div>

    <div aria-hidden="true" class="ui-sidebar-divider"></div>

    <nav class="ui-sidebar-nav" :aria-label="t('navPrimary')">
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
import { usePrimaryNavigation } from '@/composables/usePrimaryNavigation'
import { useI18n } from '@/composables/useI18n'

const { navItems, isActive } = usePrimaryNavigation()
const { t } = useI18n()
</script>
