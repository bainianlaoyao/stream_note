import { computed, ref } from 'vue'

const ONBOARDING_KEY = 'stream-note-onboarding'

const resolveInitialState = (): { completed: boolean; step: number } => {
  if (typeof window === 'undefined') {
    return { completed: false, step: 0 }
  }

  const saved = window.localStorage.getItem(ONBOARDING_KEY)
  if (saved === null) {
    return { completed: false, step: 0 }
  }

  try {
    const parsed = JSON.parse(saved)
    return {
      completed: parsed.completed === true,
      step: typeof parsed.step === 'number' ? parsed.step : 0
    }
  } catch {
    return { completed: false, step: 0 }
  }
}

const applyStateSideEffects = (completed: boolean, step: number): void => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(ONBOARDING_KEY, JSON.stringify({ completed, step }))
  }
}

const initialState = resolveInitialState()
const isCompleted = ref(initialState.completed)
const currentStep = ref(initialState.step)

export const useOnboarding = () => {
  const isVisible = computed(() => !isCompleted.value && currentStep.value > 0)

  const start = (): void => {
    currentStep.value = 1
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  const next = (): void => {
    if (currentStep.value >= 3) {
      complete()
      return
    }
    currentStep.value += 1
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  const prev = (): void => {
    if (currentStep.value <= 1) {
      return
    }
    currentStep.value -= 1
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  const skip = (): void => {
    isCompleted.value = true
    currentStep.value = 0
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  const complete = (): void => {
    isCompleted.value = true
    currentStep.value = 0
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  const reset = (): void => {
    isCompleted.value = false
    currentStep.value = 0
    applyStateSideEffects(isCompleted.value, currentStep.value)
  }

  return {
    isCompleted,
    currentStep,
    isVisible,
    start,
    next,
    prev,
    skip,
    complete,
    reset
  }
}
