<script setup lang="ts" name="GlassContainer">
import { ref, watch, computed, type CSSProperties } from 'vue'
import { GlassMode, type GlassContainerProps } from '../type'
import { ShaderDisplacementGenerator } from '../shader-util';

import GlassFilter from './GlassFilter.vue'
import { uuid } from '../utils';
const props = withDefaults(defineProps<GlassContainerProps>(), {
    className: "",
    displacementScale: 25,
    blurAmount: 12,
    saturation: 180,
    aberrationIntensity: 2,
    active: false,
    overLight: false,
    cornerRadius: 999,
    padding: "24px 32px",
    glassSize: () => ({ width: 270, height: 69 }),
    mode: GlassMode.standard,
    effect: "liquidGlass"
})
const shaderMapUrl = ref<string>("")
const isFirefox = window.navigator.userAgent.toLowerCase().includes("firefox")
const filterId = uuid()
// Generate shader-based displacement map using shaderUtils
const generateShaderDisplacementMap = async (width: number, height: number) => {
    const generator = new ShaderDisplacementGenerator({
        width,
        height,
        effect: props.effect,
    })

    const dataUrl = await generator.updateShader()
    generator.destroy()

    return dataUrl
}
watch(() => [props.mode, props.glassSize.width, props.glassSize.height, props.effect], async () => {
    if (props.mode === "shader") {
        const url = await generateShaderDisplacementMap(props.glassSize.width, props.glassSize.height)
        shaderMapUrl.value = url
    }
})

const normalizedBlurAmount = computed(() => {
    const raw = Number(props.blurAmount ?? 0)
    if (!Number.isFinite(raw)) {
        return 0
    }
    return Math.max(0, raw)
})

const backdropFilterValue = computed(() => {
    // Keep parameter semantics deterministic: 0 means no extra blur (when overLight is false).
    const blurPx = (props.overLight ? 12 : 0) + normalizedBlurAmount.value * 32
    return `blur(${blurPx}px) saturate(${props.saturation}%)`
})

const backdropStyle = computed<Partial<CSSProperties>>(() => {
    return {
        filter: isFirefox ? undefined : `url(#${filterId})`,
        backdropFilter: backdropFilterValue.value,
        WebkitBackdropFilter: backdropFilterValue.value,
    }
})



</script>

<template>
    <div :class="`relative ${className} ${active ? 'active' : ''} ${Boolean(onClick) ? 'cursor-pointer' : ''}`"
        :style="style" @click="onClick">
        <GlassFilter :mode="mode" :id="filterId" :displacementScale="displacementScale"
            :aberrationIntensity="aberrationIntensity" :width="glassSize.width" :height="glassSize.height"
            :shaderMapUrl="shaderMapUrl" />

        <div class="glass" :style="{
            borderRadius: `${cornerRadius}px`,
            position: 'relative',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '24px',
            padding,
            overflow: 'hidden',
            transition: 'all 0.2s ease-in-out',
            boxShadow: props.overLight ? '0px 16px 70px rgba(0, 0, 0, 0.75)' : '0px 12px 40px rgba(0, 0, 0, 0.25)',
        }" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
            <!-- backdrop layer that gets wiggly -->
            <span class="glass__warp" :style="{
                ...backdropStyle,
                position: 'absolute',
                inset: '0',
            }"></span>

            <!-- user content stays sharp -->
            <div class="transition-all duration-150 ease-in-out text-white" :style="{
                position: 'relative',
                zIndex: 1,
                font: '500 20px/1 system-ui',
                textShadow: props.overLight ? '0px 2px 12px rgba(0, 0, 0, 0)' : '0px 2px 12px rgba(0, 0, 0, 0.4)',
            }">
                <slot />
            </div>
        </div>
    </div>
</template>
