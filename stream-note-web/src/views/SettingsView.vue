<template>
  <section class="ui-view-stack ui-settings-shell">
    <SharedLiquidGlass class="ui-settings-glass" :tilt-sensitivity="0.38">
      <section class="ui-settings-panel">
        <section class="ui-settings-account">
          <div>
            <p class="ui-caption">{{ t('settingsAccount') }}</p>
            <p class="ui-body ui-body-sm ui-settings-account-name">
              {{ t('settingsSignedInAs') }} <strong>{{ accountName }}</strong>
            </p>
          </div>
          <button type="button" class="ui-btn ui-btn-ghost" @click="logout">
            {{ t('settingsLogout') }}
          </button>
        </section>

        <p v-if="isLoading" class="ui-body ui-body-sm ui-settings-loading">{{ t('settingsLoading') }}</p>

        <form v-else class="ui-settings-grid" @submit.prevent="saveSettings">
          <label class="ui-settings-field is-full">
            <span class="ui-caption">{{ t('settingsLanguage') }}</span>
            <div class="ui-settings-segment" role="group" :aria-label="t('settingsLanguage')">
              <button
                type="button"
                class="ui-settings-segment-btn"
                :class="{ 'is-active': locale === 'zh' }"
                @click="setLocale('zh')"
              >
                {{ t('settingsLanguageZh') }}
              </button>
              <button
                type="button"
                class="ui-settings-segment-btn"
                :class="{ 'is-active': locale === 'en' }"
                @click="setLocale('en')"
              >
                {{ t('settingsLanguageEn') }}
              </button>
            </div>
            <span class="ui-body ui-body-sm ui-settings-hint">{{ t('settingsLanguageHint') }}</span>
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">{{ t('settingsProvider') }}</span>
            <select v-model="form.provider" class="ui-settings-select">
              <option v-for="provider in supportedProviders" :key="provider" :value="provider">
                {{ providerLabel(provider) }}
              </option>
            </select>
            <span class="ui-body ui-body-sm ui-settings-hint">{{ providerHint }}</span>
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">{{ t('settingsModel') }}</span>
            <input v-model.trim="form.model" type="text" class="ui-settings-input" :placeholder="t('settingsModelPlaceholder')" />
          </label>

          <label class="ui-settings-field is-full">
            <span class="ui-caption">{{ t('settingsBaseUrl') }}</span>
            <input v-model.trim="form.api_base" type="text" class="ui-settings-input" :placeholder="t('settingsBaseUrlPlaceholder')" />
          </label>

          <label class="ui-settings-field is-full">
            <span class="ui-caption">{{ t('settingsApiKey') }}</span>
            <input
              v-model.trim="form.api_key"
              type="password"
              class="ui-settings-input"
              :placeholder="t('settingsApiKeyPlaceholder')"
            />
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">{{ t('settingsTimeout') }}</span>
            <input
              v-model.number="form.timeout_seconds"
              type="number"
              min="1"
              max="120"
              step="1"
              class="ui-settings-input"
            />
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">{{ t('settingsRetryAttempts') }}</span>
            <input
              v-model.number="form.max_attempts"
              type="number"
              min="1"
              max="5"
              step="1"
              class="ui-settings-input"
            />
          </label>

          <label class="ui-settings-field is-full ui-settings-check">
            <input v-model="form.disable_thinking" type="checkbox" />
            <div class="ui-settings-check-copy">
              <div class="ui-body ui-body-sm">{{ t('settingsDisableReasoning') }}</div>
              <div class="ui-caption">{{ t('settingsDisableReasoningHint') }}</div>
            </div>
          </label>

          <div class="ui-settings-actions">
            <button type="submit" class="ui-btn ui-btn-primary" :disabled="isSaving || isTesting">
              {{ isSaving ? t('settingsSaving') : t('settingsSave') }}
            </button>
            <button type="button" class="ui-btn ui-btn-ghost" :disabled="isSaving || isTesting" @click="testConnection">
              {{ isTesting ? t('settingsTesting') : t('settingsTestConnection') }}
            </button>
          </div>
        </form>

        <div v-if="updatedAtLabel || saveMessage || testMessage || errorMessage" class="ui-status-row">
          <p v-if="updatedAtLabel" class="ui-pill">{{ updatedAtLabel }}</p>
          <p v-if="saveMessage" class="ui-pill ui-pill-success">{{ saveMessage }}</p>
          <p v-if="testMessage" class="ui-pill ui-pill-success">{{ testMessage }}</p>
          <p v-if="errorMessage" class="ui-pill ui-pill-strong">{{ errorMessage }}</p>
        </div>
      </section>
    </SharedLiquidGlass>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import SharedLiquidGlass from '@/components/glass/SharedLiquidGlass.vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/composables/useI18n'
