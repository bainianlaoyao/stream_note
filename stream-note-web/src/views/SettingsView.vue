<template>
  <section class="ui-view-stack">
    <LiquidGlass class="ui-settings-glass-host" v-bind="settingsLiquidGlassProps">
      <section class="ui-settings-panel">
        <p v-if="isLoading" class="ui-body ui-body-sm">Loading provider settings...</p>

        <form v-else class="ui-settings-grid" @submit.prevent="saveSettings">
          <label class="ui-settings-field">
            <span class="ui-caption">Provider</span>
            <select v-model="form.provider" class="ui-settings-select">
              <option v-for="provider in supportedProviders" :key="provider" :value="provider">
                {{ providerLabel(provider) }}
              </option>
            </select>
            <span class="ui-body ui-body-sm">{{ providerHint }}</span>
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">Model</span>
            <input v-model.trim="form.model" type="text" class="ui-settings-input" placeholder="gpt-4o-mini / llama3.2" />
          </label>

          <label class="ui-settings-field is-full">
            <span class="ui-caption">Base URL</span>
            <input v-model.trim="form.api_base" type="text" class="ui-settings-input" placeholder="https://api.openai.com/v1" />
          </label>

          <label class="ui-settings-field is-full">
            <span class="ui-caption">API Key</span>
            <input
              v-model.trim="form.api_key"
              type="password"
              class="ui-settings-input"
              placeholder="sk-... (local models can keep it empty or dummy)"
            />
          </label>

          <label class="ui-settings-field">
            <span class="ui-caption">Timeout (sec)</span>
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
            <span class="ui-caption">Retry Attempts</span>
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
            <div>
              <div class="ui-body ui-body-sm">Disable reasoning mode</div>
              <div class="ui-caption">Mainly for SiliconFlow-compatible endpoints.</div>
            </div>
          </label>

          <div class="ui-settings-actions">
            <button type="submit" class="ui-btn ui-btn-primary" :disabled="isSaving || isTesting">
              {{ isSaving ? 'Saving...' : 'Save Settings' }}
            </button>
            <button type="button" class="ui-btn ui-btn-ghost" :disabled="isSaving || isTesting" @click="testConnection">
              {{ isTesting ? 'Testing...' : 'Test Connection' }}
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
    </LiquidGlass>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'
import { LiquidGlass } from '@/lib/liquid-glass'
import { GlassMode, type LiquidGlassProps } from '@/lib/liquid-glass/type'
import {
  getAIProviderSettings,
  testAIProviderSettings,
  updateAIProviderSettings,
  type AIProvider,
  type AIProviderSettings,
  type AIProviderSettingsPayload
} from '@/services/api'

const DEFAULT_PROVIDERS: AIProvider[] = ['openai_compatible', 'openai', 'siliconflow', 'ollama']

const providerLabelMap: Record<AIProvider, string> = {
  openai_compatible: 'OpenAI Compatible',
  openai: 'OpenAI',
  siliconflow: 'SiliconFlow',
  ollama: 'Ollama'
}

const providerHintMap: Record<AIProvider, string> = {
  openai_compatible: 'Any endpoint that supports OpenAI Chat Completions API.',
  openai: 'Official OpenAI endpoint with your model access.',
  siliconflow: 'Uses enable_thinking switch when testing and extracting.',
  ollama: 'Local Ollama server, usually http://localhost:11434/v1.'
}

const form = reactive<AIProviderSettingsPayload>({
  provider: 'openai_compatible',
  api_base: 'http://localhost:11434/v1',
  api_key: 'dummy-key',
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

const providerHint = computed<string>(() => providerHintMap[form.provider])
const settingsLiquidGlassProps = computed<Partial<LiquidGlassProps>>(() => ({
  displacementScale: 86,
  blurAmount: 0.72,
  saturation: 150,
  aberrationIntensity: 2,
  elasticity: 0,
  cornerRadius: 16,
  centered: false,
  padding: '0',
  overLight: false,
  mode: GlassMode.prominent,
  effect: 'flowingLiquid',
  style: { width: '100%' }
}))
const updatedAtLabel = computed<string | null>(() => {
  if (updatedAt.value === null) {
    return null
  }

  const date = new Date(updatedAt.value)
  if (Number.isNaN(date.getTime())) {
    return 'Updated recently'
  }
  return `Updated ${date.toLocaleString()}`
})

const providerLabel = (provider: AIProvider): string => providerLabelMap[provider]

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
    return `Request failed (${error.response?.status ?? 'network'})`
  }

  if (error instanceof Error && error.message.trim() !== '') {
    return error.message
  }

  return 'Unknown error'
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
    saveMessage.value = 'Provider settings saved.'
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
    testMessage.value = `Connection ok (${result.latency_ms} ms): ${result.message}`
  } catch (error) {
    errorMessage.value = formatError(error)
  } finally {
    isTesting.value = false
  }
}

onMounted(async () => {
  await loadSettings()
})
</script>

<style scoped>
.ui-settings-glass-host {
  width: 100%;
  display: block;
}

.ui-settings-glass-host .glass {
  width: 100%;
  display: flex;
  gap: 0;
}

.ui-settings-glass-host .glass > div {
  width: 100%;
  color: inherit !important;
  font: inherit !important;
  text-shadow: none !important;
}

.ui-settings-panel {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ui-settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ui-settings-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.ui-settings-field.is-full {
  grid-column: 1 / -1;
}

.ui-settings-select,
.ui-settings-input {
  width: 100%;
  min-height: 38px;
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

.ui-settings-input[type='password'] {
  font-family: var(--font-mono);
}

.ui-settings-check {
  flex-direction: row;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.45);
  background: rgba(255, 255, 255, 0.68);
}

.ui-settings-check input {
  margin-top: 2px;
  width: 16px;
  height: 16px;
  accent-color: var(--color-accent-primary);
}

.ui-settings-actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ui-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ui-pill-success {
  border-color: rgba(110, 231, 183, 0.52);
  background: rgba(236, 253, 245, 0.65);
  color: #047857;
}

@media (max-width: 900px) {
  .ui-settings-grid {
    grid-template-columns: 1fr;
  }

  .ui-settings-actions .ui-btn {
    flex: 1 1 100%;
  }
}
</style>
