import { GlassMode, type LiquidGlassProps } from '@/lib/liquid-glass/type'

// Single tuning knob for task-item frosting strength.
// Larger value => stronger blur. Original library range: 0 ~ 1.
export const TASK_ITEM_FROST_BLUR_AMOUNT = 0.88

export const taskLiquidGlassPreset: Partial<LiquidGlassProps> = {
  displacementScale: 136,
  blurAmount: TASK_ITEM_FROST_BLUR_AMOUNT,
  saturation: 132,
  aberrationIntensity: 3,
  elasticity: 0,
  cornerRadius: 18,
  centered: false,
  padding: '0',
  overLight: true,
  mode: GlassMode.prominent,
  effect: 'flowingLiquid',
}
