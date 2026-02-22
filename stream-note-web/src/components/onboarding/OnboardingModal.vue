<template>
  <Teleport to="body">
    <Transition name="onboarding">
      <div v-if="isVisible" class="onboarding-backdrop" role="dialog" :aria-label="t('onboardingAriaLabel')">
        <div class="onboarding-glass">
          <div class="onboarding-content">
            <template v-if="currentStep === 1">
              <div class="onboarding-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <h2 class="onboarding-title">{{ t('onboardingWelcomeTitle') }}</h2>
              <p class="onboarding-desc">{{ t('onboardingWelcomeDesc') }}</p>
            </template>
            
            <template v-else-if="currentStep === 2">
              <div class="onboarding-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </div>
              <h2 class="onboarding-title">{{ t('onboardingStreamTitle') }}</h2>
              <p class="onboarding-desc">{{ t('onboardingStreamDesc') }}</p>
            </template>
            
            <template v-else-if="currentStep === 3">
              <div class="onboarding-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 11l3 3L22 4"/>
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
              </div>
              <h2 class="onboarding-title">{{ t('onboardingTasksTitle') }}</h2>
              <p class="onboarding-desc">{{ t('onboardingTasksDesc') }}</p>
            </template>
            
            <div class="onboarding-footer">
              <button type="button" class="onboarding-btn onboarding-btn-skip" @click="skip">
                {{ t('onboardingSkip') }}
              </button>
              
              <div class="onboarding-dots" role="tablist" aria-label="Onboarding steps">
                <span 
                  v-for="i in 3" 
                  :key="i" 
                  class="onboarding-dot" 
                  :class="{ 'is-active': i === currentStep }"
                  role="tab"
                  :aria-selected="i === currentStep"
                  :aria-label="`Step ${i}`"
                />
              </div>
              
              <div class="onboarding-nav">
                <button v-if="currentStep > 1" type="button" class="onboarding-btn onboarding-btn-secondary" @click="prev">
                  {{ t('onboardingPrev') }}
                </button>
                <button v-if="currentStep < 3" type="button" class="onboarding-btn onboarding-btn-primary" @click="next">
                  {{ t('onboardingNext') }}
                </button>
                <button v-else type="button" class="onboarding-btn onboarding-btn-primary" @click="complete">
                  {{ t('onboardingDone') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { useOnboarding } from '@/composables/useOnboarding'
import { useI18n } from '@/composables/useI18n'


const { currentStep, isVisible, next, prev, skip, complete } = useOnboarding()
const { t } = useI18n()
</script>

<style scoped>
.onboarding-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background-color: rgba(41, 37, 36, 0.08);
  backdrop-filter: blur(12px) saturate(120%);
  -webkit-backdrop-filter: blur(12px) saturate(120%);
}

.onboarding-glass {
  width: 100%;
  max-width: 420px;
  border-radius: 16px;
  background-color: var(--glass-modal-bg);
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  box-shadow: var(--glass-shadow-lg);
  border: 1px solid var(--border-subtle);
}

.onboarding-content {
  padding: 28px 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
}

.onboarding-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(var(--color-accent), 0.18) 0%, rgba(var(--color-accent), 0.08) 100%);
  color: var(--color-accent-primary);
  margin-bottom: 8px;
}

.onboarding-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
}

.onboarding-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
  max-width: 360px;
}

.onboarding-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 8px;
  gap: 12px;
}

.onboarding-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.onboarding-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: rgba(168, 162, 158, 0.4);
  transition: background-color 0.24s ease, transform 0.24s ease, box-shadow 0.24s ease;
}

.onboarding-dot.is-active {
  background-color: var(--color-accent-primary);
  transform: scale(1.4);
  box-shadow: 0 0 0 2px rgba(var(--color-accent), 0.2);
}

.onboarding-nav {
  display: flex;
  gap: 8px;
}

.onboarding-btn {
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
}

.onboarding-btn-skip {
  background: transparent;
  color: var(--text-secondary);
  padding: 8px 12px;
}

.onboarding-btn-skip:hover {
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.05);
}

.onboarding-btn-secondary {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-primary);
}

.onboarding-btn-secondary:hover {
  background: rgba(0, 0, 0, 0.1);
}

.onboarding-btn-primary {
  background: linear-gradient(135deg, var(--color-accent-primary) 0%, color-mix(in srgb, var(--color-accent-primary) 85%, #1c1917) 100%);
  color: white;
  box-shadow: 0 2px 8px -2px rgba(var(--color-accent), 0.35);
}

.onboarding-btn-primary:hover {
  filter: brightness(1.05);
}

/* Transitions */
.onboarding-enter-active,
.onboarding-leave-active {
  transition: opacity 0.24s ease;
}

.onboarding-enter-active .onboarding-glass,
.onboarding-leave-active .onboarding-glass {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.onboarding-enter-from,
.onboarding-leave-to {
  opacity: 0;
}

.onboarding-enter-from .onboarding-glass,
.onboarding-leave-to .onboarding-glass {
  transform: scale(0.95);
  opacity: 0;
}

/* Mobile */
@media (max-width: 540px) {
  .onboarding-backdrop {
    padding: 16px;
    align-items: flex-end;
    padding-bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  }

  .onboarding-glass {
    max-width: none;
    width: calc(100% - 32px);
  }

  .onboarding-content {
    padding: 28px 20px 20px;
  }

  .onboarding-title {
    font-size: 18px;
  }

  .onboarding-desc {
    font-size: 13px;
  }

  .onboarding-footer {
    flex-wrap: wrap;
    justify-content: center;
  }

  .onboarding-btn-skip {
    order: 1;
    width: 100%;
    margin-bottom: 4px;
  }

  .onboarding-dots {
    order: 2;
  }

  .onboarding-nav {
    order: 3;
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
