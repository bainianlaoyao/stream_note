# Stream Note MVP 实施计划

## TL;DR

> **Quick Summary**: 实现一个极简流式笔记应用的核心功能 - Stream 编辑器（TipTap）+ Tasks 视图，使用 OpenAI Compatible API 进行任务识别和时间解析。
> 
> **Deliverables**:
> - 前端: Vue 3 + TipTap 编辑器 + Tasks 视图
> - 后端: FastAPI + SQLite 数据存储
> - AI 服务: 任务识别 + 时间解析
> - 核心功能: 自动保存、溯源跳转、任务完成状态

> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Frontend Setup → TipTap Editor → AI Service → Tasks View → Integration

---

## Context

### Original Request
实施 Stream Note 的 MVP 版本，包含主要的笔记界面（Stream）和 Todo 界面（Tasks），使用 OpenAI Compatible API 进行 AI 识别。

### Interview Summary
**Key Discussions**:
- **交互模式变更**: Stream 页面从"笔记列表"变为"单一富文本编辑器"，使用 TipTap
- **数据模型变更**: 从 Note 表变为 Document + Block 模型
- **AI 触发时机**: 惰性触发，2分钟无输入后开始识别
- **任务完成反馈**: 对应块显示删除线

**Research Findings**:
- STREAM_NOTE_PLANNING.md: 已有完整架构设计，需调整适应新模型
- STREAM_NOTE_STYLE_GUIDE.md: 毛玻璃视觉系统可直接复用

### Metis Review
**Identified Gaps** (addressed):
- Guardrails: MVP 无认证、无 WebSocket/Celery/Redis
- Edge Cases: AI 错误处理、时区、级联删除、幂等性
- 安全: API Key 仅服务端，v-html 需要 XSS 处理

---

## Work Objectives

### Core Objective
实现一个可用的 MVP，用户可以在 Stream 编辑器中自由输入内容，AI 自动识别任务和时间，用户可以在 Tasks 视图中管理任务并通过溯源跳转回 Stream。

### Concrete Deliverables
- `stream-note-web/` - Vue 3 前端项目
- `stream-note-api/` - FastAPI 后端项目
- TipTap 编辑器，支持块级别管理
- Tasks 视图，支持状态切换和时间显示
- OpenAI Compatible AI 服务

### Definition of Done
- [ ] `npm run dev` 启动前端，localhost:5173 可访问
- [ ] `uvicorn app.main:app` 启动后端，localhost:8000 可访问
- [ ] 用户可以在 Stream 编辑器中输入内容，自动保存
- [ ] AI 识别任务并在 Tasks 视图显示
- [ ] 点击任务可跳转到 Stream 对应位置
- [ ] 完成任务后块显示删除线

### Must Have
- TipTap 编辑器
- 块级别内容管理
- AI 任务识别（OpenAI Compatible）
- Tasks 视图
- 自动保存
- 溯源跳转

### Must NOT Have (Guardrails)
- 用户认证系统
- WebSocket / Celery / Redis
- Calendar / Ideas / Code 视图
- 桌面端封装 (Tauri)
- 前端暴露 API Key

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (需从头搭建)
- **Automated tests**: YES (TDD)
- **Framework**: Vitest (frontend) + pytest (backend)
- **TDD**: Each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **API/Backend**: Use Bash (curl) — Send requests, assert status + response fields
- **Library/Module**: Use Bash (pytest/vitest) — Run tests, assert pass

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — 项目脚手架 + 基础设施):
├── Task 1: Frontend 项目初始化 (Vue 3 + Vite + Tailwind) [quick]
├── Task 2: Backend 项目初始化 (FastAPI + SQLAlchemy) [quick]
├── Task 3: 设计令牌和基础样式 (复用 STYLE_GUIDE) [quick]
├── Task 4: 数据库模型设计 (Document, Block, TaskCache) [quick]
├── Task 5: API 客户端封装 [quick]
└── Task 6: 环境配置和 .env 模板 [quick]

Wave 2 (After Wave 1 — 核心功能实现):
├── Task 7: TipTap 编辑器集成 [unspecified-high]
├── Task 8: 块管理逻辑 (Enter 分割 + ID 生成) [deep]
├── Task 9: 自动保存功能 (防抖 + 持久化) [quick]
├── Task 10: Document API (CRUD) [quick]
├── Task 11: Block API (查询 + 状态更新) [quick]
├── Task 12: AI 服务 - OpenAI Compatible 封装 [deep]
├── Task 13: 任务提取 Prompt 设计 [deep]
└── Task 14: 时间解析逻辑 [unspecified-high]

Wave 3 (After Wave 2 — Tasks 视图 + 集成):
├── Task 15: Tasks 视图 UI [visual-engineering]
├── Task 16: TaskItem 组件 (状态切换 + 时间显示) [quick]
├── Task 17: Task API (列表 + 状态更新) [quick]
├── Task 18: 溯源跳转功能 (跳转到 Block) [quick]
├── Task 19: 任务完成样式 (删除线) [quick]
├── Task 20: 侧边栏导航 [visual-engineering]
└── Task 21: 路由配置 [quick]