import {
  getAIProviderSettings,
  testAIProviderSettings,
  updateAIProviderSettings,
  type AIProvider,
  type AIProviderSettings,
  type AIProviderSettingsPayload
} from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const { locale, setLocale, t, getDateTimeLocale } = useI18n()

const DEFAULT_PROVIDERS: AIProvider[] = ['openai_compatible', 'openai', 'siliconflow', 'ollama']

const form = reactive<AIProviderSettingsPayload>({
  provider: 'openai_compatible',
  api_base: 'http://localhost:11434/v1',
  api_key: '',
  model: 'llama3.2',
  timeout_seconds: 20,
  max_attempts: 2,
  disable_thinking: true
})

const supportedProviders = ref<AIProvider[]>(DEFAULT_PROVIDERS)
const updatedAt = ref<string | null>(null)

const isLoading = ref(true)
const isSaving = ref(false)
const isTesting = ref(false)

const saveMessage = ref<string | null>(null)
const testMessage = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

const accountName = computed(() => authStore.user?.username ?? t('settingsUnknownAccount'))
const providerHint = computed<string>(() => {
  switch (form.provider) {
    case 'openai_compatible':
      return t('providerHintOpenAICompatible')
    case 'openai':
      return t('providerHintOpenAI')
    case 'siliconflow':
      return t('providerHintSiliconFlow')
    case 'ollama':
      return t('providerHintOllama')
    default:
      return t('providerHintOpenAICompatible')
  }
})
const updatedAtLabel = computed<string | null>(() => {
  if (updatedAt.value === null) {
    return null
  }

  const date = new Date(updatedAt.value)
  if (Number.isNaN(date.getTime())) {
    return t('settingsUpdatedRecently')
  }
  return `${t('settingsUpdatedPrefix')} ${date.toLocaleString(getDateTimeLocale())}`
})

const providerLabel = (provider: AIProvider): string => {
  switch (provider) {
    case 'openai_compatible':
      return t('providerOpenAICompatible')
    case 'openai':
      return t('providerOpenAI')
    case 'siliconflow':
      return t('providerSiliconFlow')
    case 'ollama':
      return t('providerOllama')
    default:
      return t('providerOpenAICompatible')
  }
}

const toPayload = (): AIProviderSettingsPayload => {
  const timeout = Number(form.timeout_seconds)
  const retry = Number(form.max_attempts)

  const normalizedTimeout = Number.isFinite(timeout) ? Math.min(120, Math.max(1, timeout)) : 20
  const normalizedRetry = Number.isFinite(retry) ? Math.min(5, Math.max(1, Math.round(retry))) : 2

  return {
    provider: form.provider,
    api_base: form.api_base.trim(),
    api_key: form.api_key.trim(),
    model: form.model.trim(),
    timeout_seconds: normalizedTimeout,
    max_attempts: normalizedRetry,
    disable_thinking: form.disable_thinking
  }
}

const applySettings = (settings: AIProviderSettings): void => {
  form.provider = settings.provider
  form.api_base = settings.api_base
  form.api_key = settings.api_key
  form.model = settings.model
  form.timeout_seconds = settings.timeout_seconds
  form.max_attempts = settings.max_attempts
  form.disable_thinking = settings.disable_thinking
  supportedProviders.value =
    settings.supported_providers.length > 0 ? settings.supported_providers : DEFAULT_PROVIDERS
  updatedAt.value = settings.updated_at
}

