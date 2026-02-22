# Stream Note 后端代码知识文档（更新版）

## 1. 技术栈与启动

- 框架：FastAPI
- ORM：SQLAlchemy 2.x（声明式模型，`Mapped[T]` + `mapped_column`）
- 数据库：SQLite（默认 `stream_note.db`）
- AI：`openai` SDK（直接调用 LLM）
- 认证：JWT（`python-jose`）

常用命令（`stream-note-api/`）：

```bash
uv sync --python .venv/Scripts/python.exe
uv run --python .venv/Scripts/python.exe python scripts/migrate_db.py
uv run --python .venv/Scripts/python.exe python -m uvicorn app.main:app --reload
```

## 2. 目录与职责

```
stream-note-api/app/
├── main.py                    # FastAPI 应用入口、CORS、路由挂载
├── core/
│   ├── env.py                 # 环境变量加载
│   └── security.py            # JWT 认证工具
├── api/v1/
│   ├── router.py              # 路由聚合
│   ├── deps.py                # 依赖注入（get_current_user）
│   └── endpoints/
│       ├── auth.py            # 认证端点（登录/注册/获取当前用户）
│       ├── documents.py       # 文档 CRUD + 恢复系统
│       ├── blocks.py          # 块查询与完成状态更新
│       ├── tasks.py           # 任务查询、汇总、切换、删除
│       └── ai.py              # AI 提取/批量分析/Provider 配置
├── models/
│   ├── database.py            # 数据库连接
│   ├── user.py                # 用户模型
│   ├── document.py            # 文档模型
│   ├── document_revision.py   # 文档版本模型（恢复系统）
│   ├── block.py               # 块模型
│   ├── task.py                # 任务缓存模型
│   ├── ai_provider_setting.py # AI Provider 配置模型
│   ├── silent_analysis_job.py # 静默分析任务模型
│   └── schema_version.py      # Schema 版本模型
├── services/
│   ├── ai_service.py          # AI 提取服务
│   ├── time_parser.py         # 中文时间表达式解析
│   └── silent_analysis.py     # 静默分析 Worker
└── alembic/                   # 数据库迁移
```

## 3. 应用启动与基础设施

### 3.1 应用入口

`app/main.py` 做了以下事情：

1. 初始化 `FastAPI(title="Stream Note API", version="0.1.0")`
2. 开启宽松 CORS（`allow_origins=["*"]`）
3. 挂载路由前缀 `"/api/v1"`
4. 启动时校验数据库版本（`ensure_database_ready`）
5. **启动静默分析 Worker**（`silent_analysis_worker.start()`）

### 3.2 环境变量

`app/core/env.py` 会在运行时读取 `stream-note-api/.env`，仅在进程环境缺失时注入。

**主要环境变量**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./stream_note.db` | 数据库连接 |
| `SQLITE_TIMEOUT_SECONDS` | `30` | SQLite 锁等待超时 |
| `OPENAI_PROVIDER` | `openai_compatible` | AI Provider 类型 |
| `OPENAI_API_BASE` | `http://localhost:11434/v1` | API 端点 |
| `OPENAI_API_KEY` | - | API Key |
| `OPENAI_MODEL` | `llama3.2` | 模型名称 |
| `OPENAI_TIMEOUT_SECONDS` | `20` | 请求超时 |
| `OPENAI_MAX_ATTEMPTS` | `2` | 重试次数 |
| `OPENAI_DISABLE_THINKING` | `1` | 禁用推理模式 |

**静默分析配置**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SILENT_ANALYSIS_ENABLED` | `1` | 是否启用 |
| `SILENT_ANALYSIS_IDLE_SECONDS` | `6.0` | 空闲时间 |
| `SILENT_ANALYSIS_POLL_SECONDS` | `0.8` | 轮询间隔 |
| `SILENT_ANALYSIS_BATCH_SIZE` | `20` | 批量大小 |
| `SILENT_ANALYSIS_MAX_RETRY` | `3` | 最大重试 |
| `SILENT_ANALYSIS_RETRY_BASE_SECONDS` | `4.0` | 重试基础间隔 |

## 4. 数据模型

### 4.1 User（用户）

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

### 4.2 Document（文档）

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default={"type": "doc", "content": []})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

### 4.3 DocumentRevision（文档版本）

```python
class DocumentRevision(Base):
    __tablename__ = "document_revisions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), index=True)
    revision_no: Mapped[int] = mapped_column(Integer)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    char_count: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(32))  # auto_save, pre_destructive, restore, pre_restore
    restored_from_revision_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("document_revisions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

### 4.4 Block（块）

```python
class Block(Base):
    __tablename__ = "blocks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))
    content: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    is_task: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 4.5 TaskCache（任务缓存）

```python
class TaskCache(Base):
    __tablename__ = "task_cache"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    block_id: Mapped[str] = mapped_column(String, ForeignKey("blocks.id"))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, completed
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    raw_time_expr: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)  # 用户手动隐藏
```

### 4.6 AIProviderSetting（AI Provider 配置）

```python
class AIProviderSetting(Base):
    __tablename__ = "ai_provider_settings"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String)
    api_base: Mapped[str] = mapped_column(String)
    api_key: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    timeout_seconds: Mapped[float] = mapped_column(Float)
    max_attempts: Mapped[int] = mapped_column(Integer)
    disable_thinking: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

