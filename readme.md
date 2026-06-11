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