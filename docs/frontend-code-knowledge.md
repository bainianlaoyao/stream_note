# Stream Note 前端代码知识文档

## 1. 技术栈与启动

- 框架：Vue 3 + TypeScript + Pinia + Vue Router
- 编辑器：TipTap（`@tiptap/vue-3` + `starter-kit` + `placeholder`）
- 构建：Vite 5
- 样式：TailwindCSS + CSS Variables（`tokens.css`）
- API 调用：Axios（统一前缀 `/api/v1`）

常用命令（`stream-note-web/`）：

```bash
npm install
npm run dev
npm run build
npm run test
```

## 2. 目录与职责

- `src/main.ts`：应用入口，挂载 Pinia 和 Router
- `src/App.vue`：整体布局，左侧 `Sidebar` + 右侧 `router-view`
- `src/router/index.ts`：路由定义（`/stream`、`/tasks`）
- `src/views/StreamView.vue`：流式编辑器页面 + AI 分析触发入口
- `src/views/TasksView.vue`：任务列表页面
- `src/stores/document.ts`：文档状态与持久化
- `src/stores/tasks.ts`：任务列表与状态切换
- `src/services/api.ts`：所有后端请求封装
- `src/components/layout/Sidebar.vue`：导航栏
- `src/components/tasks/TaskItem.vue`：任务项展示与交互
- `src/types/*.ts`：前端数据类型

## 3. 运行时主流程

### 3.1 文档加载与保存

1. 进入 `/stream` 页面时，`StreamView.vue` 在 `onMounted` 调用 `documentStore.loadDocument()`
2. `loadDocument()` 通过 `GET /documents` 拉取唯一文档
3. TipTap 编辑器内容变化时触发 `onUpdate`
4. `onUpdate` 中同时：
- `documentStore.updateContent(json)` 更新本地状态
- `debouncedSave(json)`（500ms）调用 `documentStore.saveDocument(json)`
5. `saveDocument()` 逻辑：
- 直接调用 `PUT /documents/current` 做单文档 upsert
- 前端不再决定“先创建还是更新”

### 3.2 任务提取与任务列表刷新

在 `StreamView.vue` 有两个调试入口：

- `runAIExtract()` -> `POST /ai/extract`（基于当前编辑器 JSON）
- `analyzePending()` -> `POST /ai/analyze-pending`（后端读取已存文档并分析前 10 段）
- `resetAIState()` -> `POST /ai/reset-debug-state`（清空任务缓存并重置块分析状态）

两者成功后都会执行 `tasksStore.loadTasks()` 重新拉取任务列表。

### 3.3 任务状态切换

`TaskItem.vue` 点击复选框后：

1. 调用 `tasksStore.toggleTaskStatus(task.id)`
2. store 调用 `POST /tasks/{taskId}/commands/toggle` 发送命令
3. 后端原子完成任务状态切换与块完成状态同步
4. 前端只使用接口返回的 `task + summary` 刷新展示

## 4. API 契约（前端视角）

`src/services/api.ts` 当前封装接口：

- `GET /documents` -> `Document | 404`
- `PUT /documents/current`
- `GET /tasks`
- `GET /tasks/summary`
- `POST /tasks/{id}/commands/toggle`
- `POST /ai/extract`
- `POST /ai/analyze-pending`
- `POST /ai/reset-debug-state`

类型定义关键字段：

- `Document`: `id`, `content`, `created_at`, `updated_at`
- `Task`: `id`, `block_id`, `text`, `status`, `due_date`, `raw_time_expr`, `created_at`

## 5. 样式系统与 UI 实体语义

- 全局 token：`src/assets/styles/tokens.css`
- 实体风格定义：`src/assets/styles/base.css`
- 组件模板以 Tailwind utility + 语义实体类混合使用

### 5.0 Clear 拟物分层原则（最新）

- 最底层（`Desk / Paper`）只承载环境与阅读面：例如 Stream 页面背景、侧边栏背景、主内容底面。
- 上层（`Acrylic Blocks`）统一承载交互实体：按钮、卡片、任务条目、chip、pill、popover、命令岛等。
- 设计判断优先级：先判断“是否是底面”，再决定是否使用亚克力块语义；不要把底面做成漂浮卡片。
- 旧命名里的 `glass-*` 仅作为兼容别名，语义解释统一按“亚克力块”理解。

### 5.1 实体列表（Entity -> 语义）

