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

**路由守卫**：所有 `requiresAuth: true` 的路由需要认证，未认证自动跳转 `/auth`。

## 4. 认证系统

### 4.1 认证流程

- 用户访问 `/auth`，看到登录/注册表单（标签页切换）
- 注册：调用 `POST /api/v1/auth/register`，获取 token 并存储
- 登录：调用 `POST /api/v1/auth/login`，获取 token 并存储
- Token 存储在 `localStorage`（key: `stream-note-auth-token`）
- 后续请求通过 Axios 拦截器自动附带 `Authorization: Bearer <token>`

### 4.2 Auth Store（`src/stores/auth.ts`）

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

1. 进入 `/stream` 页面时，`documentStore.loadDocument()` 被调用
2. 首先从 **localforage** 读取本地缓存（立即显示）
3. 然后通过 `GET /documents` 拉取服务器文档
4. 如果本地无缓存，使用服务器内容；否则保留本地

### 5.2 保存流程

1. TipTap 编辑器内容变化时触发 `onUpdate`
2. `updateContent(json)` 立即保存到 localforage
3. `debouncedSave(json)`（500ms）调用 `saveDocument()`
4. `saveDocument()` 先保存到 localforage，再调用 `PUT /documents/current`
5. 后端保存时自动触发静默 AI 分析

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

## 6. 任务管理

### 6.1 功能列表

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
```

## 7. 静默 AI 分析

后端实现了 `silent_analysis.py` 后台 Worker：

- 文档保存时自动触发 `enqueue_silent_analysis()`
- Worker 在后台线程自动分析未处理的块
- 用户无需手动触发，AI 自动识别任务
- 可通过环境变量配置（`SILENT_ANALYSIS_ENABLED` 等）

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

## 10. API 契约（前端视角）

### 10.1 认证
```typescript
POST /auth/register → { access_token, token_type, user }
POST /auth/login    → { access_token, token_type, user }
GET /auth/me        → { id, username, created_at }
```

### 10.2 文档
```typescript
GET /documents                    → Document | 404
POST /documents                   → Document
PUT /documents/current            → Document
GET /documents/recovery/candidates → { candidates: [...] }
POST /documents/recovery/{id}/restore → { document, restored_revision_id, undo_revision_id }
```

### 10.3 任务
```typescript
GET /tasks?include_hidden=...     → Task[]
GET /tasks/summary?include_hidden → { pending_count, completed_count, total_count }
POST /tasks/{id}/commands/toggle  → { task, summary }
DELETE /tasks/{id}                → { deleted_task_id, summary }
```

### 10.4 AI
```typescript
POST /ai/extract                  → { tasks_found, tasks }
POST /ai/analyze-pending?force=   → { analyzed_count, tasks_found, tasks }
GET /ai/provider-settings         → AIProviderSettings
PUT /ai/provider-settings         → AIProviderSettings
POST /ai/provider-settings/test   → { ok, latency_ms, message }
```

## 11. 样式系统

- 全局 token：`src/assets/styles/tokens.css`
- 实体风格定义：`src/assets/styles/base.css`
- 设计原则：Clear 拟物分层（底面 vs 亚克力块）

## 12. 移动端适配

- `MobileTabbar.vue`：底部标签栏导航
- 响应式断点：`@media (max-width: 900px)`
- 安全区域：`--safe-top/right/bottom/left`

## 13. 当前实现注意事项

- **离线优先**：文档优先保存到 localforage，后台同步到服务器
- **静默分析**：后端 Worker 自动分析，前端无需手动触发
- **文档恢复**：支持多版本恢复 + 撤销
- **任务可见性**：已完成任务 24 小时后自动隐藏
- **任务摘要轮询**：10 秒自动刷新，窗口获得焦点时刷新
- **国际化**：完整支持中/英文
- **认证**：完整的登录/注册/登出流程
- **主题**：支持亮/暗/跟随系统切换（样式未完全实现）

## 14. 关键文件索引

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