Wave 4 (After Wave 3 — 最终集成 + 测试):
├── Task 22: 2分钟防抖 AI 触发 [quick]
├── Task 23: 错误处理和边界情况 [unspecified-high]
├── Task 24: E2E 测试 (Playwright) [deep]
└── Task 25: Git 清理和文档 [quick]

Critical Path: T1 → T7 → T8 → T12 → T15 → T24
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

- **1-6**: — — 7-14, 1
- **7**: 1, 3 — 8, 9, 1
- **8**: 7 — 18, 19, 1
- **9**: 7, 10 — 1
- **10**: 2, 4 — 9, 11, 1
- **11**: 4, 10 — 17, 18, 1
- **12**: 2, 6 — 13, 14, 1
- **13**: 12 — 1
- **14**: 12 — 1
- **15**: 1, 3, 5 — 16, 17, 1
- **16**: 15 — 1
- **17**: 4, 11 — 16, 18, 1
- **18**: 8, 11, 17 — 1
- **19**: 8, 17 — 1
- **20**: 1, 3, 15 — 21, 1
- **21**: 7, 15, 20 — 1
- **22**: 7, 9, 12 — 1
- **23**: 12, 17 — 1
- **24**: 21, 22 — 1
- **25**: 24 — 1

### Agent Dispatch Summary

- **Wave 1**: **6** — T1-T2 → `quick`, T3-T6 → `quick`
- **Wave 2**: **8** — T7 → `unspecified-high`, T8 → `deep`, T9-T11 → `quick`, T12-T13 → `deep`, T14 → `unspecified-high`
- **Wave 3**: **7** — T15 → `visual-engineering`, T16 → `quick`, T17 → `quick`, T18-T19 → `quick`, T20 → `visual-engineering`, T21 → `quick`
- **Wave 4**: **4** — T22-T23 → `quick`/`unspecified-high`, T24 → `deep`, T25 → `quick`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [ ] 1. Frontend 项目初始化 (Vue 3 + Vite + Tailwind)

  **What to do**:
  - 创建 Vue 3 + TypeScript + Vite 项目 (`npm create vue@latest`)
  - 安装 Tailwind CSS (`npm install -D tailwindcss postcss autoprefixer`)
  - 安装核心依赖: vue-router, pinia, @tiptap/vue-3, @tiptap/starter-kit
  - 配置 Vitest 测试环境
  - 创建基础目录结构: `src/components/`, `src/views/`, `src/stores/`, `src/services/`

  **Must NOT do**:
  - 不要安装认证相关库
  - 不要配置复杂的构建优化

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 3, 7, 15, 20
  - **Blocked By**: None

  **References**:
  - `STREAM_NOTE_PLANNING.md:267-348` - 前端技术栈和目录结构
  - `STREAM_NOTE_STYLE_GUIDE.md:918-990` - Tailwind 配置示例

  **Acceptance Criteria**:
  - [ ] `stream-note-web/package.json` 存在且包含所有依赖
  - [ ] `npm run dev` 成功启动开发服务器
  - [ ] `tailwind.config.js` 配置正确
  - [ ] `vitest.config.ts` 配置完成

  **QA Scenarios**:
  ```
  Scenario: Frontend dev server starts
    Tool: Bash
    Steps:
      1. cd stream-note-web && npm install && npm run dev &
      2. sleep 5
      3. curl -s http://localhost:5173
    Expected Result: HTTP 200, HTML contains app mount point
    Evidence: .sisyphus/evidence/task-01-dev-server.txt
  ```

  **Commit**: NO (groups with Task 2)

---

- [ ] 2. Backend 项目初始化 (FastAPI + SQLAlchemy)

  **What to do**:
  - 创建 FastAPI 项目结构: `app/api/`, `app/models/`, `app/services/`
  - 创建 `requirements.txt`: fastapi, uvicorn, sqlalchemy, pydantic, httpx, openai, pytest
  - 配置 SQLite 数据库连接
  - 创建基础 API 路由和 health check 端点
  - 配置 pytest 测试环境

  **Must NOT do**:
  - 不要配置 Celery/Redis
  - 不要配置 JWT 认证

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 4, 10, 12
  - **Blocked By**: None

  **References**:
  - `STREAM_NOTE_PLANNING.md:350-435` - 后端技术栈和目录结构

  **Acceptance Criteria**:
  - [ ] `stream-note-api/requirements.txt` 存在
  - [ ] `uvicorn app.main:app` 成功启动
  - [ ] `GET /api/v1/health` 返回 `{"status": "ok"}`
  - [ ] pytest 配置完成

  **QA Scenarios**:
  ```
  Scenario: Backend health check
    Tool: Bash
    Steps:
      1. cd stream-note-api && pip install -r requirements.txt
      2. uvicorn app.main:app &
      3. sleep 3
      4. curl -s http://localhost:8000/api/v1/health
    Expected Result: {"status": "ok"}
    Evidence: .sisyphus/evidence/task-02-health.txt
  ```

  **Commit**: YES
  - Message: `chore: init frontend and backend projects`
  - Files: `stream-note-web/`, `stream-note-api/`

