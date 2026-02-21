import { GlassMode, type LiquidGlassProps } from '@/lib/liquid-glass/type'

// Shared tuning knob for liquid-glass frosting strength.
// Larger value => stronger blur. Library range: 0 ~ 1.
export const SHARED_LIQUID_GLASS_FROST_BLUR_AMOUNT = 0.28

export const sharedLiquidGlassPreset: Readonly<Partial<LiquidGlassProps>> = Object.freeze({
  displacementScale: 42,
  blurAmount: SHARED_LIQUID_GLASS_FROST_BLUR_AMOUNT,
  saturation: 106,
  aberrationIntensity: 1,
  elasticity: 0,
  cornerRadius: 18,
  padding: '0',
  overLight: false,
  mode: GlassMode.prominent,
  effect: 'flowingLiquid'
})

export const resolveSharedLiquidGlassProps = (
  overrides: Partial<LiquidGlassProps> = {}
): Partial<LiquidGlassProps> => {
  const preset = sharedLiquidGlassPreset
  return {
    ...preset,
    ...overrides,
    style: {
      width: '100%',
      ...(preset.style ?? {}),
      ...(overrides.style ?? {})
    }
  }
}
