# Stream Note 前端代码知识文档（更新版）

## 1. 技术栈与启动

- 框架：Vue 3 + TypeScript + Pinia + Vue Router
- 编辑器：TipTap（`@tiptap/vue-3` + `starter-kit` + `placeholder`）
- 构建：Vite 5
- 样式：TailwindCSS + CSS Variables（`tokens.css`）
- API 调用：Axios（统一前缀 `/api/v1`）
- 本地存储：localforage（离线优先）
- 国际化：自定义 `useI18n` composable（支持中/英文）

常用命令（`stream-note-web/`）：

```bash
npm install
npm run dev
npm run build
npm run test
```

## 2. 目录与职责

```
stream-note-web/src/
├── main.ts                    # 应用入口，挂载 Pinia 和 Router
├── App.vue                    # 整体布局（Sidebar + router-view + MobileTabbar）
├── router/
│   └── index.ts               # 路由定义 + 路由守卫
├── views/
│   ├── AuthView.vue           # 登录/注册页面
│   ├── StreamView.vue         # 流式编辑器页面 + 文档恢复面板
│   ├── TasksView.vue          # 任务列表页面 + AI 分析入口
│   └── SettingsView.vue       # 设置页面（AI Provider、语言、主题）
├── stores/
│   ├── pinia.ts               # Pinia 实例
│   ├── auth.ts                # 认证状态管理
│   ├── document.ts            # 文档状态 + localforage 离线存储
│   └── tasks.ts               # 任务列表 + 状态切换 + 自动刷新
├── services/
│   └── api.ts                 # 所有后端请求封装
├── components/
│   ├── layout/
│   │   ├── Sidebar.vue        # 桌面端侧边栏导航
│   │   └── MobileTabbar.vue   # 移动端底部导航栏
│   ├── tasks/
│   │   └── TaskItem.vue       # 任务项 + 删除功能
│   └── glass/
│       └── SharedLiquidGlass.vue  # 液态玻璃效果组件
├── composables/
│   ├── useI18n.ts             # 国际化 composable
│   └── usePrimaryNavigation.ts    # 主导航逻辑 + 任务徽章
├── types/
│   ├── document.ts            # 文档类型定义
│   └── task.ts                # 任务类型定义
├── config/
│   ├── liquid-glass.ts        # 液态玻璃配置
│   └── task-liquid-glass.ts   # 任务卡片液态玻璃配置
├── lib/
│   ├── document-utils.ts      # 文档工具函数
│   └── liquid-glass/          # 液态玻璃效果实现
└── assets/
    └── styles/
        ├── tokens.css         # 设计令牌
        └── base.css           # 基础样式 + 实体语义类
```

## 3. 路由配置

```typescript
// src/router/index.ts
routes: [
  { path: '/', redirect: '/stream' },
  { path: '/auth', name: 'auth', component: AuthView },
  { path: '/stream', name: 'stream', component: StreamView, meta: { requiresAuth: true } },
  { path: '/tasks', name: 'tasks', component: TasksView, meta: { requiresAuth: true } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } }
]
```

**路由守卫**：
```typescript
router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia)
  await authStore.initialize()

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth === true)
  if (requiresAuth && !authStore.isAuthenticated) {
    return { name: 'auth' }  // 未认证跳转登录页
  }
  if (to.name === 'auth' && authStore.isAuthenticated) {
    return { name: 'stream' }  // 已认证跳转主页
  }
  return true
})
```

## 4. 认证系统

### 4.1 认证流程

```
┌─────────────────────────────────────────────────────────────┐
│                      AuthView.vue                            │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ 登录标签页    │    │ 注册标签页    │                       │
│  │ username     │    │ username     │                       │
│  │ password     │    │ password     │                       │
│  │ [登录按钮]    │    │ [创建账号]    │                       │
│  └──────┬───────┘    └──────┬───────┘                       │
└─────────┼───────────────────┼────────────────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                       auth.ts store                          │
│  login(username, password)    register(username, password)  │
└─────────┬───────────────────────────────────┬───────────────┘
          │                                   │
          ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 端点                                │
│  POST /auth/login              POST /auth/register          │
│  → { access_token, user }      → { access_token, user }     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Token 管理

- **存储位置**：`localStorage`（key: `stream-note-auth-token`）
- **自动附加**：Axios 请求拦截器自动添加 `Authorization: Bearer <token>`
- **401 处理**：响应拦截器自动清除过期 Token

### 4.3 Auth Store API

```typescript
export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isReady = ref(false)
  const isLoading = ref(false)
  const isAuthenticated = computed(() => user.value !== null && getStoredAuthToken() !== null)

  const initialize = async () => { /* 恢复会话 */ }
  const register = async (username, password) => { /* 注册 */ }
  const login = async (username, password) => { /* 登录 */ }
  const logout = () => { /* 登出 */ }

  return { user, isReady, isLoading, isAuthenticated, initialize, register, login, logout }
})
```

## 5. 文档系统（离线优先）

### 5.1 加载流程

```
用户访问 /stream
       │
       ▼
