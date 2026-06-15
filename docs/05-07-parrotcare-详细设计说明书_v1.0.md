# ParrotCare AI — 详细设计说明书

**文档版本**: V1.0
**创建日期**: 2026-06-12
**项目名称**: ParrotCare AI
**对应需求**: REQ-PARROT-001 / REQ-PARROT-002 / REQ-PARROT-003

---

## 一、系统架构

### 1.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | FastAPI (Python 3.10+) | 异步高性能，自动 API 文档 |
| 数据库 | SQLite (MVP) → PostgreSQL (生产) | 关系型数据存储 |
| ORM | SQLAlchemy 2.0 | 数据库模型映射 |
| AI 引擎 | librosa + 规则引擎 (MVP) → PyTorch (V1.0+) | 音频特征提取 + 分类 |
| 前端 | HTML5 + Bootstrap 5 (MVP) | 响应式 Web 应用 |
| 实时通信 | WebSocket (WebSocketManager) | 实时推送异常告警 |
| 容器化 | Docker + Docker Compose | 开发/部署环境 |

### 1.2 项目结构

```
parrot-care/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由层
│   │   │   ├── users.py      # 用户注册、登录
│   │   │   ├── parrots.py    # 鹦鹉档案管理
│   │   │   ├── events.py     # 事件查询、统计
│   │   │   └── audio.py      # 音频上传、分类
│   │   ├── models/           # 数据模型层
│   │   │   ├── database.py   # SQLAlchemy ORM 模型
│   │   │   └── schemas.py    # Pydantic 请求/响应 Schema
│   │   ├── services/         # 业务逻辑层
│   │   │   ├── audio_classifier.py   # 音频分类服务
│   │   │   └── realtime_analyzer.py  # 实时分析服务
│   │   ├── config.py         # 配置管理
│   │   └── db.py             # 数据库初始化
│   ├── main.py               # 应用入口
│   ├── start.py              # 启动脚本
│   ├── requirements.txt      # Python 依赖
│   ├── dockerfile            # 容器构建
│   └── .env.example          # 环境变量模板
├── web_app/
│   └── index.html            # Web 前端入口
├── docker-compose.yml        # 容器编排
└── docs/                     # 项目文档
```

### 1.3 模块设计

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Application             │
├─────────────┬─────────────┬─────────┬───────────┤
│  Users API  │ Parrots API │ Events  │ Audio API │
│  路由层     │  路由层     │  路由层 │  路由层   │
├─────────────┴─────────────┴─────────┴───────────┤
│              Pydantic Schemas (数据验证)         │
├─────────────┬───────────────────────────────────┤
│  SQLAlchemy │  Business Services                │
│  ORM Models │  ┌─────────────┬───────────────┐  │
│             │  │AudioClassifier│RealtimeAnalyzer│  │
├─────────────┴──┴─────────────┴───────────────┴──┤
│              SQLite / PostgreSQL                 │
└─────────────────────────────────────────────────┘
```

---

## 二、数据库设计

### 2.1 ER 图

```
users ────< parrots ────< media_events ────< user_feedback
  │           │              │
  └──< devices │              │
               └────> behavior_daily_stats
```

### 2.2 表结构

#### users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | VARCHAR(64) | PK | UUID |
| nickname | VARCHAR(100) | NULL | 昵称 |
| phone | VARCHAR(30) | UNIQUE, INDEX | 手机号 |
| email | VARCHAR(100) | UNIQUE, INDEX | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| subscription_status | VARCHAR(30) | DEFAULT 'free' | 订阅状态 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### parrots 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| parrot_id | VARCHAR(64) | PK | UUID |
| user_id | VARCHAR(64) | FK → users | 所属用户 |
| name | VARCHAR(100) | NOT NULL | 名称 |
| species | VARCHAR(100) | NOT NULL | 品种 |
| age | INTEGER | NULL | 年龄 |
| gender | VARCHAR(30) | NULL | 性别 |
| weight | DECIMAL(6,2) | NULL | 体重(g) |
| has_plucking_history | BOOLEAN | DEFAULT FALSE | 拔毛史 |
| has_night_fright_history | BOOLEAN | DEFAULT FALSE | 夜惊史 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### media_events 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| event_id | VARCHAR(64) | PK | UUID |
| parrot_id | VARCHAR(64) | FK → parrots | 所属鹦鹉 |
| device_id | VARCHAR(64) | FK → devices, NULL | 设备 ID |
| event_time | DATETIME | INDEX | 事件时间 |
| event_type | VARCHAR(100) | NOT NULL | 行为类型 |
| media_type | VARCHAR(30) | NOT NULL | 媒体类型 |
| audio_url | TEXT | NULL | 音频 URL |
| video_url | TEXT | NULL | 视频 URL |
| duration | DECIMAL(8,2) | NULL | 时长(秒) |
| confidence | DECIMAL(5,4) | NULL | 分类置信度 |
| is_abnormal | BOOLEAN | DEFAULT FALSE | 是否异常 |
| risk_level | VARCHAR(30) | NULL | 风险等级 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### user_feedback 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| feedback_id | VARCHAR(64) | PK | UUID |
| event_id | VARCHAR(64) | FK → media_events | 关联事件 |
| user_id | VARCHAR(64) | FK → users | 用户 ID |
| feedback_type | VARCHAR(50) | NOT NULL | 反馈类型 |
| feedback_label | VARCHAR(100) | NULL | 反馈标签 |
| comment | TEXT | NULL | 补充说明 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### behavior_daily_stats 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| stat_id | VARCHAR(64) | PK | UUID |
| parrot_id | VARCHAR(64) | FK → parrots | 所属鹦鹉 |
| stat_date | DATETIME | INDEX | 统计日期 |
| chirp_count | INTEGER | DEFAULT 0 | 鸣叫次数 |
| scream_count | INTEGER | DEFAULT 0 | 尖叫次数 |
| night_activity_count | INTEGER | DEFAULT 0 | 夜间活动次数 |
| active_minutes | INTEGER | DEFAULT 0 | 活跃分钟数 |
| quiet_minutes | INTEGER | DEFAULT 0 | 安静分钟数 |
| abnormal_event_count | INTEGER | DEFAULT 0 | 异常事件数 |
| health_score | INTEGER | DEFAULT 100 | 健康评分 |

---

## 三、API 设计

### 3.1 用户模块 `/api/users`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/register` | 用户注册 | phone, password, nickname | UserResponse |
| POST | `/login` | 用户登录 | phone, password | TokenResponse |