const formatError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim() !== '') {
      return detail
    }
    return `${t('commonRequestFailed')} (${error.response?.status ?? t('commonNetwork')})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return t('commonUnknownError')
}

const loadSettings = async (): Promise<void> => {
  isLoading.value = true
  errorMessage.value = null
  saveMessage.value = null
  testMessage.value = null

  try {
    const settings = await getAIProviderSettings()
    applySettings(settings)
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isLoading.value = false
  }
}

const saveSettings = async (): Promise<void> => {
  if (isSaving.value || isTesting.value) {
    return
  }

  isSaving.value = true
  errorMessage.value = null
  saveMessage.value = null
  testMessage.value = null

  try {
    const payload = toPayload()
    const settings = await updateAIProviderSettings(payload)
    applySettings(settings)
    saveMessage.value = t('settingsSavedMessage')
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isSaving.value = false
  }
}

const testConnection = async (): Promise<void> => {
  if (isSaving.value || isTesting.value) {
    return
  }

  isTesting.value = true
  errorMessage.value = null
  testMessage.value = null

  try {
    const payload = toPayload()
    const result = await testAIProviderSettings(payload)
    testMessage.value = `${t('settingsConnectionOkPrefix')} (${result.latency_ms} ms): ${result.message}`
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isTesting.value = false
  }
}

const logout = async () => {
  authStore.logout()
  await router.replace('/auth')
}

onMounted(async () => {
  await loadSettings()
})
</script>

<style scoped>
.ui-settings-shell {
  width: min(960px, 100%);
  margin-inline: auto;
  padding: 4px 4px 8px;
}

.ui-settings-glass {
  width: 100%;
}

.ui-settings-panel {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ui-settings-account {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.45);
  background: rgba(255, 255, 255, 0.68);
}

.ui-settings-account-name {
  margin-top: 2px;
}

.ui-settings-loading {
  margin: 2px 0;
}

.ui-settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 12px;
  row-gap: 14px;
  align-items: start;
}

.ui-settings-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.ui-settings-field.is-full {
  grid-column: 1 / -1;
}

.ui-settings-hint {
  margin-top: 1px;
  line-height: 1.45;
}

.ui-settings-select,
.ui-settings-input {
  width: 100%;
  min-height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.56);
  background: rgba(255, 255, 255, 0.86);
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-sans);
  padding: 0 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.ui-settings-select:hover,
.ui-settings-input:hover {
  background: rgba(255, 255, 255, 0.94);
}

.ui-settings-select:focus,
.ui-settings-input:focus {
  border-color: rgba(var(--color-accent), 0.56);
  box-shadow: 0 0 0 2px rgba(var(--color-accent), 0.2);
}

.ui-settings-segment {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.56);
  background: rgba(255, 255, 255, 0.82);
}

.ui-settings-segment-btn {
  min-height: 30px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  padding: 0 12px;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.ui-settings-segment-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.74);
}

.ui-settings-segment-btn.is-active {
  color: var(--color-accent-primary);
  background: rgba(250, 237, 205, 0.62);
  border-color: rgba(var(--color-accent), 0.44);
}

.ui-settings-input[type='password'] {
  font-family: var(--font-mono);
}

.ui-settings-check {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.45);
  background: rgba(255, 255, 255, 0.68);
}

.ui-settings-check input {
  margin: 0;
  width: 16px;
  height: 16px;
  accent-color: var(--color-accent-primary);
  flex-shrink: 0;
}

.ui-settings-check-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.ui-settings-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 2px;
  padding-top: 4px;
}

.ui-settings-actions .ui-btn {
  min-width: 136px;
}

.ui-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.ui-pill-success {
  border-color: rgba(110, 231, 183, 0.52);
  background: rgba(236, 253, 245, 0.65);
  color: #047857;
}

@media (max-width: 900px) {
  .ui-settings-shell {
    width: 100%;
    padding: 2px 0 6px;
  }

  .ui-settings-panel {
    padding: 14px;
    gap: 14px;
  }

  .ui-settings-account {
    flex-direction: column;
    align-items: stretch;
  }

  .ui-settings-account .ui-btn {
    width: 100%;
  }

  .ui-settings-grid {
    grid-template-columns: 1fr;
    row-gap: 12px;
  }

  .ui-settings-actions {
    justify-content: stretch;
    gap: 8px;
    padding-top: 2px;
  }

  .ui-settings-actions .ui-btn {
    flex: 1 1 100%;
    min-width: 0;
  }
}
</style>