documentStore.loadDocument()
       │
       ├─── 1. 从 localforage 读取本地缓存
       │         │
       │         ▼
       │    content.value = localDoc（立即显示）
       │
       └─── 2. 从服务器拉取最新
              │
              ▼
         GET /documents
              │
              ├── 本地无缓存 → 使用服务器内容
              └── 本地有缓存 → 保留本地（下次保存时同步）
```

### 5.2 保存流程

```
TipTap onUpdate 事件
       │
       ▼
documentStore.updateContent(json)
       │
       └─── 立即保存到 localforage（确保本地持久化）
       
debouncedSave(json) [500ms]
       │
       ▼
documentStore.saveDocument(json)
       │
       ├── 1. 保存到 localforage
       └── 2. PUT /documents/current（后台同步）
              │
              └── 触发后端静默分析
```

### 5.3 文档恢复系统

**恢复面板位置**：`StreamView.vue` 右上角

**候选类型**：
| 类型 | 说明 |
|------|------|
| `latest` | 最近可用版本 |
| `yesterday` | 昨日版本（24 小时前） |
| `stable` | 稳定版本（字符数最多） |

**API**：
- `GET /documents/recovery/candidates` → 获取候选列表
- `POST /documents/recovery/{revision_id}/restore` → 恢复指定版本

**流程**：
1. 点击"恢复"按钮 → 展开候选列表
2. 点击"恢复此版本" → 调用恢复 API
3. 文档内容更新 → 编辑器自动刷新
4. 可点击"撤销上次恢复" → 回退到恢复前状态

## 6. 任务管理

### 6.1 任务列表功能

- 按 `created_at` 倒序显示
- **已完成任务 24 小时后自动隐藏**
- 切换显示/隐藏已完成任务
- 点击卡片切换完成状态
- **删除任务**（带二次确认）

### 6.2 任务摘要自动刷新

```typescript
// src/stores/tasks.ts
const startSummaryAutoRefresh = (intervalMs = 10000) => {
  summaryPollTimer.value = setInterval(() => {
    void loadSummary(false)
  }, intervalMs)
}

// 窗口获得焦点时也刷新
window.addEventListener('focus', refreshSummary)
document.addEventListener('visibilitychange', handleVisibilityChange)
```

### 6.3 任务可见性逻辑

后端自动隐藏 24 小时前的已完成任务：
```python
# app/api/v1/endpoints/tasks.py
HIDE_COMPLETED_AFTER_HOURS = 24
completed_cutoff = datetime.now(UTC) - timedelta(hours=HIDE_COMPLETED_AFTER_HOURS)
visibility_clause = or_(
    TaskCache.status != "completed",
    TaskCache.updated_at > completed_cutoff,
)
```

## 7. 静默 AI 分析

后端实现了 `silent_analysis.py` 后台 Worker：

```
用户保存文档
       │
       ▼
PUT /documents/current
       │
       └── enqueue_silent_analysis()
              │
              ▼
       SilentAnalysisWorker（后台线程）
              │
              ├── 轮询待分析任务（0.8 秒间隔）
              │
              └── 处理未分析的块（批量 20 个）
                     │
                     └── AI 提取任务 → 写入 TaskCache
```

**配置项（环境变量）**：
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SILENT_ANALYSIS_ENABLED` | `1` | 是否启用 |
| `SILENT_ANALYSIS_IDLE_SECONDS` | `6.0` | 空闲时间 |
| `SILENT_ANALYSIS_POLL_SECONDS` | `0.8` | 轮询间隔 |
| `SILENT_ANALYSIS_BATCH_SIZE` | `20` | 批量大小 |
| `SILENT_ANALYSIS_MAX_RETRY` | `3` | 最大重试次数 |

## 8. 国际化

### 8.1 useI18n Composable

```typescript
export const useI18n = () => {
  const locale = ref<Locale>('zh' | 'en')
  const setLocale = (nextLocale: Locale) => { /* 切换语言 */ }
  const t = (key: MessageKey) => messages[locale.value][key]
  const getDateTimeLocale = () => locale.value === 'zh' ? 'zh-CN' : 'en-US'

  return { locale, setLocale, t, getDateTimeLocale }
}
```

### 8.2 特性

- 默认语言：中文（`zh`）
- 浏览器语言自动检测
- 语言偏好存储在 `localStorage`（key: `stream-note-locale`）
- 切换语言时自动更新 `<html lang>` 属性

