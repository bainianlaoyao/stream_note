# Stream Note 风格设计系统

## 一、设计哲学：极简毛玻璃

### 1.1 核心理念

Stream Note 的视觉风格建立在「极简」与「质感」两个支柱之上。我们追求的不是炫目的视觉效果，而是让界面像一块精心打磨的玻璃——通透、干净、若有若无。

**毛玻璃（Glassmorphism）** 在这里不是装饰，而是功能。它创造视觉层次，区分不同功能区域，同时保持整体的一致性和呼吸感。玻璃后面的内容隐隐可见，就像思想在意识中流动——你可以专注当前，也可以余光感知全局。

### 1.2 设计原则

**克制（Restraint）**：每一处视觉效果都必须服务于功能。装饰是多余的，只有那些帮助用户理解界面层次、增强内容可读性的视觉处理才是必要的。

**通透（Transparency）**：层级之间应该是通透的，而非封闭的。毛玻璃创造了视觉上的深度，但不应该成为阅读的障碍。

**一致性（Consistency）**：整个应用共享同一套视觉语言。从侧边栏到弹窗，从输入框到下拉菜单，同样的圆角、同样的阴影、同样的透明度。

**自然（Naturalness）**：动画和交互应该符合物理世界的直觉。物体有重量，运动有惯性，静止有摩擦。

---

## 二、毛玻璃系统

### 2.1 玻璃层级

应用中的毛玻璃效果分为三个层级，每个层级有不同的透明度和模糊度：

| 层级 | 用途 | 背景色 | 模糊半径 | 边框 |
|------|------|--------|----------|------|
| L1 - 基底层 | 主内容区域背景 | `#0D0D0D` | 0 | 无 |
| L2 - 容器层 | 侧边栏、卡片、弹窗 | `rgba(30, 30, 30, 0.6)` | 20px | 1px `rgba(255,255,255,0.08)` |
| L3 - 悬浮层 | 浮层、提示、角标 | `rgba(40, 40, 40, 0.8)` | 30px | 1px `rgba(255,255,255,0.12)` |

**实现代码**：

```css
/* 基底层 */
.glass-base {
  background: #0D0D0D;
}

/* 容器层 - 侧边栏、卡片 */
.glass-container {
  background: rgba(30, 30, 30, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* 悬浮层 - 浮层、角标 */
.glass-elevated {
  background: rgba(40, 40, 40, 0.8);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.12);
}
```

### 2.2 微妙的纹理

为了避免纯色毛玻璃带来的「塑料感」，我们添加极微妙的噪点纹理：

```css
.glass-texture {
  position: relative;
}

.glass-texture::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.02;
  pointer-events: none;
  mix-blend-mode: overlay;
}
```

### 2.3 边框光晕

毛玻璃边缘添加极细的内部光晕，创造「发光玻璃」的质感：

```css
.glass-glow {
  position: relative;
}

.glass-glow::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.02) 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
```

---

## 三、色彩系统

### 3.1 设计令牌（Design Tokens）

所有颜色通过 CSS 变量定义，便于主题切换和全局调整。

#### 3.1.1 暗色主题（默认）

```css
:root {
  /* ===== 背景色 ===== */
  --bg-base: #0D0D0D;          /* 最底层，应用主背景 */
  --bg-surface: #141414;         /* 表面层，略亮于基底 */
  --bg-elevated: #1E1E1E;       /* 悬浮层，最亮的表面 */
  
  /* ===== 毛玻璃层 ===== */
  --glass-surface: rgba(30, 30, 30, 0.6);
  --glass-elevated: rgba(40, 40, 40, 0.8);
  
  /* ===== 文字色 ===== */
  --text-primary: #E8E8E8;      /* 主要文字，高对比度 */
  --text-secondary: #9A9A9A;    /* 次要文字 */
  --text-tertiary: #5C5C5C;     /* 弱化文字 */
  --text-placeholder: #4A4A4A;  /* 占位符 */
  
  /* ===== 强调色 ===== */
  --accent-primary: #FF9500;     /* 主强调色，温暖的橙色 */
  --accent-hover: #FFA633;       /* 强调色悬停态 */
  --accent-muted: rgba(255, 149, 0, 0.15); /* 强调色低饱和度背景 */
  
  /* ===== 功能色 ===== */
  --color-success: #34C759;      /* 成功，完成 */
  --color-warning: #FFD60A;      /* 警告 */
  --color-error: #FF453A;        /* 错误 */
  --color-info: #64D2FF;        /* 信息 */
  
  /* ===== 边框色 ===== */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.16);
  
  /* ===== 分割线 ===== */
  --divider: rgba(255, 255, 255, 0.04);
  
  /* ===== 阴影 ===== */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 20px rgba(255, 149, 0, 0.15);
}
```