---

- [ ] 3. 设计令牌和基础样式

  **What to do**:
  - 创建 `src/assets/styles/tokens.css` - CSS 变量定义
  - 创建 `src/assets/styles/base.css` - 基础样式和 Tailwind 指令
  - 实现毛玻璃工具类: `.glass-container`, `.glass-elevated`
  - 配置 Tailwind 自定义主题 (颜色、字体、间距)
  - 在 `main.ts` 中引入样式

  **Must NOT do**:
  - 不要创建复杂组件样式
  - 不要使用未定义的颜色值

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 7, 15, 20
  - **Blocked By**: Task 1 (需要前端项目存在)

  **References**:
  - `STREAM_NOTE_STYLE_GUIDE.md:120-161` - CSS 变量定义
  - `STREAM_NOTE_STYLE_GUIDE.md:36-58` - 毛玻璃类实现
  - `STREAM_NOTE_STYLE_GUIDE.md:918-990` - Tailwind 配置

  **Acceptance Criteria**:
  - [ ] `tokens.css` 包含所有设计令牌
  - [ ] 毛玻璃类可用: `.glass-container`, `.glass-elevated`
  - [ ] Tailwind 主题扩展配置完成
  - [ ] 样式在 App.vue 中生效

  **QA Scenarios**:
  ```
  Scenario: CSS tokens loaded correctly
    Tool: Bash
    Steps:
      1. grep -c "var(--bg-base)" stream-note-web/src/assets/styles/tokens.css
    Expected Result: Count >= 1
    Evidence: .sisyphus/evidence/task-03-tokens.txt
  ```

  **Commit**: YES
  - Message: `style: add design tokens and base styles`

---

- [ ] 4. 数据库模型设计

  **What to do**:
  - 创建 `app/models/database.py` - 数据库连接配置
  - 创建 `app/models/document.py` - Document 模型
  - 创建 `app/models/block.py` - Block 模型 (块级别内容)
  - 创建 `app/models/task.py` - TaskCache 模型
  - 创建数据库初始化脚本

  **Must NOT do**:
  - 不要创建 User 模型 (MVP 无认证)
  - 不要创建 Event/Calendar 相关模型

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 10, 11, 17
  - **Blocked By**: Task 2 (需要后端项目存在)

  **References**:
  - Draft 中的新数据模型设计
  - `STREAM_NOTE_PLANNING.md:439-586` - 原数据模型参考

  **Acceptance Criteria**:
  - [ ] Document 模型: id, content(JSON), created_at, updated_at
  - [ ] Block 模型: id, document_id, content, position, is_task, is_completed
  - [ ] TaskCache 模型: id, block_id, text, due_date, status, raw_time_expr
  - [ ] SQLite 数据库文件可创建

  **QA Scenarios**:
  ```
  Scenario: Database models create tables
    Tool: Bash
    Steps:
      1. cd stream-note-api
      2. python -c "from app.models.database import engine; from app.models import document, block, task; print('OK')"
    Expected Result: Output contains "OK"
    Evidence: .sisyphus/evidence/task-04-models.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add database models`

---

- [ ] 5. API 客户端封装

  **What to do**:
  - 创建 `src/services/api.ts` - Axios 或 fetch 封装
  - 创建类型定义: `src/types/document.ts`, `src/types/task.ts`
  - 实现 Document API 调用: `getDocument()`, `updateDocument()`
  - 实现 Task API 调用: `getTasks()`, `updateTaskStatus()`
  - 添加请求拦截器 (未来认证预留)

  **Must NOT do**:
  - 不要在前端存储 API Key
  - 不要实现认证逻辑

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 15
  - **Blocked By**: Task 1

  **References**:
  - `STREAM_NOTE_PLANNING.md:602-780` - API 设计参考

  **Acceptance Criteria**:
  - [ ] `api.ts` 导出所有 API 函数
  - [ ] TypeScript 类型定义完整
  - [ ] 单元测试覆盖 API 调用 (mock)

  **QA Scenarios**:
  ```
  Scenario: API client exports functions
    Tool: Bash
    Steps:
      1. grep -c "export.*getDocument\|export.*getTasks" stream-note-web/src/services/api.ts
    Expected Result: Count >= 2
    Evidence: .sisyphus/evidence/task-05-api-client.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): add API client`

---

