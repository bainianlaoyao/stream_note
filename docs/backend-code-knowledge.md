# Stream Note 后端代码知识文档

## 1. 技术栈与启动

- 框架：FastAPI
- ORM：SQLAlchemy 2.x（声明式模型，`Mapped[T]` + `mapped_column`）
- 数据库：SQLite（默认 `stream_note.db`）
- AI：`openai` SDK（直接调用 LLM）

常用命令（`stream-note-api/`）：

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## 2. 目录与职责

- `app/main.py`：FastAPI 应用入口、CORS、路由挂载、启动建表
- `app/api/v1/router.py`：聚合 v1 路由
- `app/api/v1/endpoints/documents.py`：文档 CRUD（当前是单文档模式）
- `app/api/v1/endpoints/blocks.py`：块查询与完成状态更新
- `app/api/v1/endpoints/tasks.py`：任务查询与状态更新
- `app/api/v1/endpoints/ai.py`：任务提取/批量分析
- `app/models/*.py`：数据库模型与会话
- `app/services/ai_service.py`：AI 提取服务（LLM）
- `app/services/time_parser.py`：中文时间表达式解析

## 3. 应用启动与基础设施

### 3.1 应用入口

`app/main.py` 做了三件事：

1. 初始化 `FastAPI(title="Stream Note API", version="0.1.0")`
2. 开启宽松 CORS（`allow_origins=["*"]`）
3. 挂载路由前缀 `"/api/v1"`，并提供 `GET /api/v1/health`

### 3.2 启动建表

在 `startup` 事件中执行：

```python
Base.metadata.create_all(bind=engine)
```

意味着没有迁移系统（如 Alembic），结构变更依赖手工处理。

### 3.3 数据库会话

`app/models/database.py`：

- `engine` 根据 `DATABASE_URL` 创建（SQLite 自动加 `check_same_thread=False`）
- `SessionLocal` 作为会话工厂
- `get_db()` 通过 `yield` 提供请求级 Session，并在 finally 关闭

## 4. 数据模型

## 4.1 Document（`documents`）

- 字段：`id`, `content(JSON)`, `created_at`, `updated_at`
- `content` 默认值是 TipTap 文档空结构：`{"type": "doc", "content": []}`

## 4.2 Block（`blocks`）

- 字段：`id`, `document_id`, `content`, `position`
- 任务相关标志：`is_task`, `is_completed`, `is_analyzed`
- `document_id` 外键指向 `documents.id`

## 4.3 TaskCache（`task_cache`）

- 字段：`id`, `block_id`, `text`, `status`, `due_date`, `raw_time_expr`, `created_at`, `updated_at`
- `block_id` 外键指向 `blocks.id`
- 当前任务列表页面直接读取该缓存表

## 5. API 说明（按模块）

所有接口前缀均为 `/api/v1`。

### 5.1 documents

- `GET /documents`
- 返回第一条文档；不存在返回 404

- `POST /documents`
- 若已存在文档则直接返回现有文档；否则创建并返回 201

- `PATCH /documents/{document_id}`
- 更新文档 `content`

当前设计是“单文档模式”，即业务上只维护一条主文档。

### 5.2 blocks

- `GET /blocks`：按 `position` 升序返回所有块
- `GET /blocks/{block_id}`：返回单块
- `PATCH /blocks/{block_id}`：更新 `is_completed`

### 5.3 tasks

- `GET /tasks?status=...`：可选状态过滤，按 `created_at desc` 返回
- `PATCH /tasks/{task_id}`：更新 `status`

### 5.4 ai

- `POST /ai/extract`
- 输入：当前编辑器 TipTap JSON
- 行为：提取段落文本 -> 调 AI 识别任务 -> 解析时间 -> 写入 `TaskCache`

- `POST /ai/analyze-pending`
- 行为：从数据库读取文档 -> 提取文本块 -> 分析前 10 条
- 对每个块：
  - 若已有 `Block` 且 `is_analyzed=True` 则跳过
  - 否则新建/复用 `Block`，AI 提取任务后写入 `TaskCache`
  - 更新 `Block.is_task` 与 `Block.is_analyzed`

- `POST /ai/reset-debug-state`
- 行为：删除全部 `TaskCache` 记录，并将全部 `Block` 统一重置为：
  - `is_analyzed=False`
  - `is_task=False`
  - `is_completed=False`
- 返回：`deleted_tasks` 与 `reset_blocks` 计数，便于 AI 调试快速回到初始状态

## 6. AI 与时间解析链路

### 6.1 `AIService`

- 配置来自环境变量：
  - `OPENAI_API_BASE`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_TIMEOUT_SECONDS`（可选，默认 20 秒）
- `extract_tasks(text)`：
  - 请求 LLM，要求输出 JSON 数组
  - 对 markdown code fence / 非纯 JSON 返回做容错解析
  - 请求或解析失败时返回空数组

### 6.2 `TimeParser`

- 支持表达式：
  - 相对日期：`今天`、`明天`、`后天`
  - 周表达：`下周一` 到 `下周日`
  - 月日：`3月8日`
  - 时间：`10点`、`10点30分`，含 `下午/晚上` 加 12 小时逻辑
- `parse(text)` 先定日期再定时间，最终返回 `datetime`

## 7. 环境变量

`stream-note-api/.env.example`：

- `DATABASE_URL=sqlite:///./stream_note.db`
- `OPENAI_API_BASE=http://localhost:11434/v1`
- `OPENAI_API_KEY=dummy-key`
- `OPENAI_MODEL=llama3.2`
- `OPENAI_TIMEOUT_SECONDS=20`

## 8. 当前实现注意事项

- `documents.py` / `ai.py` 中大量手工 `JSONResponse` + `try/except`，返回结构由代码拼装，尚未统一 Pydantic 响应模型
- 仍存在动态属性赋值：
  - `app/api/v1/endpoints/blocks.py` 使用 `setattr(block, "is_completed", ...)`
  - `app/api/v1/endpoints/tasks.py` 使用 `setattr(task, "status", ...)`
- `ai/extract` 路径里 `block_id` 使用临时 UUID，未落表 `Block`，与 `TaskCache.block_id` 外键语义存在偏差风险（而 `analyze-pending` 会创建/复用 `Block`）
- 缺少自动化测试目录与迁移管理，数据库 schema 演进和回归验证成本较高

## 9. 关键文件索引

- `stream-note-api/app/main.py`
- `stream-note-api/app/api/v1/router.py`
- `stream-note-api/app/api/v1/endpoints/documents.py`
- `stream-note-api/app/api/v1/endpoints/blocks.py`
- `stream-note-api/app/api/v1/endpoints/tasks.py`
- `stream-note-api/app/api/v1/endpoints/ai.py`
- `stream-note-api/app/models/database.py`
- `stream-note-api/app/models/document.py`
- `stream-note-api/app/models/block.py`
- `stream-note-api/app/models/task.py`
- `stream-note-api/app/services/ai_service.py`
- `stream-note-api/app/services/time_parser.py`
