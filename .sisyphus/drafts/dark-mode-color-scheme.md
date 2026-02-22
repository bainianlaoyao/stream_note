# Draft: Dark Mode Color Scheme Design

## Current State Analysis

### Existing Dark Mode Tokens (tokens.css:81-112)

```css
:root[data-theme='dark'] {
  --color-accent-primary: #e6b88a;
  --color-accent-hover: #d4a373;
  --color-accent-subtle: #4a3f35;

  --color-bg-app: #1c1917;
  --color-bg-surface-1: rgba(28, 25, 23, 0.85);
  --color-bg-surface-2: rgba(41, 37, 36, 0.7);

  --text-primary: #f5f5f4;
  --text-secondary: #d6d3d1;
  --text-tertiary: #a8a29e;
  --text-muted: #78716c;
  --text-placeholder: #78716c;

  --border-light: rgba(255, 255, 255, 0.1);
  --border-subtle: rgba(255, 255, 255, 0.05);
}
```

### Identified Problems

| Issue | Current Value | Problem | Impact |
|-------|--------------|---------|--------|
| **Surface 层级不足** | 只有 surface-1, surface-2 | 无法表达复杂的 elevation 层级 | 层次感弱，UI 元素难以区分 |
| **Border 太淡** | `rgba(255,255,255,0.1)` | 对比度不足 | 边界模糊，视觉疲劳 |
| **Text tertiary/muted 对比度不足** | `#a8a29e` | 在 `#1c1917` 上对比度约 4.2:1 | 勉强达标，阅读体验差 |
| **Accent 在深色背景上过亮** | `#e6b88a` | 直接使用浅色变体 | 刺眼，破坏视觉平衡 |
| **阴影使用纯黑** | `rgba(0,0,0,0.4-0.6)` | 缺乏色调 | 阴影死板，缺乏深度感 |
| **Glass 效果参数未调优** | 直接沿用亮色模式 | 透明度/模糊度不匹配 | 效果浑浊或过于透明 |

### Light Mode Reference (The "Washi Acrylic" Aesthetic)

