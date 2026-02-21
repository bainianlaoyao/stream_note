<template>
  <section class="ui-auth-shell">
    <article class="ui-surface-card ui-auth-card">
      <header class="ui-auth-header">
        <h1 class="ui-heading ui-heading-lg">Stream Note</h1>
        <p class="ui-body ui-body-sm">Sign in to access your isolated workspace.</p>
      </header>

      <div class="ui-auth-tabs" role="tablist" aria-label="Auth mode">
        <button
          type="button"
          :class="['ui-auth-tab', { 'is-active': mode === 'login' }]"
          role="tab"
          :aria-selected="mode === 'login'"
          @click="mode = 'login'"
        >
          Login
        </button>
        <button
          type="button"
          :class="['ui-auth-tab', { 'is-active': mode === 'register' }]"
          role="tab"
          :aria-selected="mode === 'register'"
          @click="mode = 'register'"
        >
          Register
        </button>
      </div>

      <form class="ui-auth-form" @submit.prevent="submit">
        <label class="ui-auth-field">
          <span class="ui-caption">Username</span>
          <input
            v-model.trim="username"
            type="text"
            class="ui-auth-input"
            autocomplete="username"
            placeholder="alice"
            required
          />
        </label>

        <label class="ui-auth-field">
          <span class="ui-caption">Password</span>
          <input
            v-model="password"
            type="password"
            class="ui-auth-input"
            autocomplete="current-password"
            placeholder="At least 6 characters"
            required
          />
        </label>

        <button type="submit" class="ui-btn ui-btn-primary ui-auth-submit" :disabled="authStore.isLoading">
          {{ authStore.isLoading ? 'Processing...' : mode === 'login' ? 'Login' : 'Create Account' }}
        </button>
      </form>

      <p v-if="errorMessage" class="ui-pill ui-pill-strong ui-auth-error">{{ errorMessage }}</p>
      <p class="ui-body ui-body-sm ui-auth-footnote">
        {{ mode === 'login' ? 'No account yet? Switch to Register.' : 'Already have an account? Switch to Login.' }}
      </p>
    </article>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const errorMessage = ref<string | null>(null)

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

  return 'Request failed'
}

const submit = async () => {
  errorMessage.value = null

  try {
    if (mode.value === 'login') {
      await authStore.login(username.value, password.value)
    } else {
      await authStore.register(username.value, password.value)
    }
    await router.replace('/stream')
  } catch (error) {
    errorMessage.value = formatError(error)
  }
}

onMounted(async () => {
  await authStore.initialize()
  if (authStore.isAuthenticated) {
    await router.replace('/stream')
  }
})
</script>

<style scoped>
.ui-auth-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.ui-auth-card {
  width: min(420px, 100%);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ui-auth-header p {
  margin-top: 4px;
}

.ui-auth-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.ui-auth-tab {
  min-height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.45);
  background: rgba(255, 255, 255, 0.68);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  transition: border-color 0.2s ease, background-color 0.2s ease, color 0.2s ease;
}

.ui-auth-tab:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.82);
}

.ui-auth-tab.is-active {
  border-color: rgba(var(--color-accent), 0.42);
  background: rgba(250, 237, 205, 0.56);
  color: var(--color-accent-primary);
}

.ui-auth-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ui-auth-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ui-auth-input {
  width: 100%;
  min-height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(214, 211, 209, 0.56);
  background: rgba(255, 255, 255, 0.86);
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-sans);
  padding: 0 12px;
}

.ui-auth-input:focus {
  border-color: rgba(var(--color-accent), 0.56);
  box-shadow: 0 0 0 2px rgba(var(--color-accent), 0.2);
}

.ui-auth-submit {
  margin-top: 4px;
}

.ui-auth-error {
  margin: 0;
}

.ui-auth-footnote {
  margin: 0;
}
</style>