### 3.2 鹦鹉模块 `/api/parrots`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/` | 创建鹦鹉档案 | ParrotCreate | ParrotResponse |
| GET | `/` | 获取用户所有鹦鹉 | — | List[ParrotResponse] |
| GET | `/{parrot_id}` | 获取鹦鹉详情 | — | ParrotResponse |
| GET | `/{parrot_id}/summary` | 获取鹦鹉健康摘要 | — | ParrotSummary |

### 3.3 事件模块 `/api/events`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/` | 创建事件记录 | EventCreate | EventDetail |
| GET | `/parrot/{parrot_id}` | 获取鹦鹉事件列表 | days (query) | List[EventDetail] |
| GET | `/abnormal/parrot/{parrot_id}` | 获取异常事件列表 | days (query) | List[EventDetail] |
| GET | `/today-summary/parrot/{parrot_id}` | 获取今日摘要 | — | ParrotSummary |

### 3.4 音频模块 `/api/audio`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/upload` | 上传音频并分类 | AudioUpload | EventResponse |
| POST | `/upload-and-analyze` | 上传 + 实时分析 | AudioUpload | EventResponse |

---

## 四、核心业务逻辑

### 4.1 音频分类引擎 (AudioClassifier)

```
输入: 音频文件 (URL 或本地路径)
  ↓
1. 使用 librosa 提取音频特征
   - MFCC 系数
   - 频谱质心
   - 过零率
   - 频谱带宽
   - 频谱对比度
  ↓
2. 规则引擎分类 (MVP)
   - 高频 + 高能量 + 短持续 → scream (尖叫)
   - 中频 + 间歇 + 中等能量 → wing_flap (扑翅)
   - 低频 + 突发高能量 → cage_bump (撞笼)
   - 其他 → normal_chirp (正常鸣叫)
  ↓
输出: 分类结果 + 置信度
```

### 4.2 实时分析服务 (RealtimeAnalyzer)

```
输入: 音频流 / 上传的音频事件
  ↓
1. 时间窗口分析 (5 秒窗口)
  ↓
2. 夜间模式检测 (22:00-06:00)
   - 夜间活动频率阈值: 3 次/小时
   - 超过阈值 → risk_level = "high"
  ↓
3. 异常事件判断
   - 单事件异常 → risk_level = "low/medium"
   - 连续异常 (3+) → risk_level = "high"
  ↓
4. WebSocket 实时推送
   - 用户在线 → 推送事件通知
   - 用户离线 → 标记为未读，下次登录显示
  ↓
5. 健康评分计算
   - 基础分: 100
   - 尖叫事件: -10/次
   - 夜间异常: -15/次
   - 撞笼事件: -20/次
   - 最低分: 0
```

### 4.3 健康评分算法

```python
def calculate_health_score(parrot_id: str, date: datetime) -> int:
    base_score = 100
    events = get_daily_events(parrot_id, date)
    
    deductions = 0
    for event in events:
        if event.event_type == "scream":
            deductions += 10
        elif event.is_abnormal and is_night(event.event_time):
            deductions += 15
        elif event.event_type == "cage_bump":
            deductions += 20
    
    return max(0, base_score - deductions)
```

---

## 五、安全设计

| 安全措施 | 实现方式 |
|---------|---------|
| 密码加密 | bcrypt (salt rounds=12) |
| 认证方式 | JWT Bearer Token (有效期 24h) |
| CORS | 开发环境: *, 生产环境: 白名单 |
| 输入验证 | Pydantic Schema 自动校验 |
| SQL 注入 | SQLAlchemy ORM (参数化查询) |
| 文件上传 | 限制大小 < 10MB，仅允许音频格式 |

---

## 六、部署架构

### 6.1 开发环境

```
Docker Compose:
  - backend (FastAPI, port 8000)
  - SQLite (内置，持久化卷)
```

### 6.2 生产环境 (V1.0+)

```
Docker Compose:
  - backend (FastAPI, Gunicorn workers)
  - PostgreSQL (主数据库)
  - Redis (缓存 + WebSocket 消息队列)
  - MinIO (对象存储 - 音频/视频文件)
  - Nginx (反向代理 + 静态文件)
```

---

## 七、MVP 开发计划

| Sprint | 内容 | Story Points |
|--------|------|-------------|
| V0.1 | 用户系统 + 鹦鹉档案 + 基础音频分类 | 11 |
| V0.2 | 事件列表 + 异常检测 + 健康评分 | 11 |
| V0.3 | 实时分析 + WebSocket 推送 + 用户反馈 | 9 |

---

**文档状态**: V1.0 完成
**下次更新**: V0.3 完成后补充实时分析详细设计