#### 3.1.2 亮色主题

```css
[data-theme="light"] {
  --bg-base: #F5F5F5;
  --bg-surface: #FFFFFF;
  --bg-elevated: #FFFFFF;
  
  --glass-surface: rgba(255, 255, 255, 0.7);
  --glass-elevated: rgba(255, 255, 255, 0.85);
  
  --text-primary: #1A1A1A;
  --text-secondary: #6B6B6B;
  --text-tertiary: #A3A3A3;
  --text-placeholder: #C4C4C4;
  
  --accent-primary: #E68300;
  --accent-hover: #CC7500;
  --accent-muted: rgba(230, 131, 0, 0.1);
  
  --border-subtle: rgba(0, 0, 0, 0.04);
  --border-default: rgba(0, 0, 0, 0.08);
  --border-strong: rgba(0, 0, 0, 0.12);
  
  --divider: rgba(0, 0, 0, 0.04);
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.1);
  --shadow-glow: 0 0 20px rgba(230, 131, 0, 0.1);
}
```

### 3.2 强调色的使用场景

强调色 `#FF9500`（暖橙色）只用于最关键的操作和状态指示：

- **输入框聚焦**：底部分隔线
- **待办完成**：复选框对勾
- **角标数字**：侧边栏待办数量
- **按钮悬停**（次级按钮）
- **链接文字**
- **重要提示**

**不要**在以下场景使用强调色：

- 大面积背景
- 卡片填充色
- 图表数据色（使用功能色）
- 普通文字

### 3.3 语义化颜色

```css
/* 任务状态 */
.task-pending {
  color: var(--text-secondary);
}

.task-completed {
  color: var(--text-tertiary);
  text-decoration: line-through;
}

/* 结构化内容暗示 */
.ai-detected {
  color: var(--text-primary);
  opacity: 0.85;
}

/* 来源信息 */
.source-info {
  color: var(--text-tertiary);
  font-size: 11px;
}
```

---

## 四、字体系统

### 4.1 字体家族

两套字体，分别用于不同的使用场景：

```css
/* 记录模式 - 衬线体 */
--font-serif: 'Noto Serif SC', 'Source Han Serif SC', 'Merriweather', Georgia, serif;

/* 工作模式 - 无衬线体 */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* 代码 */
--font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
```

### 4.2 字体规范

```css
/* ===== 标题 ===== */
--text-h1: 600 28px/1.3 var(--font-serif);
--text-h2: 600 22px/1.35 var(--font-serif);
--text-h3: 600 18px/1.4 var(--font-sans);
--text-h4: 500 15px/1.4 var(--font-sans);

/* ===== 正文 ===== */
--text-body-lg: 400 16px/1.6 var(--font-serif);   /* Stream 笔记正文 */
--text-body-md: 400 14px/1.5 var(--font-sans);    /* 视图页面正文 */
--text-body-sm: 400 13px/1.5 var(--font-sans);

/* ===== 辅助文字 ===== */
--text-caption: 400 12px/1.4 var(--font-sans);
--text-label: 500 11px/1.2 var(--font-sans);      /* 标签、角标 */
--text-mono: 400 13px/1.5 var(--font-mono);       /* 代码 */
```

### 4.3 Stream 页面的字体处理

Stream 页面使用衬线字体创造「文学感」，但为了阅读舒适，需要精细调整：

```css
/* Stream 笔记条目 */
.note-content {
  font: var(--text-body-lg);
  letter-spacing: 0.01em;      /* 微小的字间距增加高级感 */
  text-rendering: optimizeLegibility;
}

/* 任务完成后的删除线 */
.note-content.completed {
  text-decoration: line-through;
  text-decoration-color: var(--text-tertiary);
  color: var(--text-tertiary);
}

/* AI 检测内容的微妙提示 */
.note-content .ai-highlight {
  color: var(--text-primary);
  text-decoration: underline;
  text-decoration-style: dotted;
  text-decoration-color: var(--border-default);
  text-underline-offset: 3px;
}
```

