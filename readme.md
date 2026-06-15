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
- **数据库**: PostgreSQL
- **AI**: PyTorch + librosa
- **存储**: MinIO (音视频文件)

### 项目结构
```
parrot-care/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── models/    # 数据模型
│   │   ├── services/  # 业务逻辑
│   │   └── ai/        # AI 模型服务
│   └── requirements.txt
├── mobile/            # Flutter App
├── docs/              # 文档
└── scripts/           # 脚本
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
- [ ] 推送通知
- [ ] Flutter App
- [ ] 数据库初始化
- [ ] Docker部署

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

## 快速启动

### Docker 启动（推荐）
`ash
docker-compose up
`
访问：
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发启动
`ash
cd backend
pip install -r requirements.txt
python main.py
`

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 自动化测试

### 运行 Sprint 1 测试
`ash
cd backend
pytest test_sprint1.py -v
`

### 测试覆盖范围
- 用户认证（注册、登录）
- 密码重置（请求、确认、频率限制、强度校验）
- 个人信息（获取、更新、修改密码）
- 消息中心（创建、列表、标记已读）
- 健康档案（单个/全部总览）

### 测试技术栈
- pytest + pytest-asyncio
- httpx (异步 HTTP 客户端)
- SQLite 内存数据库
- 事务回滚隔离