- [ ] 6. 环境配置和 .env 模板

  **What to do**:
  - 创建 `stream-note-api/.env.example` - 环境变量模板
  - 创建 `stream-note-api/app/core/config.py` - Pydantic Settings 配置
  - 配置: `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`
  - 创建前端环境变量: `VITE_API_BASE_URL`
  - 更新 README 说明环境配置方法

  **Must NOT do**:
  - 不要提交实际的 `.env` 文件
  - 不要硬编码敏感信息

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 12
  - **Blocked By**: Task 2

  **References**:
  - Draft 中的环境变量配置

  **Acceptance Criteria**:
  - [ ] `.env.example` 包含所有必需变量
  - [ ] `config.py` 正确加载环境变量
  - [ ] README 包含配置说明

  **QA Scenarios**:
  ```
  Scenario: Config loads from env
    Tool: Bash
    Steps:
      1. cd stream-note-api
      2. export OPENAI_API_BASE="http://test"
      3. python -c "from app.core.config import settings; print(settings.OPENAI_API_BASE)"
    Expected Result: "http://test"
    Evidence: .sisyphus/evidence/task-06-config.txt
  ```

  **Commit**: YES
  - Message: `chore: add environment configuration`

---

- [ ] 7. TipTap 编辑器集成

  **What to do**:
  - 创建 `src/components/stream/StreamEditor.vue` - TipTap 编辑器组件
  - 配置 TipTap: StarterKit, Document, Paragraph, Text
  - 实现基础编辑功能: 输入、删除、换行
  - 添加毛玻璃容器样式
  - 集成到 StreamView 页面

  **Must NOT do**:
  - 不要添加复杂格式 (粗体、斜体等) - MVP 暂不需要
  - 不要添加工具栏

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`vue-best-practices`, `frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 2 开始)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 8, 9
  - **Blocked By**: Task 1, 3

  **References**:
  - TipTap 官方文档: https://tiptap.dev/
  - `STREAM_NOTE_STYLE_GUIDE.md` - 编辑器样式参考

  **Acceptance Criteria**:
  - [ ] TipTap 编辑器可正常输入
  - [ ] Enter 键可换行
  - [ ] 编辑器应用毛玻璃样式
  - [ ] 内容可通过 v-model 获取

  **QA Scenarios**:
  ```
  Scenario: TipTap editor renders and accepts input
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:5173
      2. Click on editor area (.ProseMirror)
      3. Type "Hello World"
      4. Assert editor contains "Hello World"
    Expected Result: Text appears in editor
    Evidence: .sisyphus/evidence/task-07-tiptap.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): integrate TipTap editor`

---

- [ ] 8. 块管理逻辑 (Enter 分割 + ID 生成)

  **What to do**:
  - 监听 TipTap 的 Enter 事件
  - 为每个段落生成唯一 Block ID (使用 data-attribute 或 node attribute)
  - 实现 `getBlockId()` 工具函数
  - 创建 `src/composables/useBlocks.ts` - 块管理逻辑
  - 存储块 ID 与内容的映射关系

  **Must NOT do**:
  - 不要在每次 Enter 时重新生成所有 ID (保留已有 ID)
  - 不要使用 DOM id (可能与 Vue 冲突)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 18, 19
  - **Blocked By**: Task 7

  **References**:
  - TipTap Node Attributes: https://tiptap.dev/guide/custom-extensions#attributes

  **Acceptance Criteria**:
  - [ ] 每个段落有唯一的 blockId
  - [ ] Enter 创建新段落时自动生成 ID
  - [ ] 已有段落的 ID 在编辑后保持不变
  - [ ] `useBlocks` composable 可获取所有块

  **QA Scenarios**:
  ```
  Scenario: Block IDs persist after editing
    Tool: Playwright
    Steps:
      1. Type "Block 1" + Enter + "Block 2"
      2. Get all paragraph blockIds
      3. Edit "Block 1" to "Block 1 edited"
      4. Get all paragraph blockIds again
      5. Assert same IDs exist
    Expected Result: Block IDs unchanged
    Evidence: .sisyphus/evidence/task-08-blocks.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add block management logic`

---

- [ ] 9. 自动保存功能

  **What to do**:
  - 创建 `src/composables/useAutoSave.ts` - 自动保存 composable
  - 实现防抖逻辑 (500ms 无输入后保存)
  - 调用 `updateDocument()` API
  - 显示保存状态指示器 (可选)
  - 处理保存失败和重试

  **Must NOT do**:
  - 不要在每次按键都保存
  - 不要阻塞 UI

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 22
  - **Blocked By**: Task 7, 10

  **References**:
  - VueUse `useDebounceFn`: https://vueuse.org/shared/usedebouncefn/

  **Acceptance Criteria**:
  - [ ] 输入后 500ms 自动保存
  - [ ] 保存调用正确的 API
  - [ ] 保存失败时控制台输出错误

  **QA Scenarios**:
  ```
  Scenario: Auto-save triggers after debounce
    Tool: Playwright
    Steps:
      1. Type "Auto save test"
      2. Wait 1 second
      3. Check network requests for PATCH /api/v1/documents
    Expected Result: API call made with updated content
    Evidence: .sisyphus/evidence/task-09-autosave.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add auto-save functionality`

---

- [ ] 10. Document API (CRUD)

  **What to do**:
  - 创建 `app/api/v1/endpoints/documents.py`
  - 实现 `GET /api/v1/documents` - 获取文档 (MVP 单文档，返回默认文档)
  - 实现 `PATCH /api/v1/documents/{id}` - 更新文档内容
  - 实现 `POST /api/v1/documents` - 创建默认文档 (如不存在)
  - 添加 Pydantic Schema: `DocumentResponse`, `DocumentUpdate`

  **Must NOT do**:
  - 不要实现多文档支持
  - 不要添加用户关联

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9, 11
  - **Blocked By**: Task 2, 4

  **References**:
  - `STREAM_NOTE_PLANNING.md:602-730` - API 设计参考

  **Acceptance Criteria**:
  - [ ] `GET /documents` 返回 TipTap JSON 格式
  - [ ] `PATCH /documents/{id}` 更新成功返回 200
  - [ ] pytest 测试覆盖 CRUD

  **QA Scenarios**:
  ```
  Scenario: Document CRUD works
    Tool: Bash
    Steps:
      1. curl -X POST http://localhost:8000/api/v1/documents
      2. curl -s http://localhost:8000/api/v1/documents | jq -r '.id'
      3. curl -X PATCH -H "Content-Type: application/json" -d '{"content":{"type":"doc","content":[]}}' http://localhost:8000/api/v1/documents/{id}
    Expected Result: All return 200/201
    Evidence: .sisyphus/evidence/task-10-document-api.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add Document API`

---

- [ ] 11. Block API (查询 + 状态更新)

  **What to do**:
  - 创建 `app/api/v1/endpoints/blocks.py`
  - 实现 `GET /api/v1/blocks` - 获取所有块
  - 实现 `GET /api/v1/blocks/{block_id}` - 获取单个块
  - 实现 `PATCH /api/v1/blocks/{block_id}` - 更新块状态 (is_completed)
  - 添加 Pydantic Schema: `BlockResponse`, `BlockUpdate`

  **Must NOT do**:
  - 不要允许修改块内容 (内容由文档派生)
  - 不要删除块 API (通过文档更新处理)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 17, 18
  - **Blocked By**: Task 4, 10

  **References**:
  - Draft 中的 Block 模型设计

  **Acceptance Criteria**:
  - [ ] `GET /blocks` 返回块列表
  - [ ] `PATCH /blocks/{id}` 可更新 is_completed
  - [ ] pytest 测试覆盖

  **QA Scenarios**:
  ```
  Scenario: Block status update
    Tool: Bash
    Steps:
      1. curl -X PATCH -H "Content-Type: application/json" -d '{"is_completed":true}' http://localhost:8000/api/v1/blocks/{block_id}
      2. curl -s http://localhost:8000/api/v1/blocks/{block_id} | jq -r '.is_completed'
    Expected Result: true
    Evidence: .sisyphus/evidence/task-11-block-api.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add Block API`

---

- [ ] 12. AI 服务 - OpenAI Compatible 封装

  **What to do**:
  - 创建 `app/services/ai_service.py`
  - 实现 `AIService` 类，使用 `openai` Python SDK
  - 配置自定义 base_url (从环境变量读取)
  - 实现超时和重试机制
  - 添加 stub 模式用于测试 (`AI_MODE=stub`)

  **Must NOT do**:
  - 不要在前端暴露 API Key
  - 不要无限重试 (最多 3 次)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 13, 14, 22
  - **Blocked By**: Task 2, 6

  **References**:
  - OpenAI Python SDK: https://github.com/openai/openai-python
  - Draft 中的环境变量配置

  **Acceptance Criteria**:
  - [ ] 可连接自定义 OpenAI Compatible 端点
  - [ ] 超时设置为 30 秒
  - [ ] stub 模式返回固定响应
  - [ ] pytest 测试覆盖 (mock 和 stub)

  **QA Scenarios**:
  ```
  Scenario: AI service with stub mode
    Tool: Bash
    Steps:
      1. export AI_MODE=stub
      2. cd stream-note-api
      3. python -c "from app.services.ai_service import AIService; s=AIService(); print(s.extract_tasks('todo: test'))"
    Expected Result: Returns stub response
    Evidence: .sisyphus/evidence/task-12-ai-service.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add AI service with OpenAI Compatible support`

---

- [ ] 13. 任务提取 Prompt 设计

  **What to do**:
  - 设计结构化 Prompt 提取任务
  - 使用 JSON Schema 或 Function Calling 确保输出格式
  - 识别模式: `todo:`, `需要...`, `记得...`, `[ ]`
  - 返回格式: `{ "tasks": [{"text": "...", "has_time": bool, "time_expr": "..."}] }`
  - 添加单元测试验证 Prompt 有效性

  **Must NOT do**:
  - 不要依赖特定模型特性 (保持兼容性)
  - 不要让 Prompt 过长

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: Task 12

  **References**:
  - OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling

  **Acceptance Criteria**:
  - [ ] Prompt 可从文本中提取任务
  - [ ] 输出为有效 JSON
  - [ ] 识别常见任务模式

  **QA Scenarios**:
  ```
  Scenario: Task extraction works
    Tool: Bash
    Steps:
      1. cd stream-note-api
      2. export AI_MODE=stub
      3. python -c "from app.services.ai_service import AIService; result=AIService().extract_tasks('todo: 完成报告'); print(result)"
    Expected Result: JSON with tasks array
    Evidence: .sisyphus/evidence/task-13-prompt.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add task extraction prompt`

---

- [ ] 14. 时间解析逻辑

  **What to do**:
  - 创建 `app/services/time_parser.py`
  - 实现相对时间解析: 今天、明天、下周一、下周三
  - 实现绝对时间解析: 1月15日、2024-01-15
  - 实现时间点解析: 3点、下午2点、晚上8点
  - 结合 AI 和规则解析 (AI 提取 + 规则规范化)

  **Must NOT do**:
  - 不要使用复杂 NLP 库 (保持轻量)
  - 不要处理过于模糊的时间 (如"找个时间")

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: Task 12

  **References**:
  - `STREAM_NOTE_PLANNING.md:869-964` - 时间解析参考

  **Acceptance Criteria**:
  - [ ] 可解析 "明天" → 具体日期
  - [ ] 可解析 "下周一 3点" → 具体日期时间
  - [ ] 时区使用本地时区
  - [ ] pytest 测试覆盖

  **QA Scenarios**:
  ```
  Scenario: Time parsing works
    Tool: Bash
    Steps:
      1. cd stream-note-api
      2. python -c "from app.services.time_parser import TimeParser; p=TimeParser(); print(p.parse('明天 3点'))"
    Expected Result: Returns datetime object
    Evidence: .sisyphus/evidence/task-14-time-parser.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add time parsing logic`

---

- [ ] 15. Tasks 视图 UI

  **What to do**:
  - 创建 `src/views/TasksView.vue`
  - 创建 `src/stores/tasks.ts` - Pinia store
  - 实现任务列表布局 (参考 STYLE_GUIDE)
  - 显示任务数量统计
  - 添加空状态提示

  **Must NOT do**:
  - 不要添加复杂的筛选功能
  - 不要添加任务创建 UI (任务来自 AI 识别)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`vue-best-practices`, `frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 3)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 16, 17
  - **Blocked By**: Task 1, 3, 5

  **References**:
  - `STREAM_NOTE_STYLE_GUIDE.md:679-769` - TaskItem 样式

  **Acceptance Criteria**:
  - [ ] TasksView 显示任务列表
  - [ ] 毛玻璃样式正确应用
  - [ ] 响应式布局

  **QA Scenarios**:
  ```
  Scenario: Tasks view renders
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:5173/tasks
      2. Assert page title or heading exists
    Expected Result: Tasks view visible
    Evidence: .sisyphus/evidence/task-15-tasks-view.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Tasks view UI`

