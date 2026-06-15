# ParrotCare V0.4 Sprint 1 自动化测试方案

**版本**: v1.0
**日期**: 2026-06-12
**负责人**: dev (开发工程师)

---

## 1. 测试范围

### 1.1 测试目标
验证 V0.4 Sprint 1 新增功能的 API 正确性、边界条件和错误处理。

### 1.2 功能范围

| 模块 | API 数量 | 测试用例数 |
|------|---------|-----------|
| 用户认证 | 4 | 4 |
| 密码重置 | 3 | 5 |
| 个人信息 | 4 | 5 |
| 消息中心 | 6 | 5 |
| 健康档案 | 2 | 2 |
| **总计** | **19** | **21** |

---

## 2. 测试用例列表

### 2.1 用户认证测试

| 编号 | 测试用例 | 验证点 |
|------|---------|-------|
| UC-01 | test_register_new_user | 注册成功，返回 token |
| UC-02 | test_register_duplicate_phone | 重复手机号返回 400 |
| UC-03 | test_login_success | 登录成功，返回 token |
| UC-04 | test_login_wrong_password | 密码错误返回 401 |

### 2.2 密码重置测试

| 编号 | 测试用例 | 验证点 |
|------|---------|-------|
| PR-01 | test_request_password_reset | 请求成功 |
| PR-02 | test_password_reset_frequency_limit | 第4次请求返回 429 |
| PR-03 | test_confirm_password_reset | 有效 Token 重置成功 |
| PR-04 | test_confirm_expired_token | 过期 Token 返回 400 |
| PR-05 | test_password_strength_validation | 弱密码返回 400 |

### 2.3 个人信息测试

| 编号 | 测试用例 | 验证点 |
|------|---------|-------|
| PF-01 | test_get_profile | 获取个人信息成功 |
| PF-02 | test_update_profile | 更新昵称/邮箱成功 |
| PF-03 | test_update_duplicate_email | 已占用邮箱返回 400 |
| PF-04 | test_change_password | 修改密码成功 |
| PF-05 | test_change_password_wrong_old | 旧密码错误返回 400 |

### 2.4 消息中心测试

| 编号 | 测试用例 | 验证点 |
|------|---------|-------|
| NT-01 | test_create_notification | 创建消息成功 |
| NT-02 | test_list_notifications | 分页列表正确 |
| NT-03 | test_unread_count | 未读计数正确 |
| NT-04 | test_mark_notification_read | 单条标记已读 |
| NT-05 | test_mark_all_read | 批量标记已读 |

### 2.5 健康档案测试

| 编号 | 测试用例 | 验证点 |
|------|---------|-------|
| HO-01 | test_health_overview_single | 单鹦鹉总览正确 |
| HO-02 | test_health_overview_all | 全鹦鹉总览正确 |

---

## 3. 测试环境配置

### 3.1 技术栈

| 类别 | 工具 | 版本 |
|------|------|------|
| 测试框架 | pytest | >=7.4.0 |
| 异步支持 | pytest-asyncio | >=0.21.0 |
| HTTP 客户端 | httpx | >=0.24.0 |
| 数据库 | SQLite (内存) | via aiosqlite |
| ORM | SQLAlchemy | >=2.0.0 |

### 3.2 测试数据库

- 使用 SQLite 内存数据库 (:memory:)
- 每个测试独立数据库实例
- 测试结束后事务回滚

### 3.3 测试隔离

- 每个测试函数独立的 db_session
- 使用 fixture 注入测试用户
- auth_client 自动携带认证 token

---

## 4. 运行方式

### 4.1 安装测试依赖
`ash
cd backend
pip install -r requirements.txt
`

### 4.2 运行全部测试
`ash
cd backend
pytest test_sprint1.py -v
`

### 4.3 运行单个测试
`ash
pytest test_sprint1.py::test_register_new_user -v
`

### 4.4 运行指定模块测试
`ash
pytest test_sprint1.py -k "password" -v
`

### 4.5 查看测试覆盖率（可选）
`ash
pytest test_sprint1.py --cov=app --cov-report=html
`

---

## 5. 测试结果预期

| 模块 | 预期结果 | 备注 |
|------|---------|------|
| 用户认证 | 全部通过 | 基础功能 |
| 密码重置 | 全部通过 | 含频率限制验证 |
| 个人信息 | 全部通过 | 含唯一性验证 |
| 消息中心 | 全部通过 | 含分页验证 |
| 健康档案 | 全部通过 | 含统计计算验证 |

**预期总计**: 21 个测试用例全部通过

---

## 6. 附录

### 6.1 测试文件结构
`
backend/
├── conftest.py          # 测试配置和 fixtures
├── test_sprint1.py      # Sprint 1 测试用例
└── requirements.txt     # 包含测试依赖
`

### 6.2 关键 fixtures

| Fixture | 作用 |
|---------|------|
| db_session | 异步数据库会话（事务回滚） |
| client | 异步 HTTP 客户端 |
| test_user | 测试用户（已注册） |
| auth_token | JWT token |
| auth_client | 带认证的 HTTP 客户端 |

---

**文档结束**