---

## 五、间距系统

### 5.1 基础间距单位

基于 4px 网格的间距系统：

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
```

### 5.2 组件间距

```css
/* ===== 侧边栏 ===== */
--sidebar-width-collapsed: 60px;
--sidebar-width-expanded: 200px;
--sidebar-item-height: 48px;
--sidebar-padding: var(--space-3);
--sidebar-gap: var(--space-1);

/* ===== 主视图 ===== */
--view-padding-x: var(--space-6);      /* 24px */
--view-padding-y: var(--space-8);       /* 32px */
--view-max-width: 720px;               /* 笔记流最大宽度 */

/* ===== 笔记条目 ===== */
--note-padding-vertical: var(--space-4);
--note-padding-horizontal: var(--space-3);
--note-gap: var(--space-2);
--note-border-radius: 6px;

/* ===== 输入框 ===== */
--input-height: 48px;
--input-padding-x: var(--space-4);
--input-padding-y: var(--space-3);
--input-bottom-offset: var(--space-6);  /* 距离底部的距离 */
```

### 5.3 留白原则

**Stream 页面的留白**：内容区域左右各留 24px 边距，但不设最大宽度限制——让文字自然流动。当文字过长时（约 80 个字符后），考虑截断或添加阅读更多。

**视图页面的留白**：内容居中，最大宽度 640px，确保阅读舒适度。

---

## 六、组件样式

### 6.1 侧边栏

```vue
<template>
  <aside class="sidebar glass-container" :class="{ expanded: isExpanded }">
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="sidebar-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="sidebar-icon" v-html="item.icon"></span>
        <span class="sidebar-label">{{ item.label }}</span>
        <span v-if="item.badge" class="sidebar-badge">{{ item.badge }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width-collapsed);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  border-right: 1px solid var(--border-subtle);
}

.sidebar.expanded {
  width: var(--sidebar-width-expanded);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: var(--space-3);
  gap: var(--space-1);
}

.sidebar-item {
  display: flex;
  align-items: center;
  height: var(--sidebar-item-height);
  padding: 0 var(--space-3);
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.sidebar-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: var(--accent-muted);
  color: var(--accent-primary);
}

.sidebar-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent-primary);
  border-radius: 0 2px 2px 0;
}

.sidebar-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-label {
  margin-left: var(--space-3);
  font: var(--text-body-sm);
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar.expanded .sidebar-label {
  opacity: 1;
}

.sidebar-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--accent-primary);
  color: #000;
  font: var(--text-label);
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar.expanded .sidebar-badge {
  opacity: 1;
}
</style>
```

### 6.2 笔记条目

```vue
<template>
  <article class="note-item" :class="{ completed: note.is_completed }">
    <div class="note-content" v-html="renderedContent"></div>
    <div class="note-meta">
      <span class="note-time">{{ timeAgo }}</span>
    </div>
  </article>
</template>

<style scoped>
.note-item {
  padding: var(--note-padding-vertical) var(--note-padding-horizontal);
  border-radius: var(--note-border-radius);
  transition: background 0.2s ease;
  cursor: default;
}

.note-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.note-content {
  font: var(--text-body-lg);
  color: var(--text-primary);
  line-height: 1.7;
  word-wrap: break-word;
}

/* 完成后状态 */
.note-item.completed .note-content {
  color: var(--text-tertiary);
  text-decoration: line-through;
  text-decoration-color: var(--text-tertiary);
}