### 4.7 SilentAnalysisJob（静默分析任务）

```python
class SilentAnalysisJob(Base):
    __tablename__ = "silent_analysis_jobs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String)  # pending, running, done, failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

## 5. API 说明

### 5.1 认证端点（`/auth`）

```python
# 注册
POST /auth/register
Body: { "username": "alice", "password": "secret123" }
Response: { "access_token": "...", "token_type": "bearer", "user": {...} }

# 登录
POST /auth/login
Body: { "username": "alice", "password": "secret123" }
Response: { "access_token": "...", "token_type": "bearer", "user": {...} }

# 获取当前用户
GET /auth/me
Headers: Authorization: Bearer <token>
Response: { "id": "...", "username": "alice", "created_at": "..." }
```

### 5.2 文档端点（`/documents`）

```python
# 获取文档
GET /documents
Response: Document | 404

# 创建文档（兼容保留）
POST /documents
Response: Document

# 更新/创建文档（推荐）
PUT /documents/current
Body: { "content": {...} }
Response: Document
# 副作用：触发静默分析 + 自动快照

# 获取恢复候选
GET /documents/recovery/candidates
Response: { "candidates": [...] }

# 恢复指定版本
POST /documents/recovery/{revision_id}/restore
Response: { "document": {...}, "restored_revision_id": "...", "undo_revision_id": "..." }
```

### 5.3 任务端点（`/tasks`）

```python
# 获取任务列表
GET /tasks?status=...&include_hidden=...
Response: Task[]

# 获取任务汇总
GET /tasks/summary?include_hidden=...
Response: { "pending_count": 5, "completed_count": 3, "total_count": 8 }

# 切换任务状态（推荐）
POST /tasks/{task_id}/commands/toggle
Response: { "task": {...}, "summary": {...} }

# 删除任务
DELETE /tasks/{task_id}?include_hidden=...
Response: { "deleted_task_id": "...", "summary": {...} }

# 更新任务状态（兼容保留）
PATCH /tasks/{task_id}
Body: { "status": "completed" }
Response: Task
```

**任务可见性规则**：
- 已完成任务 24 小时后自动隐藏
- `include_hidden=true` 显示所有任务
- 默认只显示未完成 + 24 小时内完成的任务

### 5.4 AI 端点（`/ai`）

```python
# 从内容提取任务
POST /ai/extract
Body: { "content": {...} }
Response: { "tasks_found": 3, "tasks": [...] }

# 分析待处理块
POST /ai/analyze-pending?force=false
Response: { "analyzed_count": 5, "tasks_found": 2, "tasks": [...] }

# 重置 AI 状态（调试用）
POST /ai/reset-debug-state
Response: { "deleted_tasks": 10, "reset_blocks": 15 }

# 获取 AI Provider 设置
GET /ai/provider-settings
Response: AIProviderSettings

# 更新 AI Provider 设置
PUT /ai/provider-settings
Body: { "provider": "openai", "api_base": "...", ... }
Response: AIProviderSettings

# 测试 AI Provider 连接
POST /ai/provider-settings/test
Body: { "provider": "openai", ... }
Response: { "ok": true, "latency_ms": 123, "message": "..." }
```

## 6. 静默分析服务

### 6.1 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    SilentAnalysisWorker                      │
│                      （后台线程）                              │
│                                                              │
│  while not stopped:                                          │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ process_one_silent_analysis_job()                   │  │
│    │   ├── 查询待处理任务（status=pending/failed）         │  │
│    │   ├── 领取任务（status=running）                      │  │
│    │   ├── 批量分析未处理的块（batch_size=20）             │  │
│    │   ├── 更新任务状态（done/failed）                     │  │
│    │   └── 如果有更多未处理块，创建新任务                   │  │
│    └─────────────────────────────────────────────────────┘  │
│                                                              │
│    sleep(poll_seconds)  # 默认 0.8 秒                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 触发机制

```python
# 文档保存时自动触发
def upsert_current_document(...):
    # ... 保存文档 ...
    enqueue_silent_analysis(
        document_id=str(doc.id),
        user_id=user_id,
        content=doc.content,
    )
```

### 6.3 分析流程

```python
def _analyze_document_once(db, document, user_id, batch_size):
    # 1. 提取文本块
    text_blocks = _extract_text_from_tiptap(doc_content)
    
    # 2. 删除过期的块
    stale_blocks = query(Block).filter(position >= len(text_blocks))
    
    # 3. 分析未处理的块
    for position, text in enumerate(text_blocks[:batch_size]):
        db_block = get_or_create_block(...)
        if db_block.is_analyzed:
            continue
        
        # 4. AI 提取任务
        extracted = ai_service.extract_tasks(text)
        
        # 5. 写入 TaskCache
        for task_data in extracted:
            db.add(TaskCache(...))
        
        # 6. 标记已分析
        db_block.is_analyzed = True
