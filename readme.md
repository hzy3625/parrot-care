?# ParrotCare AI - 楣﹂箟鍋ュ悍琛屼负鐩戞祴绯荤??
## MVP V0.1 楠岃瘉鐗?
### 鏍稿績鍔熻兘
- 鐢ㄦ埛娉ㄥ唽鐧诲??- 鍒涘缓楣﹂箟妗ｆ??- 鎵嬫満褰曢煶涓婁紶
- 鍩虹闊抽鍒嗙被锛堟甯搁福鍙?灏栧??鎵戠繀/鎾炵锛?- 澶滈棿灏栧彨寮傚父妫€娴?- 寮傚父浜嬩欢鍒楄??- 鐢ㄦ埛鍙嶉鎸夐??- 鎺ㄩ€侀€氱??
### 鎶€鏈??- **鍚庣??*: Python FastAPI
- **鏁版嵁搴?*: PostgreSQL
- **AI**: PyTorch + librosa
- **瀛樺??*: MinIO (闊宠棰戞枃??

### 椤圭洰缁撴??```
parrot-care/
鈹溾攢鈹??backend/           # FastAPI 鍚庣????  鈹溾攢鈹??app/
??  ??  鈹溾攢鈹??api/       # API 璺????  ??  鈹溾攢鈹??models/    # 鏁版嵁妯″????  ??  鈹溾攢鈹??services/  # 涓氬姟閫昏緫
??  ??  鈹斺攢鈹??ai/        # AI 妯″瀷鏈嶅姟
??  鈹斺攢鈹??requirements.txt
鈹溾攢鈹??mobile/            # Flutter App
鈹溾攢鈹??docs/              # 鏂囨??鈹斺攢鈹??scripts/           # 鑴氭??```

### 寮€鍙戣繘搴?- [x] 鍚庣鍩虹妗嗘????- [x] 鐢ㄦ埛绯荤粺 ??- [x] 楣﹂箟妗ｆ ??- [x] 闊抽涓婁紶 ??- [x] AI 鍒嗙被妯″瀷锛圡VP瑙勫垯鍒ゆ柇????- [x] 寮傚父妫€娴???- [x] 浜嬩欢鍒楄????- [x] 鐢ㄦ埛鍙嶉 ??- [ ] 鎺ㄩ€侀€氱??- [ ] Flutter App
- [ ] 鏁版嵁搴撳垵濮嬪??- [ ] Docker閮ㄧ??## V0.4 Sprint 1 新增功能

### 用户认证增强
- 密码重置流程（邮件验证）
- 密码重置频率限制??小时内最??次）
- 密码强度校验（至??位，包含字母和数字）
- 个人信息管理（昵称、邮箱、通知偏好??
### 站内消息中心
- 消息创建与查??- 消息列表（分页、筛选）
- 未读计数
- 单条/批量标记已读
- 消息删除

### 健康档案总览
- 单鹦鹉健康总览????30天统计）
- 全鹦鹉健康总览
- 健康趋势分析（improving/stable/declining??- 智能建议生成

## 快速启??
### Docker 启动（推荐）
`ash
docker-compose up
`
访问??- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发启??`ash
cd backend
pip install -r requirements.txt
python main.py
`

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 自动化测??
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
- 健康档案（单??全部总览??
### 测试技术栈
- pytest + pytest-asyncio
- httpx (异步 HTTP 客户??
- SQLite 内存数据??- 事务回滚隔离
