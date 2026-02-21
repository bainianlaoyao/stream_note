<template>
  <div
    ref="hostRef"
    class="ui-liquid-glass-inline-host"
    :class="hostClass"
    :style="hostInlineStyle"
    v-bind="forwardedAttrs"
    @mousemove="handlePointerMove"
    @mouseenter="handlePointerEnter"
    @mouseleave="handlePointerLeave"
    @mousedown="isActive = true"
    @mouseup="isActive = false"
    @click="handleClick"
  >
    <div
      class="ui-liquid-glass-host"
      :class="{ 'is-hovered': isHovered, 'is-active': isActive, 'is-over-light': isOverLight }"
    >
      <span class="ui-liquid-glass-backdrop"></span>
      <span class="ui-liquid-glass-frost"></span>
      <span class="ui-liquid-glass-noise"></span>
      <span class="ui-liquid-glass-glow"></span>
      <span class="ui-liquid-glass-edge ui-liquid-glass-edge-screen"></span>
      <span class="ui-liquid-glass-edge ui-liquid-glass-edge-overlay"></span>
      <div class="ui-liquid-glass-content" :style="contentStyle">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useAttrs, type CSSProperties, type StyleValue } from 'vue'
import type { LiquidGlassProps } from '@/lib/liquid-glass/type'
import { resolveSharedLiquidGlassProps } from '@/config/liquid-glass'

defineOptions({
  name: 'SharedLiquidGlass',
  inheritAttrs: false
})

const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, value))

const props = withDefaults(
  defineProps<{
    liquidGlass?: Partial<LiquidGlassProps>
    tiltSensitivity?: number
  }>(),
  {
    liquidGlass: () => ({}),
    tiltSensitivity: 1
  }
)

const attrs = useAttrs()
const hostRef = ref<HTMLElement | null>(null)
const isHovered = ref(false)
const isActive = ref(false)
const pointer = ref({ x: 50, y: 28 })

const forwardedAttrs = computed(() => {
  const source = attrs as Record<string, unknown>
  const next: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(source)) {
    if (key === 'class' || key === 'style') {
      continue
    }
    next[key] = value
  }
  return next
})

const hostClass = computed(() => attrs.class as StyleValue)
const hostInlineStyle = computed<StyleValue>(() => [attrs.style as StyleValue, hostStyle.value])

const resolvedLiquidGlassProps = computed<Partial<LiquidGlassProps>>(() =>
  resolveSharedLiquidGlassProps(props.liquidGlass ?? {})
)

const blurAmount = computed(() => clamp(Number(resolvedLiquidGlassProps.value.blurAmount ?? 0), 0, 1))
const saturation = computed(() => clamp(Number(resolvedLiquidGlassProps.value.saturation ?? 100), 70, 220))
const aberration = computed(() => clamp(Number(resolvedLiquidGlassProps.value.aberrationIntensity ?? 0), 0, 8))
const depth = computed(() => clamp(Number(resolvedLiquidGlassProps.value.displacementScale ?? 0), 0, 180))
const elasticity = computed(() => clamp(Number(resolvedLiquidGlassProps.value.elasticity ?? 0), 0, 1))
const cornerRadius = computed(() => clamp(Number(resolvedLiquidGlassProps.value.cornerRadius ?? 18), 6, 80))
const isOverLight = computed(() => Boolean(resolvedLiquidGlassProps.value.overLight))

const pointerNorm = computed(() => ({
  x: (pointer.value.x - 50) / 50,
  y: (pointer.value.y - 50) / 50
}))
const tiltSensitivity = computed(() => clamp(Number(props.tiltSensitivity ?? 1), 0, 1))

const blurPx = computed(() => (isOverLight.value ? 2 : 0) + blurAmount.value * 30)
const frostAlpha = computed(() => 0.14 + blurAmount.value * 0.3)
const tintAlpha = computed(() => clamp(0.06 + blurAmount.value * 0.2 + depth.value * 0.0005, 0.05, 0.24))
const grainAlpha = computed(() => clamp(0.055 + blurAmount.value * 0.13 + aberration.value * 0.008, 0.05, 0.2))
const backdropContrast = computed(() => clamp(1.02 + blurAmount.value * 0.08 + depth.value * 0.0003, 1.02, 1.16))
const backdropBrightness = computed(() => clamp(0.99 - blurAmount.value * 0.035, 0.92, 0.99))
const rimShadowAlpha = computed(() => clamp(0.06 + depth.value * 0.0012, 0.06, 0.22))
const depthShadow = computed(() => 12 + depth.value * 0.16)

