# Stream Note - Agent 规则

## 代码知识文档按需读取

项目提供两份代码知识文档：

- 前端：`docs/frontend-code-knowledge.md`
- 后端：`docs/backend-code-knowledge.md`

执行任务时遵循“按需读取”原则，避免无关上下文：

1. 前端任务（Vue 组件、Pinia、路由、样式、前端 API 调用）优先读取前端文档。
2. 后端任务（FastAPI 路由、SQLAlchemy 模型、服务层、AI 提取链路）优先读取后端文档。
3. 跨端联调任务（接口契约、端到端流程、字段对齐）先读前端文档的 API 章节，再读后端文档对应 endpoint/模型章节。
4. 若任务范围明确且很小，只读取相关章节，不必通读全文。

## Python 代码规范

## Python 环境管理（后端）

后端 Python 环境统一使用 `uv`，不使用 `pip`：

1. 创建虚拟环境：`uv venv stream-note-api/.venv`
2. 添加依赖：`uv add <package>`（批量可用 `uv add -r stream-note-api/requirements.txt --frozen`）
3. 安装/同步依赖：`uv sync --python stream-note-api/.venv/Scripts/python.exe`
4. 启动服务：`uv run --python stream-note-api/.venv/Scripts/python.exe python -m uvicorn app.main:app --reload`
5. 禁止使用 `pip install` 或 `python -m pip`

## 数据库运行建议（稳健性）

在服务器/生产环境中，为避免数据库出现“锁死/数据不一致/迁移遗漏”等问题，按以下顺序执行：

1. **每次部署或升级后先跑安全迁移（带备份）**：
   - `uv run --python stream-note-api/.venv/Scripts/python.exe python stream-note-api/scripts/migrate_db.py`
2. **用健康检查作为 readiness**（会做 DB 连通性 + schema revision 检查）：
   - `GET /api/v1/health`
   - 返回 `503` 视为数据库不可用/未就绪（不要继续放量）
3. **需要手动备份时**：
   - `uv run --python stream-note-api/.venv/Scripts/python.exe python stream-note-api/scripts/backup_db.py`

注意：SQLite 更适合单机/轻并发写入场景；如果要多进程 worker 或高并发写入，建议迁移到 PostgreSQL。

### SQLAlchemy 模型类型注解

使用 `Mapped[T]` 和 `mapped_column` 进行严格的类型注解，确保 LSP/类型检查器能识别属性存在。

**正确做法:**
```python
from sqlalchemy.orm import Mapped, mapped_column

class Block(Base):
    __tablename__ = "blocks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    is_task: Mapped[bool] = mapped_column(Boolean, default=False)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

# 直接属性赋值
db_block.is_task = True
db_block.is_analyzed = True
```

**禁止做法:**
```python
# 禁止使用 setattr 进行动态属性赋值
setattr(db_block, "is_task", True)  # ❌ 丑陋且绕过类型检查
```

### 类型安全原则

1. **禁止 `setattr`**: 使用严格的类定义和类型注解，确保属性在编译时存在
2. **禁止 `getattr` 默认值**: 如果需要可选属性，在类定义中声明为 `Optional[T]`
3. **使用 `is None` 检查**: 避免对 SQLAlchemy 对象使用布尔真值检查

**正确做法:**
```python
if db_block is not None and db_block.is_analyzed:
    continue
```

**禁止做法:**
```python
if db_block and db_block.is_analyzed:  # ❌ SQLAlchemy Column 的 __bool__ 会抛出异常
    continue
```

### Dict 类型注解

从 JSON 列读取数据时，添加明确的类型注解:

```python
doc_content: Dict[str, Any] = doc.content if doc.content else {"type": "doc", "content": []}
```