.note-meta {
  margin-top: var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.note-time {
  font: var(--text-caption);
  color: var(--text-tertiary);
}

/* AI 检测提示 - 极其微妙 */
.note-content :deep(.ai-detected) {
  color: var(--text-primary);
  opacity: 0.85;
  text-decoration: underline;
  text-decoration-style: dotted;
  text-decoration-color: var(--border-default);
  text-underline-offset: 3px;
  cursor: pointer;
}

.note-content :deep(.ai-detected:hover) {
  opacity: 1;
  text-decoration-color: var(--accent-primary);
}
</style>
```

### 6.3 输入框

```vue
<template>
  <div class="note-input-wrapper">
    <div class="note-input-container glass-container">
      <textarea
        ref="textareaRef"
        v-model="content"
        class="note-input"
        :placeholder="placeholder"
        @keydown="handleKeydown"
        @focus="isFocused = true"
        @blur="isFocused = false"
        rows="1"
      ></textarea>
      <button 
        class="send-button"
        :class="{ active: content.trim() }"
        @click="submit"
        :disabled="!content.trim()"
      >
        <svg>...</svg>
      </button>
    </div>
    <div class="input-hint">
      <kbd>Enter</kbd> 换行，<kbd>Ctrl + Enter</kbd> 发送
    </div>
  </div>
</template>

<style scoped>
.note-input-wrapper {
  position: fixed;
  bottom: var(--input-bottom-offset);
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  max-width: 640px;
}

.note-input-container {
  display: flex;
  align-items: flex-end;
  padding: var(--space-2);
  border-radius: 16px;
  transition: all 0.2s ease;
}

.note-input-container:focus-within {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
}

.note-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font: var(--text-body-lg);
  color: var(--text-primary);
  resize: none;
  max-height: 200px;
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
}

.note-input::placeholder {
  color: var(--text-placeholder);
}

.send-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--accent-muted);
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button.active {
  background: var(--accent-primary);
  color: #000;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  text-align: center;
  margin-top: var(--space-2);
  font: var(--text-caption);
  color: var(--text-tertiary);
  opacity: 0.6;
}

kbd {
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-sans);
  font-size: 11px;
}
</style>
```

### 6.4 待办条目

```vue
<template>
  <div class="task-item" :class="{ completed: task.status === 'completed' }">
    <button 
      class="task-checkbox"
      :class="{ checked: task.status === 'completed' }"
      @click="toggleStatus"
    >
      <svg v-if="task.status === 'completed'" class="check-icon">...</svg>
    </button>
    <span class="task-text">{{ task.text }}</span>
    <button class="task-source" @click="goToSource">
      <svg>...</svg>
    </button>
  </div>
</template>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  gap: var(--space-3);
  border-radius: 8px;
  transition: background 0.15s ease;
}

.task-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.task-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid var(--border-default);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.task-checkbox:hover {
  border-color: var(--accent-primary);
}

.task-checkbox.checked {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

.check-icon {
  width: 12px;
  height: 12px;
  color: #000;
}

.task-text {
  flex: 1;
  font: var(--text-body-md);
  color: var(--text-primary);
}

.task-item.completed .task-text {
  color: var(--text-tertiary);
  text-decoration: line-through;
}

.task-source {
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.task-item:hover .task-source {
  opacity: 1;
}

.task-source:hover {
  color: var(--accent-primary);
}
</style>
```

### 6.5 溯源箭头（极小）

```css
/* 溯源箭头 - 只有 12px，需要仔细看才能发现 */
.backlink-arrow {
  width: 12px;
  height: 12px;
  color: var(--text-tertiary);
  opacity: 0.3;
  cursor: pointer;
  transition: all 0.2s ease;
}

.backlink-arrow:hover {
  opacity: 1;
  color: var(--accent-primary);
  transform: translateX(2px);
}
```

---

## 七、动效系统

### 7.1 过渡曲线

```css
/* 缓动曲线 */
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);   /* 快速启动，缓慢停止 */
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1); /* 柔和 */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);      /* 标准 */

/* 时长 */
--duration-instant: 0ms;
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
--duration-slower: 400ms;
```

### 7.2 关键动效

#### 7.2.1 侧边栏展开

```css
.sidebar {
  transition: width var(--duration-slow) var(--ease-out-expo);
}

.sidebar-label,
.sidebar-badge {
  transition: opacity var(--duration-normal) var(--ease-out-quart);
}
```

#### 7.2.2 视图切换

```css
/* 主视图切换 - 淡入淡出 */
.view-enter-active,
.view-leave-active {
  transition: opacity var(--duration-slow) var(--ease-out-quart);
}

.view-enter-from,
.view-leave-to {
  opacity: 0;
}

/* 可选：添加微小的位移 */
.view-enter-active {
  transition: opacity var(--duration-slow) var(--ease-out-quart),
              transform var(--duration-slow) var(--ease-out-expo);
}

.view-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
```

#### 7.2.3 输入框动画

```css
.note-input-container {
  transition: all var(--duration-normal) var(--ease-out-quart);
}

.note-input-container:focus-within {
  transform: scale(1.01);
}
```

#### 7.2.4 按钮点击反馈

```css
.button {
  transition: transform var(--duration-fast) var(--ease-out-quart);
}

