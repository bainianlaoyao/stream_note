# Stream Note 后端代码知识文档

## 1. 技术栈与启动

- 框架：FastAPI
- ORM：SQLAlchemy 2.x（声明式模型，`Mapped[T]` + `mapped_column`）
- 数据库：SQLite（默认 `stream_note.db`）
- AI：`openai` SDK（直接调用 LLM）

常用命令（`stream-note-api/`）：

```bash
uv sync --python .venv/Scripts/python.exe
uv run --python .venv/Scripts/python.exe python scripts/migrate_db.py
uv run --python .venv/Scripts/python.exe python -m uvicorn app.main:app --reload
```

## 2. 目录与职责

- `app/main.py`：FastAPI 应用入口、CORS、路由挂载、启动数据库版本校验
- `alembic/` + `alembic.ini`：数据库版本迁移脚本
- `app/api/v1/router.py`：聚合 v1 路由
- `app/api/v1/endpoints/documents.py`：文档查询 + 单文档 upsert
- `app/api/v1/endpoints/blocks.py`：块查询与完成状态更新
- `app/api/v1/endpoints/tasks.py`：任务查询、汇总统计、命令式状态切换
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

### 3.2 启动数据库版本校验

在 `startup` 事件中执行：

```python
ensure_database_ready(engine)
```

如果数据库未迁移到 Alembic head，会拒绝启动并提示先执行迁移脚本。
迁移入口改为：

```bash
uv run --python .venv/Scripts/python.exe python scripts/migrate_db.py
```

### 3.3 环境变量加载

- `app/core/env.py` 会在运行时读取 `stream-note-api/.env`
- 仅在进程环境缺失时注入（不覆盖已有环境变量）
- `database.py` 与 `ai_service.py` 已接入该加载逻辑
### 3.4 数据库会话

`app/models/database.py`：

- `engine` 根据 `DATABASE_URL` 创建（SQLite 自动加 `check_same_thread=False`）
- SQLite 连接会配置超时与并发参数（`SQLITE_TIMEOUT_SECONDS`、`busy_timeout`、`WAL`）
- `SessionLocal` 作为会话工厂
- `get_db()` 通过 `yield` 提供请求级 Session，并在 finally 关闭
- 运行时不再自动建表；schema 变更通过 Alembic 管理

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

- `PUT /documents/current`
- 单文档 upsert：存在则更新 `content`，不存在则创建并返回 201

- `POST /documents`
- 兼容保留接口：若已存在文档则返回现有文档；否则创建并返回 201

- `PATCH /documents/{document_id}`
- 兼容保留接口：按 id 更新文档 `content`

当前设计是“单文档模式”，即业务上只维护一条主文档。

### 5.2 blocks

- `GET /blocks`：按 `position` 升序返回所有块
- `GET /blocks/{block_id}`：返回单块
- `PATCH /blocks/{block_id}`：更新 `is_completed`

### 5.3 tasks

- `GET /tasks?status=...`：可选状态过滤，按 `created_at desc` 返回
- `GET /tasks/summary`：返回 `pending_count`、`completed_count`、`total_count`
- `POST /tasks/{task_id}/commands/toggle`：
  - 命令式状态切换（`pending <-> completed`）
  - 在同一事务内同步 `Block.is_completed`
  - 返回更新后的 task 与最新 summary
- `PATCH /tasks/{task_id}`：
  - 兼容保留接口，可直接设置 `status`
  - 后端会校验状态并同步 `Block.is_completed`

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
  - `OPENAI_MAX_ATTEMPTS`（可选，默认 2 次）
  - `OPENAI_DISABLE_THINKING`（可选，默认 `1`，请求时附带 `enable_thinking=false`）
- `extract_tasks(text)`：
  - 直接请求 LLM，要求输出 JSON 数组
  - 对 markdown code fence / 非纯 JSON 返回做容错解析
  - 请求失败会做短重试（超时/连接失败/5xx/429）
  - 持续失败时抛出错误，由 API 层返回 502

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
- `SQLITE_TIMEOUT_SECONDS=30`
- `OPENAI_API_BASE=http://localhost:11434/v1`
- `OPENAI_API_KEY=dummy-key`
- `OPENAI_MODEL=llama3.2`
- `OPENAI_TIMEOUT_SECONDS=20`
- `OPENAI_MAX_ATTEMPTS=2`
- `OPENAI_DISABLE_THINKING=1`

数据库运维脚本：

- `scripts/migrate_db.py`：迁移前自动备份（SQLite）+ 旧 schema 安全引导 + `alembic upgrade head`
- `scripts/backup_db.py`：手动备份数据库
- `scripts/restore_db.py`：从备份恢复数据库（默认会先做一次恢复前快照）

## 8. 当前实现注意事项

- 任务状态切换已经采用后端命令式接口（`/tasks/{id}/commands/toggle`），由后端统一维护 `TaskCache` 与 `Block` 一致性
- 任务汇总统计由后端统一提供（`GET /tasks/summary`），前端不再自行计算待办数
- 文档保存推荐使用 `PUT /documents/current`，前端不再决定“先创建还是更新”
- 已引入 Alembic 版本化迁移与迁移脚本；仍建议为每次 schema 变更新增 migration + 升级回归测试

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
- `stream-note-api/app/models/schema_version.py`
- `stream-note-api/alembic/env.py`
- `stream-note-api/alembic/versions/20260221_000001_baseline.py`
- `stream-note-api/app/services/ai_service.py`
- `stream-note-api/app/services/time_parser.py`
