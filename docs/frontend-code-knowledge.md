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
- 若本地无 `documentId`，先 `POST /documents` 创建
- 再 `PATCH /documents/{id}` 更新 `content`

### 3.2 任务提取与任务列表刷新

在 `StreamView.vue` 有两个调试入口：

- `runAIExtract()` -> `POST /ai/extract`（基于当前编辑器 JSON）
- `analyzePending()` -> `POST /ai/analyze-pending`（后端读取已存文档并分析前 10 段）
- `resetAIState()` -> `POST /ai/reset-debug-state`（清空任务缓存并重置块分析状态）

两者成功后都会执行 `tasksStore.loadTasks()` 重新拉取任务列表。

### 3.3 任务状态切换

`TaskItem.vue` 点击复选框后：

1. 调用 `tasksStore.toggleTaskStatus(task.id)`
2. store 先 `PATCH /tasks/{taskId}` 更新任务状态
3. 再 `PATCH /blocks/{blockId}` 同步块完成状态
4. 前端本地 `task.status` 直接更新

## 4. API 契约（前端视角）

`src/services/api.ts` 当前封装接口：

- `GET /documents` -> `Document | 404`
- `POST /documents`
- `PATCH /documents/{id}`
- `GET /tasks`
- `PATCH /tasks/{id}`（body: `{ status }`）
- `PATCH /blocks/{id}`（body: `{ is_completed }`）
- `POST /ai/extract`
- `POST /ai/analyze-pending`
- `POST /ai/reset-debug-state`

类型定义关键字段：

- `Document`: `id`, `content`, `created_at`, `updated_at`
- `Task`: `id`, `block_id`, `text`, `status`, `due_date`, `raw_time_expr`, `created_at`

## 5. 样式系统

- 全局 token 在 `src/assets/styles/tokens.css`
- 基础层和 utility 在 `src/assets/styles/base.css`
- 玻璃态容器复用类：`.glass-container` / `.glass-elevated`
- 颜色、字体、间距优先使用 CSS 变量，不建议组件内写死

## 6. 扩展开发入口

- 新页面：`src/views` + `src/router/index.ts`
- 新状态域：新增 Pinia store（`src/stores`）
- 新后端接口：先在 `src/services/api.ts` 追加函数，再在 store 或 view 调用
- 新任务 UI 交互：`src/components/tasks/TaskItem.vue`

## 7. 当前实现注意事项

- 自动保存逻辑已统一在 `StreamView.vue` 的 `debouncedSave`，未再保留未接入的 composable
- `DocumentContent` 已对齐 TipTap 的 `JSONContent` 类型，避免前端手写结构与编辑器返回值漂移
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