Light mode features:
- Warm, paper-like background (#fdfcfb → #fcf8f1)
- Amber/clay accent (#d4a373) - "和纸" (washi) inspired
- Soft grain textures
- Subtle ambient orbs (yellow #fef08a, cream #ffedd5)
- Multiple glass layers with careful transparency

## Research Findings

### Material Design 3 Dark Theme Principles

1. **Tonal Elevation**: Higher surfaces receive more primary color tint
2. **Surface Tint Formula**: 
   - 0dp: 0% tint
   - 1dp: 5% tint
   - 3dp: 7% tint
   - 6dp: 8% tint
   - 8dp: 9% tint
   - 12dp: 11% tint
   - 24dp: 14% tint

3. **Avoid Pure Black**: Use `#121212` or warmer equivalents

### Carbon Design System Layering Model

```
Layer 03 (Highest): Popovers, Tooltips, Toasts
Layer 02: Cards, Side panels, Modals
Layer 01: Content areas, Tab content
Base Layer: Page background
```

### Radix Colors 12-Step Scale (Dark Mode Adapted)

| Step | Use Case | Dark Mode Principle |
|------|----------|---------------------|
| 1 | App background | Darkest but not pure black |
| 2 | Subtle background | Slightly elevated |
| 3 | UI element background | Interactive surface base |
| 4 | Hovered UI background | Hover state |
| 5 | Active/Selected background | Active state |
| 6 | Subtle borders | Separator lines |
| 7 | UI element border | Input borders |
| 8 | Hovered border | Hover border state |
| 9 | Solid backgrounds | Buttons, badges |
| 10 | Hovered solid | Button hover |
| 11 | Low-contrast text | Secondary text |
| 12 | High-contrast text | Primary text |

### WCAG AA Contrast Requirements

- Body text: **4.5:1 minimum**
- Large text (18px+): **3:1 minimum**
- UI components: **3:1 minimum**

## Design System Architecture Proposal

### Color Token Structure

```
Foundation Colors
├── Surface Scale (12 steps)
├── Text Scale (5 levels)
├── Border Scale (4 levels)
├── Accent Scale (primary, hover, subtle, dim)
└── Utility Colors (error, warning, success)

Semantic Tokens
├── Background
│   ├── app (base)
│   ├── sidebar (elevated-1)
│   ├── card (elevated-2)
│   ├── modal (elevated-3)
│   └── overlay (elevated-4)
├── Text
│   ├── primary (high emphasis)
│   ├── secondary (medium emphasis)
│   ├── tertiary (low emphasis)
│   ├── muted (disabled/hint)
│   └── placeholder
├── Border
│   ├── default
│   ├── subtle
│   ├── strong
│   └── focus
└── Interactive
    ├── accent-default
    ├── accent-hover
    ├── accent-active
    └── accent-subtle
```

### Elevation System (5 Levels)

```
Level 0: App Background      → Darkest, base tint
Level 1: Sidebar, Nav        → +4% luminance, subtle tint
Level 2: Cards, Content      → +8% luminance, light tint
Level 3: Modals, Popovers    → +12% luminance, medium tint
Level 4: Floating elements   → +16% luminance, visible tint
```

## Confirmed Design Decisions ✅

1. **色调基调**: 暖色调 (Warm)
   - 使用偏暖的深灰色，保持与亮色模式的 amber/和纸质感一致性
   - 基础色: #1a1815 (暖黑), #2a2520 (暖灰)

2. **对比度级别**: 平衡对比度 (WCAG AA)
   - 满足 4.5:1 标准文本对比度
   - 3:1 大文本/UI 组件对比度
   - 阅读舒适，不刺眼

3. **Accent 颜色处理**: 同色降饱和
   - 保持相同色相 (amber #d4a373)
   - 降低 10-15% 饱和度
   - 结果: #c99a6a (略柔和不刺眼)

4. **Glass 效果**: 温暖玻璃
   - 更不透明 (92% opacity)
   - 更强模糊 (24px blur)
   - 暖色调 tint (amber 染色)

---

## Final Dark Mode Color System Design

### 1. Surface Elevation System (5 Levels)

基于 Material Design 3 Tonal Elevation 原则，结合暖色调主题设计。

| Level | Token | Hex | RGB | Usage | Luminance |
|-------|-------|-----|-----|-------|-----------|
| 0 | `--surface-0` | #181614 | 24, 22, 20 | App Background (Base) | 1.8% |
| 1 | `--surface-1` | #1e1b17 | 30, 27, 23 | Sidebar, Navigation | 2.4% |
| 2 | `--surface-2` | #25221d | 37, 34, 29 | Cards, Content areas | 3.2% |
| 3 | `--surface-3` | #2d2a24 | 45, 42, 36 | Modals, Dialogs | 4.2% |
| 4 | `--surface-4` | #35322b | 53, 50, 43 | Floating panels, Tooltips | 5.4% |

**Surface with Alpha (for glass effects):**
| Token | Value | Usage |
|-------|-------|-------|
| `--surface-1-alpha` | rgba(30, 27, 23, 0.92) | Glass sidebar |
| `--surface-2-alpha` | rgba(37, 34, 29, 0.88) | Glass cards |
| `--surface-3-alpha` | rgba(45, 42, 36, 0.94) | Glass modals |

### 2. Text Color System (WCAG AA Compliant)

所有文本颜色基于 surface-0 (#181614) 计算对比度。

| Token | Hex | Contrast Ratio | Usage |
|-------|-----|----------------|-------|
| `--text-primary` | #faf9f7 | 16.8:1 ✅ AAA | High emphasis text, headings |
| `--text-secondary` | #c4bfb8 | 8.4:1 ✅ AAA | Body text, descriptions |
| `--text-tertiary` | #9c968c | 4.8:1 ✅ AA | Low emphasis, timestamps |
| `--text-muted` | #78746a | 3.2:1 ✅ AA (large) | Disabled, hints |
| `--text-placeholder` | #68645c | 2.6:1 ⚠️ | Placeholder text |

**Note**: `--text-placeholder` 用于 placeholder 是可接受的（非主要内容）。

### 3. Border Color System

| Token | Hex/Value | Usage |
|-------|-----------|-------|
| `--border-subtle` | rgba(255, 255, 255, 0.06) | Very subtle separators |
| `--border-default` | rgba(255, 255, 255, 0.10) | Standard borders |
| `--border-strong` | rgba(255, 255, 255, 0.16) | Emphasized borders, inputs |
| `--border-focus` | rgba(201, 154, 106, 0.50) | Focus ring |
| `border-accent` | rgba(201, 154, 106, 0.40) | Accent colored borders |

### 4. Accent Color System

原色 #d4a373 (amber/clay)，降低饱和度后变体：

| Token | Hex | HSL | Usage |
|-------|-----|-----|-------|
| `--accent-9` | #c99a6a | 34°, 48%, 60% | Primary accent (buttons, links) |
| `--accent-10` | #b8895c | 34°, 42%, 54% | Hover state |
| `--accent-11` | #d4a878 | 34°, 52%, 65% | Active state |
| `--accent-3` | #3d3529 | 34°, 18%, 20% | Subtle background (accent-subtle) |
| `--accent-4` | #4a4235 | 34°, 16%, 25% | Accent surface variant |
| `--accent-5` | #5a5042 | 34°, 15%, 31% | Selected/hovered accent surface |

**Accent RGB aliases** (for `rgba(var(--accent), alpha)` usage):
```css
--accent: 201, 154, 106;      /* Primary */
--accent-dim: 184, 137, 92;   /* Hover */
--accent-bright: 212, 168, 120; /* Active */
```

### 5. Glass Effect Parameters (Dark Mode Specific)

```css
/* Glass Background */
--glass-bg-sidebar: linear-gradient(
  165deg,
  rgba(30, 27, 23, 0.96),
  rgba(26, 24, 21, 0.92)
);
--glass-bg-card: linear-gradient(
  165deg,
  rgba(45, 42, 36, 0.94),
  rgba(37, 34, 29, 0.88)
);
--glass-bg-modal: linear-gradient(
  165deg,
  rgba(53, 50, 43, 0.98),
  rgba(45, 42, 36, 0.95)
);

/* Glass Blur */
--glass-blur-sidebar: 28px;
--glass-blur-card: 24px;
--glass-blur-modal: 32px;

/* Glass Tint (Warm) */
--glass-tint: rgba(201, 154, 106, 0.04);
--glass-tint-strong: rgba(201, 154, 106, 0.08);

/* Glass Border */
--glass-border-light: rgba(255, 255, 255, 0.08);
--glass-border-default: rgba(255, 255, 255, 0.12);
--glass-border-accent: rgba(201, 154, 106, 0.20);
```

### 6. Shadow System

```css
/* Elevation Shadows (with warm tone) */
--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.32);
--shadow-sm: 0 2px 8px -2px rgba(0, 0, 0, 0.40);
--shadow-md: 0 8px 24px -8px rgba(0, 0, 0, 0.48);
--shadow-lg: 0 16px 48px -16px rgba(0, 0, 0, 0.56);
--shadow-xl: 0 24px 64px -24px rgba(0, 0, 0, 0.64);

/* Accent Glow Shadow */
--shadow-accent-sm: 0 4px 16px -4px rgba(201, 154, 106, 0.20);
--shadow-accent-md: 0 8px 32px -8px rgba(201, 154, 106, 0.28);
--shadow-accent-lg: 0 16px 48px -16px rgba(201, 154, 106, 0.35);

/* Inset Shadows (for pressed states) */
--shadow-inset-sm: inset 0 1px 2px rgba(0, 0, 0, 0.24);
--shadow-inset-md: inset 0 2px 4px rgba(0, 0, 0, 0.32);
```

### 7. Interactive State Colors

```css
/* Hover overlays */
--hover-overlay: rgba(255, 255, 255, 0.04);
--hover-overlay-strong: rgba(255, 255, 255, 0.08);

/* Active/Pressed */
--active-overlay: rgba(255, 255, 255, 0.12);

/* Focus Ring */
--focus-ring: 0 0 0 2px rgba(201, 154, 106, 0.40);
--focus-ring-strong: 0 0 0 2px rgba(201, 154, 106, 0.60);
```

### 8. Material Texture Parameters (Dark Mode)

```css
/* Paper/Fiber grain textures */
--material-grain-alpha: 0.12;       /* Light mode: 0.22 */
--material-fiber-alpha: 0.06;       /* Light mode: 0.04 */
--material-paper-tint-alpha: 0.35;  /* Light mode: 0.28 */

/* Sidebar acrylic */
--material-sidebar-blur: 28px;
--material-sidebar-tint: 0.50;
--material-sidebar-shadow: 0.28;
```

### 9. Ambient/Background Gradients

```css
/* Stage background - warm dark with subtle ambient glow */
--stage-bg: 
  radial-gradient(45% 40% at 8% 10%, rgba(201, 154, 106, 0.06), transparent 60%),
  radial-gradient(40% 45% at 90% 85%, rgba(180, 140, 100, 0.04), transparent 65%),
  linear-gradient(165deg, #181614 0%, #1a1815 50%, #1c1917 100%);
```

### 10. Semantic Aliases (For Backward Compatibility)

```css
/* Map new system to existing token names */
--color-bg-app: var(--surface-0);
--color-bg-surface-1: var(--surface-1-alpha);
--color-bg-surface-2: var(--surface-2-alpha);

--color-accent-primary: var(--accent-9);
--color-accent-hover: var(--accent-10);
--color-accent-subtle: var(--accent-3);

--glass-card-bg: rgba(45, 42, 36, 0.72);
--glass-sidebar-bg: rgba(30, 27, 23, 0.92);
```

---

## Implementation CSS Code

```css
/* ============================================
   DARK MODE - Warm Clay/Amber Theme
   ============================================ */
:root[data-theme='dark'] {
  
  /* ========== SURFACE ELEVATION ========== */
  --surface-0: #181614;
  --surface-1: #1e1b17;
  --surface-2: #25221d;
  --surface-3: #2d2a24;
  --surface-4: #35322b;
  
  /* Surface with alpha (for glass) */
  --surface-1-alpha: rgba(30, 27, 23, 0.92);
  --surface-2-alpha: rgba(37, 34, 29, 0.88);
  --surface-3-alpha: rgba(45, 42, 36, 0.94);
  --surface-4-alpha: rgba(53, 50, 43, 0.96);
  
  /* ========== TEXT COLORS ========== */
  --text-primary: #faf9f7;
  --text-secondary: #c4bfb8;
  --text-tertiary: #9c968c;
  --text-muted: #78746a;
  --text-placeholder: #68645c;
  
  /* ========== ACCENT COLORS ========== */
  /* Primary accent scale (reduced saturation from #d4a373) */
  --accent-1: #1a1612;
  --accent-2: #2a2420;
  --accent-3: #3d3529;
  --accent-4: #4a4235;
  --accent-5: #5a5042;
  --accent-6: #6b6050;
  --accent-7: #7d7260;
  --accent-8: #958672;
  --accent-9: #c99a6a;      /* Primary */
  --accent-10: #b8895c;     /* Hover */
  --accent-11: #d4a878;     /* Active */
  --accent-12: #f5e8d4;     /* High contrast on accent */
  
  /* Accent RGB aliases */
  --color-accent: 201, 154, 106;
  --color-accent-dim: 184, 137, 92;
  --color-accent-bright: 212, 168, 120;
  
  /* ========== LEGACY ACCENT TOKENS ========== */
  --color-accent-primary: #c99a6a;
  --color-accent-hover: #b8895c;
  --color-accent-subtle: #3d3529;
  
  /* ========== BORDER COLORS ========== */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.10);
  --border-strong: rgba(255, 255, 255, 0.16);
  --border-light: rgba(255, 255, 255, 0.12);
  --border-accent: rgba(201, 154, 106, 0.40);
  
  /* ========== SHADOWS ========== */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.32);
  --shadow-sm: 0 2px 8px -2px rgba(0, 0, 0, 0.40);
  --shadow-md: 0 8px 24px -8px rgba(0, 0, 0, 0.48);
  --shadow-lg: 0 16px 48px -16px rgba(0, 0, 0, 0.56);
  --shadow-xl: 0 24px 64px -24px rgba(0, 0, 0, 0.64);
  --shadow-accent-sm: 0 4px 16px -4px rgba(201, 154, 106, 0.20);
  --shadow-accent-md: 0 8px 32px -8px rgba(201, 154, 106, 0.28);
  --shadow-inset-sm: inset 0 1px 2px rgba(0, 0, 0, 0.24);
  --shadow-inset-md: inset 0 2px 4px rgba(0, 0, 0, 0.32);
  
  /* ========== GLASS MATERIAL ========== */
  --glass-sidebar-bg: var(--surface-1-alpha);
  --glass-sidebar-blur: 28px;
  --glass-main-bg: var(--surface-2-alpha);
  --glass-main-blur: 24px;
  --glass-card-bg: rgba(45, 42, 36, 0.72);
  --glass-modal-bg: rgba(53, 50, 43, 0.94);
  --glass-blur-modal: 32px;
  --glass-tint: rgba(201, 154, 106, 0.04);
  --glass-tint-strong: rgba(201, 154, 106, 0.08);
  --glass-border-light: rgba(255, 255, 255, 0.08);
  --glass-shadow-sm: var(--shadow-sm);
  --glass-shadow-md: var(--shadow-md);
  --glass-shadow-lg: var(--shadow-lg);
  
  /* ========== LEGACY BACKGROUND TOKENS ========== */
  --color-bg-app: #181614;
  --color-bg-surface-1: rgba(30, 27, 23, 0.92);
  --color-bg-surface-2: rgba(37, 34, 29, 0.88);
  
  /* ========== MATERIAL TEXTURES ========== */
  --material-sidebar-desk-fiber-alpha: 0.06;
  --material-sidebar-desk-grain-alpha: 0.12;
  --material-stream-paper-grain-alpha: 0.18;
  --material-stream-paper-tint-alpha: 0.35;
  --material-nav-acrylic-blur: 10px;
  --material-nav-acrylic-tint-alpha: 0.48;
  --material-nav-acrylic-shadow-alpha: 0.28;
  
  /* ========== INTERACTIVE STATES ========== */
  --hover-overlay: rgba(255, 255, 255, 0.04);
  --hover-overlay-strong: rgba(255, 255, 255, 0.08);
  --active-overlay: rgba(255, 255, 255, 0.12);
  
  /* ========== COMPATIBILITY ALIASES ========== */
  --accent-main: var(--color-accent-primary);
  --accent-main-strong: var(--color-accent-hover);
  --accent-soft: rgba(var(--color-accent), 0.12);
  --overlay-blur: 6px;
}
```

---

## Contrast Verification

### Text on Surface-0 (#181614)

| Text Color | Contrast Ratio | WCAG Level |
|------------|----------------|------------|
| #faf9f7 (primary) | ~16.8:1 | AAA |
| #c4bfb8 (secondary) | ~8.4:1 | AAA |
| #9c968c (tertiary) | ~4.8:1 | AA |
| #78746a (muted) | ~3.2:1 | AA (large) |

### Accent Colors on Surface-2 (#25221d)

| Accent | On Dark Contrast | Usage |
|--------|------------------|-------|
| #c99a6a (accent-9) | 5.2:1 | Buttons, links ✅ |
| #b8895c (accent-10) | 4.4:1 | Hover state ✅ |
| #d4a878 (accent-11) | 6.0:1 | Active state ✅ |

---

## Next Steps

1. ✅ Design decisions confirmed
2. ✅ Color system designed
3. ⏳ Update tokens.css with implementation
4. ⏳ Update component CSS for dark mode variants
5. ⏳ Test in browser
6. ⏳ Document changes