```

## 7. 文档版本系统

### 7.1 自动快照

```python
AUTO_SNAPSHOT_INTERVAL_SECONDS = 30.0    # 30 秒间隔
AUTO_SNAPSHOT_ABS_CHAR_DELTA = 120       # 120 字符变化
AUTO_SNAPSHOT_RELATIVE_DELTA = 0.18      # 18% 相对变化
```

**触发条件**（满足任一）：
- 距离上次快照超过 30 秒
- 字符数变化超过 120
- 字符数变化比例超过 18%

### 7.2 破坏性操作备份

```python
PRE_DESTRUCTIVE_DROP_RATIO = 0.4         # 删除 40% 以上
PRE_DESTRUCTIVE_MIN_CHAR_COUNT = 80      # 最少 80 字符
```

**触发条件**：
- 原文档超过 80 字符
- 新内容比原内容少 40% 以上

### 7.3 恢复候选选择

```python
def get_recovery_candidates():
    candidates = []
    
    # 1. 最新版本
    candidates.append(latest_revision)
    
    # 2. 昨日版本（24 小时前）
    yesterday_cutoff = now - timedelta(hours=24)
    candidates.append(first_revision_before(yesterday_cutoff))
    
    # 3. 稳定版本（字符数最多）
    candidates.append(max(revisions, key=lambda r: r.char_count))
    
    return candidates[:3]
```

## 8. AI 服务

### 8.1 支持的 Provider

| Provider | 说明 |
|----------|------|
| `openai_compatible` | 任意 OpenAI 兼容端点 |
| `openai` | 官方 OpenAI 端点 |
| `siliconflow` | SiliconFlow（支持 enable_thinking） |
| `ollama` | 本地 Ollama 服务 |

### 8.2 请求配置

```python
@dataclass
class AIProviderConfig:
    provider: str
    api_base: str
    api_key: str
    model: str
    timeout_seconds: float = 20.0
    max_attempts: int = 2
    disable_thinking: bool = True
```

### 8.3 任务提取

```python
def extract_tasks(text: str) -> List[Dict]:
    # 1. 构建提示词
    prompt = f"""
    从以下文本中提取任务。返回 JSON 数组。
    每个任务包含：text（任务文本）、time_expr（时间表达式，可选）
    
    文本：{text}
    """
    
    # 2. 调用 LLM
    response = client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        timeout=self.timeout_seconds,
    )
    
    # 3. 解析 JSON
    return parse_json_response(response.content)
```

### 8.4 重试机制

```python
def extract_tasks_with_retry(text: str) -> List[Dict]:
    for attempt in range(max_attempts):
        try:
            return extract_tasks(text)
        except (TimeoutError, ConnectionError, HTTPStatusError) as e:
            if attempt == max_attempts - 1:
                raise AIServiceError(f"Failed after {max_attempts} attempts: {e}")
            time.sleep(0.5 * (attempt + 1))
```

## 9. 时间解析器

### 9.1 支持的表达式

| 类型 | 示例 |
|------|------|
| 相对日期 | 今天、明天、后天 |
| 周表达 | 下周一、下周日 |
| 月日 | 3月8日、12月25日 |
| 时间 | 10点、下午3点、晚上8点30分 |
| 组合 | 下周一10点、明天下午3点 |

### 9.2 解析逻辑

```python
def parse(text: str) -> Optional[datetime]:
    # 1. 解析日期
    date = parse_date(text)  # 今天/明天/下周X/X月X日
    
    # 2. 解析时间
    time = parse_time(text)  # X点/X点X分/上午/下午
    
    # 3. 合并
    if date and time:
        return datetime.combine(date.date(), time.time())
    return date
```

## 10. 认证系统

### 10.1 密码哈希

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

### 10.2 JWT Token

```python
from jose import jwt
from datetime import timedelta

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### 10.3 依赖注入

```python
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    payload = decode_token(token)
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
```

## 11. 关键文件索引

```
stream-note-api/app/
├── main.py
├── core/
│   ├── env.py
│   └── security.py
├── api/v1/
│   ├── router.py
│   ├── deps.py
│   └── endpoints/
│       ├── auth.py
│       ├── documents.py
│       ├── blocks.py
│       ├── tasks.py
│       └── ai.py
├── models/
│   ├── database.py
│   ├── user.py
│   ├── document.py
│   ├── document_revision.py
│   ├── block.py
│   ├── task.py
│   ├── ai_provider_setting.py
│   ├── silent_analysis_job.py
│   └── schema_version.py
├── services/
│   ├── ai_service.py
│   ├── time_parser.py
│   └── silent_analysis.py
└── alembic/
    └── versions/
```