const edgeAngle = computed(() => 135 + pointerNorm.value.x * 34)
const edgeStopA = computed(() => clamp(34 + pointerNorm.value.y * 10, 12, 82))
const edgeStopB = computed(() => clamp(66 + pointerNorm.value.y * 10, 18, 94))
const edgeMid = computed(() => clamp(0.12 + Math.abs(pointerNorm.value.x) * 0.08 + depth.value * 0.0004, 0.08, 0.5))
const edgePeak = computed(() =>
  clamp(0.34 + Math.abs(pointerNorm.value.x) * 0.14 + aberration.value * 0.02, 0.2, 0.88)
)

const tiltX = computed(
  () => pointerNorm.value.y * -(2.4 + elasticity.value * 4.6) * tiltSensitivity.value
)
const tiltY = computed(
  () => pointerNorm.value.x * (2.8 + elasticity.value * 5.2) * tiltSensitivity.value
)
const scale = computed(() => (isActive.value ? 0.992 : isHovered.value ? 1.003 : 1))

const hostStyle = computed<CSSProperties>(() => {
  const style = {
    ...(resolvedLiquidGlassProps.value.style ?? {}),
    '--ui-glass-radius': `${cornerRadius.value}px`,
    '--ui-glass-blur': `${blurPx.value.toFixed(2)}px`,
    '--ui-glass-saturation': `${saturation.value.toFixed(1)}%`,
    '--ui-glass-frost-alpha': frostAlpha.value.toFixed(3),
    '--ui-glass-tint-alpha': tintAlpha.value.toFixed(3),
    '--ui-glass-grain-alpha': grainAlpha.value.toFixed(3),
    '--ui-glass-backdrop-contrast': backdropContrast.value.toFixed(3),
    '--ui-glass-backdrop-brightness': backdropBrightness.value.toFixed(3),
    '--ui-glass-rim-shadow-alpha': rimShadowAlpha.value.toFixed(3),
    '--ui-glass-depth-shadow': `${depthShadow.value.toFixed(2)}px`,
    '--ui-glass-glow-x': `${pointer.value.x.toFixed(2)}%`,
    '--ui-glass-glow-y': `${pointer.value.y.toFixed(2)}%`,
    '--ui-glass-edge-angle': `${edgeAngle.value.toFixed(2)}deg`,
    '--ui-glass-edge-stop-a': `${edgeStopA.value.toFixed(2)}%`,
    '--ui-glass-edge-stop-b': `${edgeStopB.value.toFixed(2)}%`,
    '--ui-glass-edge-mid': edgeMid.value.toFixed(3),
    '--ui-glass-edge-peak': edgePeak.value.toFixed(3),
    '--ui-glass-tilt': `perspective(820px) rotateX(${tiltX.value.toFixed(2)}deg) rotateY(${tiltY.value.toFixed(2)}deg) scale(${scale.value.toFixed(4)})`
  } as CSSProperties
  return style
})

const contentStyle = computed<CSSProperties>(() => ({
  padding: resolvedLiquidGlassProps.value.padding ?? '0'
}))

const handlePointerMove = (event: MouseEvent): void => {
  const host = hostRef.value
  if (host === null) {
    return
  }

  const rect = host.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) {
    return
  }

  const x = ((event.clientX - rect.left) / rect.width) * 100
  const y = ((event.clientY - rect.top) / rect.height) * 100
  pointer.value = { x: clamp(x, 0, 100), y: clamp(y, 0, 100) }
}

const handlePointerEnter = (): void => {
  isHovered.value = true
}

const handlePointerLeave = (): void => {
  isHovered.value = false
  isActive.value = false
  pointer.value = { x: 50, y: 28 }
}

const handleClick = (): void => {
  resolvedLiquidGlassProps.value.onClick?.()
}
</script>