### 8.3 使用示例

```vue
<script setup>
import { useI18n } from '@/composables/useI18n'
const { locale, setLocale, t } = useI18n()
</script>

<template>
  <button @click="setLocale('en')">English</button>
  <p>{{ t('tasksTitle') }}</p>
</template>
```

## 9. 设置页面

### 9.1 功能模块

| 模块 | 功能 |
|------|------|
| 账户 | 显示用户名 + 登出按钮 |
| 语言 | 中文 / English 切换 |
| 主题 | 亮色 / 暗色 / 跟随系统 |
| AI Provider | 提供商选择、模型、Base URL、API Key |
| 高级 | 超时时间、重试次数、推理模式开关 |
| 测试 | 连接测试按钮 |

### 9.2 支持的 AI Provider

| Provider | 说明 |
|----------|------|
| `openai_compatible` | 任意 OpenAI 兼容端点 |
| `openai` | 官方 OpenAI 端点 |
| `siliconflow` | SiliconFlow（使用 enable_thinking 开关） |
| `ollama` | 本地 Ollama 服务 |

### 9.3 主题切换

```typescript
// 使用 @vueuse/core 的 useStorage
const themePreference = useStorage<'system' | 'light' | 'dark'>(
  'stream-note-theme-preference',
  'system'
)
```

**注意**：主题切换逻辑已实现，但暗色主题样式未完全实现。

## 10. API 契约（前端视角）

### 10.1 认证

```typescript
// 登录/注册
POST /auth/register → { access_token, token_type, user }
POST /auth/login    → { access_token, token_type, user }
GET /auth/me        → { id, username, created_at }
```

### 10.2 文档

```typescript
GET /documents                    → Document | 404
POST /documents                   → Document
PUT /documents/current            → Document
PATCH /documents/{document_id}    → Document

// 恢复系统
GET /documents/recovery/candidates
  → { candidates: DocumentRecoveryCandidate[] }
POST /documents/recovery/{revision_id}/restore
  → { document, restored_revision_id, undo_revision_id }
```

### 10.3 任务

```typescript
GET /tasks?include_hidden=...     → Task[]
GET /tasks/summary?include_hidden → { pending_count, completed_count, total_count }
POST /tasks/{id}/commands/toggle  → { task, summary }
DELETE /tasks/{id}                → { deleted_task_id, summary }
PATCH /tasks/{id}                 → Task
```

### 10.4 AI

```typescript
POST /ai/extract                  → { tasks_found, tasks }
POST /ai/analyze-pending?force=   → { analyzed_count, tasks_found, tasks }
POST /ai/reset-debug-state        → { deleted_tasks, reset_blocks }

// Provider 配置
GET /ai/provider-settings         → AIProviderSettings
PUT /ai/provider-settings         → AIProviderSettings
POST /ai/provider-settings/test   → { ok, latency_ms, message }
```

## 11. 样式系统

### 11.1 设计令牌（tokens.css）

- `--font-sans`：无衬线字体栈
- `--font-serif`：衬线字体栈（用于 Stream 编辑器）
- `--font-mono`：等宽字体栈
- `--color-accent`：强调色 RGB 值
- `--text-primary/secondary/tertiary`：文字颜色
- `--safe-top/right/bottom/left`：安全区域

### 11.2 实体语义类

| 类名 | 用途 |
|------|------|
| `ui-stage` | 桌面环境层 |
| `ui-shell` | 布局壳 |
| `ui-main` | 主内容区 |
| `ui-sidebar-surface` | 侧边栏 |
| `ui-nav-item` | 导航项 |
| `ui-task-card` | 任务卡片 |
| `ui-editor-surface` | 编辑器容器 |
| `ui-btn` | 按钮 |
| `ui-pill` | 状态标签 |

## 12. 移动端适配

- `MobileTabbar.vue`：底部标签栏导航
- 响应式断点：`@media (max-width: 900px)`
- 安全区域：`--safe-top/right/bottom/left`

## 13. 关键文件索引

```
stream-note-web/src/
├── main.ts
├── App.vue
├── router/index.ts
├── views/
│   ├── AuthView.vue
│   ├── StreamView.vue
│   ├── TasksView.vue
│   └── SettingsView.vue
├── stores/
│   ├── auth.ts
│   ├── document.ts
│   └── tasks.ts
├── services/api.ts
├── components/
│   ├── layout/
│   │   ├── Sidebar.vue
│   │   └── MobileTabbar.vue
│   └── tasks/TaskItem.vue
├── composables/
│   ├── useI18n.ts
│   └── usePrimaryNavigation.ts
└── types/
    ├── document.ts
    └── task.ts
```