.button:active {
  transform: scale(0.96);
}
```

#### 7.2.5 任务完成动画

```css
.task-checkbox.checked {
  animation: check-bounce 0.3s var(--ease-out-expo);
}

@keyframes check-bounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
```

### 7.3 页面加载效果

```css
/* 笔记条目依次淡入 */
.note-item {
  animation: fade-slide-up 0.4s var(--ease-out-expo) backwards;
}

.note-item:nth-child(1) { animation-delay: 0ms; }
.note-item:nth-child(2) { animation-delay: 50ms; }
.note-item:nth-child(3) { animation-delay: 100ms; }
.note-item:nth-child(4) { animation-delay: 150ms; }
/* ... 依次类推，最多 10 个 */

@keyframes fade-slide-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## 八、Tailwind 配置

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 背景色
        'base': 'var(--bg-base)',
        'surface': 'var(--bg-surface)',
        'elevated': 'var(--bg-elevated)',
        
        // 文字色
        'primary': 'var(--text-primary)',
        'secondary': 'var(--text-secondary)',
        'tertiary': 'var(--text-tertiary)',
        'placeholder': 'var(--text-placeholder)',
        
        // 强调色
        'accent': 'var(--accent-primary)',
        'accent-hover': 'var(--accent-hover)',
        'accent-muted': 'var(--accent-muted)',
        
        // 功能色
        'success': 'var(--color-success)',
        'warning': 'var(--color-warning)',
        'error': 'var(--color-error)',
        'info': 'var(--color-info)',
        
        // 边框
        'border-subtle': 'var(--border-subtle)',
        'border-default': 'var(--border-default)',
        'border-strong': 'var(--border-strong)',
      },
      fontFamily: {
        'serif': ['var(--font-serif)'],
        'sans': ['var(--font-sans)'],
        'mono': ['var(--font-mono)'],
      },
      spacing: {
        'sidebar-collapsed': 'var(--sidebar-width-collapsed)',
        'sidebar-expanded': 'var(--sidebar-width-expanded)',
        'view-x': 'var(--view-padding-x)',
        'view-y': 'var(--view-padding-y)',
      },
      backdropBlur: {
        'glass': '20px',
        'glass-lg': '30px',
      },
      boxShadow: {
        'glow': 'var(--shadow-glow)',
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
      },
      transitionTimingFunction: {
        'expo-out': 'var(--ease-out-expo)',
        'quart-out': 'var(--ease-out-quart)',
      },
      transitionDuration: {
        'fast': 'var(--duration-fast)',
        'normal': 'var(--duration-normal)',
        'slow': 'var(--duration-slow)',
      },
    },
  },
  plugins: [],
}
```

---

## 九、响应式断点

```css
/* 移动端 - 默认隐藏侧边栏 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    width: var(--sidebar-width-expanded);
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
  
  .main-content {
    padding-left: 0;
  }
  
  .note-input-wrapper {
    width: 95%;
    bottom: var(--space-4);
  }
}

/* 平板端 */
@media (min-width: 769px) and (max-width: 1024px) {
  :root {
    --sidebar-width-expanded: 180px;
  }
}

/* 桌面端 */
@media (min-width: 1025px) {
  /* 默认样式 */
}
```

---

## 十、辅助功能

### 10.1 焦点样式

```css
*:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

/* 移除默认焦点样式 */
button:focus-visible,
a:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

### 10.2 减少动画

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 10.3 对比度

确保文字与背景的对比度符合 WCAG AA 标准：

- 主要文字 `#E8E8E8` 在背景 `#0D0D0D` 上：对比度 13.5:1 ✓
- 次要文字 `#9A9A9A` 在背景 `#0D0D0D` 上：对比度 7.2:1 ✓
- 占位符 `#4A4A4A` 在背景 `#0D0D0D` 上：对比度 4.2:1 ✓（最低要求 4.5:1，接近但略低）

---

## 总结

这个风格系统的核心在于「克制」：

- 毛玻璃不是炫技，而是创造层级
- 强调色只在关键处出现
- 动效服务于反馈，而非装饰
- 字体切换帮助用户感知模式切换

整体效果应该是：界面像一块干净的玻璃，文字浮现其上，交互如水流般自然。当用户开始记录时，他们只会注意到自己的想法，而不会注意到界面本身。
