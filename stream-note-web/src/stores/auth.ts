import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  clearAuthToken,
  getCurrentAccount,
  getStoredAuthToken,
  loginAccount,
  registerAccount,
  saveAuthToken,
  type AuthUser
} from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isReady = ref(false)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => user.value !== null && getStoredAuthToken() !== null)

  const initialize = async () => {
    if (isReady.value) {
      return
    }

    const token = getStoredAuthToken()
    if (token === null) {
      user.value = null
      isReady.value = true
      return
    }

    isLoading.value = true
    try {
      user.value = await getCurrentAccount()
    } catch (error) {
      console.error('Failed to restore session:', error)
      clearAuthToken()
      user.value = null
    } finally {
      isLoading.value = false
      isReady.value = true
    }
  }

  const register = async (username: string, password: string) => {
    isLoading.value = true
    try {
      const result = await registerAccount({ username, password })
      saveAuthToken(result.access_token)
      user.value = result.user
      return result.user
    } finally {
      isLoading.value = false
      isReady.value = true
    }
  }

  const login = async (username: string, password: string) => {
    isLoading.value = true
    try {
      const result = await loginAccount({ username, password })
      saveAuthToken(result.access_token)
      user.value = result.user
      return result.user
    } finally {
      isLoading.value = false
      isReady.value = true
    }
  }

  const logout = () => {
    clearAuthToken()
    user.value = null
    isReady.value = true
  }

  return {
    user,
    isReady,
    isLoading,
    isAuthenticated,
    initialize,
    register,
    login,
    logout
  }
})
