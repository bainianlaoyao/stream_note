<template>
  <nav class="ui-mobile-tabbar" :aria-label="t('navPrimary')">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      :class="[
        'ui-nav-item',
        'ui-mobile-tab-item',
        {
          'is-active': isActive(item.path),
          'has-badge': hasBadge(item.badge)
        }
      ]"
    >
      <span class="ui-mobile-tab-icon-wrap">
        <span class="ui-nav-icon ui-mobile-tab-icon" v-html="item.icon"></span>
        <span
          v-if="hasBadge(item.badge)"
          class="ui-nav-badge ui-mobile-tab-badge"
        >
          {{ item.badge }}
        </span>
      </span>
      <span class="ui-nav-label ui-mobile-tab-label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
import { usePrimaryNavigation } from '@/composables/usePrimaryNavigation'
import { useI18n } from '@/composables/useI18n'

const { navItems, isActive } = usePrimaryNavigation()
const { t } = useI18n()

const hasBadge = (badge?: number): boolean => typeof badge === 'number' && badge > 0
</script>