---

- [ ] 16. TaskItem 组件

  **What to do**:
  - 创建 `src/components/tasks/TaskItem.vue`
  - 实现复选框和任务文本
  - 显示截止时间 (如果有)
  - 实现状态切换交互
  - 添加溯源箭头图标

  **Must NOT do**:
  - 不要添加复杂动画
  - 不要添加右键菜单

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 15

  **References**:
  - `STREAM_NOTE_STYLE_GUIDE.md:679-769` - TaskItem 样式参考

  **Acceptance Criteria**:
  - [ ] 复选框可点击切换状态
  - [ ] 截止时间显示正确
  - [ ] 溯源箭头可点击

  **QA Scenarios**:
  ```
  Scenario: TaskItem toggle works
    Tool: Playwright
    Steps:
      1. Navigate to /tasks
      2. Click first task checkbox
      3. Assert task status changed
    Expected Result: Task shows as completed
    Evidence: .sisyphus/evidence/task-16-taskitem.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add TaskItem component`

---

- [ ] 17. Task API (列表 + 状态更新)

  **What to do**:
  - 创建 `app/api/v1/endpoints/tasks.py`
  - 实现 `GET /api/v1/tasks` - 获取任务列表 (支持 status 筛选)
  - 实现 `PATCH /api/v1/tasks/{task_id}` - 更新任务状态
  - 更新状态时同步更新 Block.is_completed
  - 添加 Pydantic Schema

  **Must NOT do**:
  - 不要允许修改任务内容
  - 不要添加任务删除 API

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 16, 18
  - **Blocked By**: Task 4, 11

  **References**:
  - `STREAM_NOTE_PLANNING.md:732-778` - Task API 参考

  **Acceptance Criteria**:
  - [ ] `GET /tasks?status=pending` 返回待办任务
  - [ ] `PATCH /tasks/{id}` 更新状态并同步 Block
  - [ ] pytest 测试覆盖

  **QA Scenarios**:
  ```
  Scenario: Task status update syncs to block
    Tool: Bash
    Steps:
      1. curl -X PATCH -H "Content-Type: application/json" -d '{"status":"completed"}' http://localhost:8000/api/v1/tasks/{task_id}
      2. curl -s http://localhost:8000/api/v1/blocks/{block_id} | jq -r '.is_completed'
    Expected Result: true
    Evidence: .sisyphus/evidence/task-17-task-api.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add Task API`

