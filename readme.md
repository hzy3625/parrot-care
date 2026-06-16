# ParrotCare AI - 鹦鹉健康行为监测系统

## MVP V0.1 验证版

### 核心功能
- 用户注册登录
- 创建鹦鹉档案
- 手机录音上传
- 基础音频分类（正常鸣叫/尖叫/扑翅/撞笼）
- 夜间尖叫异常检测
- 异常事件列表
- 用户反馈按钮
- 推送通知

### 技术栈
- **后端**: Python FastAPI
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **AI**: PyTorch + librosa
- **存储**: MinIO (音视频文件)
- **容器化**: Docker + Docker Compose

### 项目结构
```
parrot-care/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── config.py       # 应用配置（环境变量）
│   │   └── db.py           # 数据库连接
│   ├── alembic/            # 数据库迁移
│   ├── Dockerfile          # 容器构建
│   ├── requirements.txt
│   ├── .env.example        # 环境变量模板
│   └── docker-entrypoint.sh
├── scripts/                # 运维脚本
│   ├── migrate_sqlite_to_pg.py   # SQLite → PostgreSQL 迁移
│   └── verify_docker.py          # Docker 健康检查
├── docker-compose.yml      # 容器编排
├── .env.example            # Docker 环境变量模板
├── mobile/                 # Flutter App
├── docs/                   # 文档
└── web_app/                # Web 前端
```

### 开发进度
- [x] 后端基础框架 ✅
- [x] 用户系统 ✅
- [x] 鹦鹉档案 ✅
- [x] 音频上传 ✅
- [x] AI 分类模型（MVP规则判断） ✅
- [x] 异常检测 ✅
- [x] 事件列表 ✅
- [x] 用户反馈 ✅
- [x] Docker 容器化部署 ✅
- [x] PostgreSQL 支持 ✅
- [ ] 推送通知
- [ ] Flutter App

## V0.4 Sprint 1 新增功能

### 用户认证增强
- 密码重置流程（邮件验证）
- 密码重置频率限制（1小时内最多3次）
- 密码强度校验（至少8位，包含字母和数字）
- 个人信息管理（昵称、邮箱、通知偏好）

### 站内消息中心
- 消息创建与查看
- 消息列表（分页、筛选）
- 未读计数
- 单条/批量标记已读
- 消息删除

### 健康档案总览
- 单鹦鹉健康总览（7天/30天统计）
- 全鹦鹉健康总览
- 健康趋势分析（improving/stable/declining）
- 智能建议生成

---

## 🚀 快速启动

### 方式一：Docker 部署（推荐）

#### 1. 一键启动所有服务
```bash
# 复制环境变量模板
cp .env.example .env

# 启动所有服务（backend + PostgreSQL + MinIO）
docker-compose up -d
```

启动后访问：
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001（minioadmin / minioadmin）

#### 2. 可选：启动 pgAdmin
```bash
# 启动含 pgAdmin（数据库管理界面）
docker-compose --profile tools up -d
```
- **pgAdmin**: http://localhost:5050（admin@parrotcare.local / admin）

#### 3. 验证服务状态
```bash
# 自动验证所有服务
python scripts/verify_docker.py

# 或手动检查
curl http://localhost:8000/health
docker-compose ps
```

#### 4. 查看日志
```bash
docker-compose logs -f backend
docker-compose logs -f db
```

#### 5. 停止服务
```bash
docker-compose down          # 停止但保留数据
docker-compose down -v       # 停止并删除数据卷
```

### 方式二：本地开发（SQLite）

```bash
cd backend
pip install -r requirements.txt
python start.py
```

本地启动后访问：
- **API**: http://127.0.0.1:8000
- **API 文档**: http://127.0.0.1:8000/docs

---

## 🗄️ 数据库配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 URL | `sqlite+aiosqlite:///./parrotcare.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `dev-secret-key-change-in-production` |
| `MINIO_ENDPOINT` | MinIO 服务地址 | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO 访问密钥 | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO 秘密密钥 | `minioadmin` |
| `SMTP_HOST` | SMTP 服务器 | _(未设置则使用 Mock 模式)_ |

### 数据库连接 URL 格式

| 环境 | 示例 |
|------|------|
| **本地开发（SQLite）** | `sqlite+aiosqlite:///./parrotcare.db` |
| **Docker（PostgreSQL）** | `postgresql+asyncpg://postgres:password@db:5432/parrotcare` |
| **本地 PostgreSQL** | `postgresql+asyncpg://postgres:password@localhost:5432/parrotcare` |

### SQLite → PostgreSQL 数据迁移

如果你有 SQLite 中的现有数据，可以迁移到 PostgreSQL：

```bash
# 确保 PostgreSQL 已启动
docker-compose up -d db

# 运行迁移脚本
python scripts/migrate_sqlite_to_pg.py \
    --sqlite-path backend/parrotcare.db \
    --pg-url "postgresql://postgres:password@localhost:5432/parrotcare"

# 预览模式（不写入）
python scripts/migrate_sqlite_to_pg.py --dry-run
```

### Alembic 数据库迁移

```bash
cd backend

# 生成新迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 查看迁移历史
alembic history
```

---

## 📡 API 文档

启动后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 自动化测试

### 运行所有测试
```bash
cd backend
pytest test_sprint1.py -v
pytest tests/ -v
```

### 测试覆盖范围
- 用户认证（注册、登录）
- 密码重置（请求、确认、频率限制、强度校验）
- 个人信息（获取、更新、修改密码）
- 消息中心（创建、列表、标记已读）
- 健康档案（单个/全部总览）
- 推送设置（CRUD）
- DND 设置（CRUD）

### 测试技术栈
- pytest + pytest-asyncio
- httpx（异步 HTTP 客户端）
- SQLite 内存数据库（测试隔离，不影响生产数据）
- 事务回滚隔离

---

## 📝 环境变量文件

| 文件 | 用途 | 是否提交 Git |
|------|------|-------------|
| `.env.example` | 环境变量模板 | ✅ 是 |
| `.env` | 实际配置 | ❌ 否 |

项目根目录的 `.env` 用于 Docker Compose 变量。
`backend/.env` 用于后端应用变量。