| 实体类名 | 语义 | 典型使用位置 |
| --- | --- | --- |
| `ui-stage` | 桌面环境层（最底层） | `src/App.vue` 顶层容器 |
| `ui-ambient-orb-a` / `ui-ambient-orb-b` | 环境光层（附着在桌面层，不视为独立物件） | `src/App.vue` 背景装饰元素 |
| `ui-shell` | 纸面布局壳（承载左栏 + 主内容） | `src/App.vue` 主布局容器 |
| `ui-main` | 主纸面工作区 | `src/App.vue` 右侧内容区域 |
| `ui-surface-card` | 亚克力小块通用卡面 | `StreamView`、`TasksView` 各面板 |
| `ui-sidebar-surface` | 侧边纸面（属于底层，不是漂浮块） | `Sidebar.vue` 根容器 |
| `ui-sidebar-divider` | 左栏与主区的物理分隔光线 | `Sidebar.vue` |
| `ui-sidebar-brand*` | 左栏品牌区实体（图标、标题、副标题） | `Sidebar.vue` |
| `ui-sidebar-nav` | 左栏导航组容器 | `Sidebar.vue` |
| `ui-nav-item` | 左栏导航项基础状态 | `Sidebar.vue` |
| `ui-nav-item.is-active` | 左栏导航项激活状态 | `Sidebar.vue` |
| `ui-nav-icon` / `ui-nav-label` / `ui-nav-badge` | 导航项图标、文本、徽标 | `Sidebar.vue` |
| `ui-btn` | 通用按钮基础风格 | `StreamView`、`TaskItem` |
| `ui-btn-primary` | 主按钮语义（主行动） | `StreamView` 的 Analyze Current |
| `ui-btn-ghost` | 次按钮语义（次行动） | `StreamView` / `TaskItem` |
| `ui-pill` | 状态胶囊基础语义 | `StreamView` 分析反馈 |
| `ui-pill-strong` | 强调胶囊语义（错误/重点提示） | `StreamView` 错误反馈 |
| `ui-chip` | 轻量标签语义 | `StreamView` 顶部 `Live` 标签 |
| `ui-count-chip` | 数量统计语义 | `TasksView` pending 计数 |
| `ui-editor-surface` | 编辑器纸面语义（偏内容容器，不强调漂浮） | `StreamView` 的 TipTap 容器 |
| `ui-task-card` | 任务亚克力块语义 | `TaskItem.vue` |
| `ui-task-card.is-completed` | 任务卡片完成态语义 | `TaskItem.vue` |
| `ui-task-check` / `ui-task-check.is-checked` | 亚克力控件语义（复选） | `TaskItem.vue` |
| `ui-task-text` / `ui-task-text.is-completed` | 任务文本语义（正常/完成） | `TaskItem.vue` |
| `ui-meta-pill` | 亚克力胶囊元信息语义（时间、来源） | `TaskItem.vue` |

### 5.2 风格约束（维护规范）

- 新增页面时，先定义底层是否为“桌面/纸”，再把交互部件映射成“亚克力小块”，避免层级语义混乱。
- 新增视觉层级时，先在 `base.css` 增加语义实体，再在页面引用；不要直接在业务组件里拼复杂视觉参数。
- 业务组件只表达“语义”（如主按钮/任务卡片/元信息胶囊），不内联硬编码材质参数。
- 保留 `glass-panel` / `glass-chip` 作为兼容别名，但新代码统一用 `ui-*` 实体和 Clear 语义命名。

## 6. 扩展开发入口

- 新页面：`src/views` + `src/router/index.ts`
- 新状态域：新增 Pinia store（`src/stores`）
- 新后端接口：先在 `src/services/api.ts` 追加函数，再在 store 或 view 调用
- 新任务 UI 交互：`src/components/tasks/TaskItem.vue`

## 7. 当前实现注意事项

- 自动保存逻辑已统一在 `StreamView.vue` 的 `debouncedSave`，未再保留未接入的 composable
- `DocumentContent` 已对齐 TipTap 的 `JSONContent` 类型，避免前端手写结构与编辑器返回值漂移
- `tasksStore` 不再在前端推导业务状态，任务切换与统计完全依赖后端返回
- `TaskItem.vue` 的“跳转到来源”仅设置 query 参数 `blockId`，`StreamView.vue` 目前未消费该 query 做定位
- `src/assets/styles/tokens.css` 的 `--font-serif` 已修正为可读字体栈（含 `Source Han Serif SC` / `Noto Serif SC`）

## 8. 关键文件索引

- `stream-note-web/src/main.ts`
- `stream-note-web/src/App.vue`
- `stream-note-web/src/router/index.ts`
- `stream-note-web/src/views/StreamView.vue`
- `stream-note-web/src/views/TasksView.vue`
- `stream-note-web/src/stores/document.ts`
- `stream-note-web/src/stores/tasks.ts`
- `stream-note-web/src/services/api.ts`
- `stream-note-web/src/components/layout/Sidebar.vue`
- `stream-note-web/src/components/tasks/TaskItem.vue`