---

- [ ] 18. 溯源跳转功能

  **What to do**:
  - 实现点击 TaskItem 箭头跳转到 Stream
  - 跳转时携带 blockId 参数
  - StreamView 接收参数后滚动到对应块
  - 高亮目标块 (短暂动画)

  **Must NOT do**:
  - 不要使用复杂的滚动动画
  - 不要改变 URL hash (保持干净)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 8, 11, 17

  **References**:
  - Vue Router: https://router.vuejs.org/

  **Acceptance Criteria**:
  - [ ] 点击任务箭头跳转到 /stream?blockId=xxx
  - [ ] Stream 自动滚动到目标块
  - [ ] 目标块短暂高亮

  **QA Scenarios**:
  ```
  Scenario: Backlink navigates to correct block
    Tool: Playwright
    Steps:
      1. Navigate to /tasks
      2. Click backlink arrow on first task
      3. Assert URL contains /stream
      4. Assert target block is visible in viewport
    Expected Result: Navigated and scrolled to block
    Evidence: .sisyphus/evidence/task-18-backlink.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add backlink navigation`

---

- [ ] 19. 任务完成样式

  **What to do**:
  - 在 StreamView 中，已完成任务的块显示删除线
  - 实现块级别的样式绑定
  - 添加过渡动画 (可选)

  **Must NOT do**:
  - 不要修改块的实际文本内容
  - 不要使用过于显眼的样式

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: Task 8, 17

  **References**:
  - `STREAM_NOTE_STYLE_GUIDE.md:523-531` - 完成状态样式

  **Acceptance Criteria**:
  - [ ] 已完成块显示删除线
  - [ ] 文字颜色变淡
  - [ ] 样式通过 CSS 类控制

  **QA Scenarios**:
  ```
  Scenario: Completed task shows strikethrough
    Tool: Playwright
    Steps:
      1. Complete a task via /tasks
      2. Navigate to /stream
      3. Assert corresponding block has line-through style
    Expected Result: Block shows strikethrough
    Evidence: .sisyphus/evidence/task-19-strikethrough.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add completed task styling`

---

- [ ] 20. 侧边栏导航

  **What to do**:
  - 创建 `src/components/layout/Sidebar.vue`
  - 实现 Stream 和 Tasks 导航项
  - 实现折叠/展开动画
  - 显示 Tasks 角标 (未完成数量)
  - 应用毛玻璃样式

  **Must NOT do**:
  - 不要添加其他视图入口 (Calendar/Ideas/Code)
  - 不要添加用户头像

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`vue-best-practices`, `frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 21
  - **Blocked By**: Task 1, 3, 15

  **References**:
  - `STREAM_NOTE_STYLE_GUIDE.md:372-493` - Sidebar 样式

  **Acceptance Criteria**:
  - [ ] 侧边栏显示 Stream 和 Tasks
  - [ ] 悬停时展开显示文字
  - [ ] Tasks 显示角标数字

  **QA Scenarios**:
  ```
  Scenario: Sidebar navigation works
    Tool: Playwright
    Steps:
      1. Click on Tasks in sidebar
      2. Assert URL is /tasks
      3. Click on Stream in sidebar
      4. Assert URL is /stream or /
    Expected Result: Navigation works
    Evidence: .sisyphus/evidence/task-20-sidebar.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add sidebar navigation`

---

- [ ] 21. 路由配置

  **What to do**:
  - 配置 Vue Router: `/`, `/stream`, `/tasks`
  - `/` 重定向到 `/stream`
  - 创建基础布局组件 `AppLayout.vue`
  - 集成 Sidebar 和 router-view

  **Must NOT do**:
  - 不要添加路由守卫 (无认证)
  - 不要添加懒加载 (MVP 不需要)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 24
  - **Blocked By**: Task 7, 15, 20

  **References**:
  - Vue Router: https://router.vuejs.org/

  **Acceptance Criteria**:
  - [ ] `/` 重定向到 `/stream`
  - [ ] `/tasks` 显示 TasksView
  - [ ] Sidebar 高亮当前路由

  **QA Scenarios**:
  ```
  Scenario: Routes work correctly
    Tool: Bash
    Steps:
      1. curl -s http://localhost:5173/ | head -20
      2. curl -s http://localhost:5173/tasks | head -20
    Expected Result: Both return HTML
    Evidence: .sisyphus/evidence/task-21-routes.txt
  ```

  **Commit**: YES
  - Message: `feat(frontend): configure routes`

---

- [ ] 22. 2分钟防抖 AI 触发

  **What to do**:
  - 在 `useAutoSave` 中添加 AI 触发逻辑
  - 实现 2 分钟防抖 (用户停止输入 2 分钟后触发)
  - 调用后端 AI 识别 API
  - 更新 TaskCache

  **Must NOT do**:
  - 不要在每次输入都触发 AI
  - 不要阻塞用户输入

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`vue-best-practices`]

  **Parallelization**:
  - **Can Run In Parallel**: NO (Wave 4)
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 24
  - **Blocked By**: Task 7, 9, 12

  **References**:
  - VueUse `useDebounceFn`

  **Acceptance Criteria**:
  - [ ] 2 分钟无输入后触发 AI
  - [ ] AI 识别结果存入 TaskCache
  - [ ] Tasks 角标更新

  **QA Scenarios**:
  ```
  Scenario: AI triggers after 2 min idle
    Tool: Playwright
    Steps:
      1. Type "todo: test task" in editor
      2. Wait 130 seconds (or mock timer)
      3. Navigate to /tasks
      4. Assert new task appears
    Expected Result: Task extracted and shown
    Evidence: .sisyphus/evidence/task-22-ai-trigger.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add AI trigger with 2min debounce`

---

- [ ] 23. 错误处理和边界情况

  **What to do**:
  - AI 服务超时处理 (显示友好提示)
  - API 错误统一处理
  - 网络断开重连逻辑
  - TaskCache 重复任务去重

  **Must NOT do**:
  - 不要显示原始错误信息
  - 不要无限重试

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 24
  - **Blocked By**: Task 12, 17

  **References**:
  - Metis Review 中的 Edge Cases

  **Acceptance Criteria**:
  - [ ] AI 超时显示 toast 提示
  - [ ] 网络错误可恢复
  - [ ] 重复任务不会重复创建

  **QA Scenarios**:
  ```
  Scenario: AI timeout shows friendly message
    Tool: Playwright
    Steps:
      1. Set AI service to timeout mode
      2. Trigger AI by waiting 2 min
      3. Assert error toast appears
    Expected Result: Friendly error message shown
    Evidence: .sisyphus/evidence/task-23-error.png
  ```

  **Commit**: YES
  - Message: `feat: add error handling and edge cases`

---

- [ ] 24. E2E 测试

  **What to do**:
  - 配置 Playwright
  - 编写核心流程 E2E 测试:
    1. 打开应用 → 输入内容 → 自动保存
    2. AI 识别 → 任务出现在 Tasks 视图
    3. 完成任务 → Stream 显示删除线
  - 运行测试并保存截图

  **Must NOT do**:
  - 不要测试非核心功能
  - 不要依赖外部 AI 服务 (使用 stub)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 25
  - **Blocked By**: Task 21, 22

  **References**:
  - Playwright: https://playwright.dev/

  **Acceptance Criteria**:
  - [ ] `npx playwright test` 通过
  - [ ] 核心流程测试覆盖
  - [ ] 截图保存到 evidence/

  **QA Scenarios**:
  ```
  Scenario: E2E tests pass
    Tool: Bash
    Steps:
      1. cd stream-note-web
      2. npx playwright test
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-24-e2e/
  ```

  **Commit**: YES
  - Message: `test: add E2E tests with Playwright`

---

- [ ] 25. Git 清理和文档

  **What to do**:
  - 更新 README.md (项目结构、启动方法)
  - 添加 .gitignore 条目
  - 清理调试代码和 console.log
  - 创建最终的 commit

  **Must NOT do**:
  - 不要提交 .env 文件
  - 不要提交 node_modules/

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`writing`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (Final)
  - **Blocks**: None
  - **Blocked By**: Task 24

  **References**:
  - None

  **Acceptance Criteria**:
  - [ ] README 包含完整启动说明
  - [ ] .gitignore 正确配置
  - [ ] 无调试代码残留

  **QA Scenarios**:
  ```
  Scenario: README is complete
    Tool: Bash
    Steps:
      1. grep -c "npm run dev" README.md
      2. grep -c "uvicorn" README.md
    Expected Result: Both counts >= 1
    Evidence: .sisyphus/evidence/task-25-readme.txt
  ```

  **Commit**: YES
  - Message: `release: MVP v0.1.0`

---

## Final Verification Wave (MANDATORY)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify all "Must Have" features are implemented. Check evidence files exist.

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `pytest` + `vitest`. Review for code quality.

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Execute all QA scenarios, capture evidence.

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify no scope creep, no unaccounted changes.

---

## Commit Strategy

- **Frontend Tasks**: `feat(frontend): description` — after each major feature
- **Backend Tasks**: `feat(backend): description` — after each major feature
- **Integration**: `feat: integrate X` — when connecting components
- **Final**: `release: MVP v0.1.0` — after all verification passes

---

## Success Criteria

### Verification Commands
```bash
# Backend health check
curl -s http://localhost:8000/api/v1/health | jq -r .status
# Expected: "ok"

# Frontend build
cd stream-note-web && npm run build
# Expected: Build success, no errors

# Backend tests
cd stream-note-api && pytest
# Expected: All tests pass

# Frontend tests
cd stream-note-web && npm test
# Expected: All tests pass
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Evidence files captured
