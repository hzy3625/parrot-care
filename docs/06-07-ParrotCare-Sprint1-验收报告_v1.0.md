# ParrotCare Sprint 1 验收报告

**文档版本**: V1.0  
**验收人**: ba (Product Owner)  
**验收日期**: 2026-06-12  
**Git Commit**: d7ff50 feat: V0.4 Sprint 1\  
**Sprint Goal**: 完成用户身份管理核心能力（密码重置、个人信息管理）+ 站内消息中心 + 健康档案总览页

---

## 一、验收结论总览

| 需求 ID | 标题 | 优先级 | 故事点 | 验收结论 | 说明 |
|---------|------|--------|--------|----------|------|
| REQ-PARROT-011 | 密码重置 | P0 | 5 | ⚠️ **部分通过** | 后端 API 完整，前端 JS 缺失，缺少密码强度校验和频率限制 |
| REQ-PARROT-005 | 站内消息中心 | P0 | 5 | ⚠️ **部分通过** | 后端 API 完整，前端 JS 缺失，缺少消息自动归档机制 |
| REQ-PARROT-009 | 健康档案总览页 | P1 | 3 | ⚠️ **部分通过** | 后端 API 完整，前端 JS 缺失，缺少排序功能 |
| REQ-PARROT-012 | 个人信息管理 | P1 | 3 | ⚠️ **部分通过** | 后端基本完整，前端 JS 缺失，缺少修改密码、通知偏好、邮箱验证 |

**总体结论**: ⚠️ **Sprint 1 部分通过**。后端 4 个需求的 API 均已实现，数据结构正确；但 **前端交互逻辑 (app.js) 完全缺失**，导致所有功能无法在浏览器中使用。

---

## 二、详细验收结果

### 2.1 REQ-PARROT-011：密码重置（P0，5 pts）— 部分通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/api/users.py | POST /reset-password 请求重置 API | ✅ 通过 |
| backend/app/api/users.py | POST /reset-password/{token} 确认重置 API | ✅ 通过 |
| backend/app/models/database.py | PasswordResetToken 表结构 | ✅ 通过 |
| backend/app/models/schemas.py | PasswordResetRequest/Confirm/Response Schema | ✅ 通过 |
| web_app/index.html | 重置密码页面（请求表单） | ✅ 通过 |
| web_app/app.js | 前端交互逻辑 | ❌ **文件不存在** |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-011-1 | 发起重置：输入邮箱提交，发送重置邮件 | ⚠️ 部分通过 | 后端 API 可用，邮件为 Mock 模式（开发环境合理），但前端无 JS 调用逻辑 |
| AC-011-2 | 重置链接：邮件中链接有效期 1 小时 | ✅ 通过 | expires_at = datetime.utcnow() + timedelta(hours=1) 正确实现 |
| AC-011-3 | 设置新密码：输入新密码，提交后更新 | ⚠️ 部分通过 | 后端 token 验证 + 密码更新逻辑正确，但缺少设置新密码页面（仅有请求页面，无 token 确认页） |
| AC-011-4 | 密码强度：密码至少 8 位，需含字母+数字 | ❌ **不通过** | 后端无密码强度校验（hash_password 直接接受任意长度/格式的密码），前端无校验逻辑 |
| AC-011-5 | 安全限制：已使用的链接提示已失效 | ✅ 通过 | is_used == False 条件检查正确 |
| AC-011-6 | 频率限制：1 小时内最多 3 次重置 | ❌ **不通过** | 后端无频率限制逻辑，可无限次发起重置请求 |

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P11-01 | 🔴 严重 | app.js 不存在，前端无任何交互逻辑 | 优先补全 app.js，实现密码重置全流程 |
| P11-02 | 🔴 严重 | 缺少设置新密码页面（输入 token + 新密码） | 需在 index.html 中新增页面，或在 app.js 中通过 URL 参数处理 |
| P11-03 | 🟡 中等 | 密码无强度校验 | 后端 PasswordResetConfirm schema 中增加 @field_validator，要求长度 >= 8 且含字母+数字 |
| P11-04 | 🟡 中等 | 无频率限制 | 在 request_password_reset 中增加同一邮箱/用户的请求次数限制（1 小时 3 次） |
| P11-05 | 🟡 中等 | 密码加密使用 SHA-256 而非 bcrypt | sprint-backlog 备注提到使用 bcrypt，实际代码使用 hashlib.sha256，安全性不足 |
| P11-06 | 🟢 低 | datetime.utcnow() 已废弃（Python 3.12+） | 建议改为 datetime.now(datetime.timezone.utc) |

---

### 2.2 REQ-PARROT-005：站内消息中心（P0，5 pts）— 部分通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/api/notifications.py | POST 创建消息 | ✅ 通过 |
| backend/app/api/notifications.py | GET 消息列表（分页、筛选、未读计数） | ✅ 通过 |
| backend/app/api/notifications.py | GET /unread-count 未读计数 | ✅ 通过 |
| backend/app/api/notifications.py | PATCH /mark-read 批量标记已读 | ✅ 通过 |
| backend/app/api/notifications.py | PATCH /{id}/read 单条标记已读 | ✅ 通过 |
| backend/app/api/notifications.py | DELETE /{id} 删除消息 | ✅ 通过 |
| backend/app/models/database.py | Notification 表结构 | ✅ 通过 |
| backend/app/models/schemas.py | Notification 相关 Schema | ✅ 通过 |
| web_app/index.html | 消息中心弹窗 + 列表 + 筛选按钮 | ✅ 通过 |
| web_app/app.js | 前端交互逻辑 | ❌ **文件不存在** |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-005-1 | 消息列表：显示未读消息，最新在前 | ⚠️ 部分通过 | 后端正确排序（desc created_at）+ 分页，但前端无 JS 渲染 |
| AC-005-2 | 未读标记：导航栏显示红点+数量 | ⚠️ 部分通过 | 后端有 /unread-count 端点，前端 HTML 有 badge 元素，但无 JS 联动 |
| AC-005-3 | 消息分类：按类型筛选 | ⚠️ 部分通过 | 后端支持 notification_type 筛选，前端有筛选按钮，无 JS |
| AC-005-4 | 一键已读：全部标记为已读 | ⚠️ 部分通过 | 后端 PATCH /mark-read 支持批量，前端有按钮，无 JS |
| AC-005-5 | 消息详情：点击跳转到事件详情 | ❌ **不通过** | 后端返回 related_parrot_id 和 related_event_id，但前端无跳转逻辑 |
| AC-005-6 | 消息保留：30 天后自动归档 | ❌ **不通过** | 数据库缺少 expires_at 字段，无自动归档机制 |

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P05-01 | 🔴 严重 | app.js 不存在 | 补全前端消息中心全部交互逻辑 |
| P05-02 | 🟡 中等 | 缺少消息自动归档/过期机制 | 数据库增加 expires_at 字段，添加定时任务清理过期消息 |
| P05-03 | 🟡 中等 | 缺少全部标记已读专用 API | 当前仅支持批量传入 ID 列表，建议增加 /read-all 端点 |
| P05-04 | 🟢 低 | WebSocket 实时推送未实现 | 需求文档提及在线用户即时推送，当前未集成 |

---

### 2.3 REQ-PARROT-009：健康档案总览页（P1，3 pts）— 部分通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/api/parrots.py | GET /{parrot_id}/health-overview | ✅ 通过 |
| backend/app/api/parrots.py | GET /health-overview（全部鹦鹉） | ✅ 通过 |
| backend/app/models/database.py | BehaviorDailyStat 表 | ✅ 通过 |
| backend/app/models/schemas.py | HealthOverview Schema | ✅ 通过 |
| web_app/index.html | 健康总览卡片 UI | ✅ 通过 |
| web_app/app.js | 前端交互逻辑 | ❌ **文件不存在** |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-009-1 | 鹦鹉卡片：显示名称、健康评分、最近异常 | ⚠️ 部分通过 | 后端返回 current_health_score + abnormal_event_count，但缺少最近异常事件时间字段 |
| AC-009-2 | 评分颜色：>=80 绿、60-79 黄、<60 红 | ⚠️ 部分通过 | CSS 类已定义，但无 JS 动态应用逻辑 |
| AC-009-3 | 快速操作：点击跳转到详细档案 | ⚠️ 部分通过 | 前端有健康总览按钮，无 JS 导航 |
| AC-009-4 | 排序：按评分/名称/最近异常排序 | ❌ **不通过** | 后端不支持排序参数，前端无排序控件 |

#### 后端逻辑亮点
- 健康趋势计算合理（近 3 天 vs 前 4 天平均健康评分对比）
- 建议生成逻辑完善（根据拔羽历史、夜惊历史、异常事件数生成个性化建议）

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P09-01 | 🔴 严重 | app.js 不存在 | 补全前端健康总览交互 |
| P09-02 | 🟡 中等 | 缺少最近异常事件时间返回字段 | HealthOverview schema 增加 latest_abnormal_time 字段 |
| P09-03 | 🟡 中等 | 不支持排序 | 后端 health-overview API 增加 sort_by 参数（score/name/latest_abnormal） |
| P09-04 | 🟢 低 | get_all_health_overview 循环调用单个 API，N+1 查询 | 建议优化为单次批量查询，减少数据库往返 |

---

### 2.4 REQ-PARROT-012：个人信息管理（P1，3 pts）— 部分通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/api/users.py | GET /profile 获取个人信息 | ✅ 通过 |
| backend/app/api/users.py | PUT /profile 更新个人信息 | ✅ 通过 |
| backend/app/models/schemas.py | ProfileUpdate / ProfileResponse | ✅ 通过 |
| web_app/index.html | 个人信息编辑弹窗 | ✅ 通过 |
| web_app/app.js | 前端交互逻辑 | ❌ **文件不存在** |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-012-1 | 编辑资料：修改昵称、邮箱，保存后生效 | ⚠️ 部分通过 | 后端 PUT /profile 正确实现（含唯一性校验），前端无 JS |
| AC-012-2 | 修改密码：输入旧密码+新密码更新 | ❌ **不通过** | 无修改密码 API 端点 |
| AC-012-3 | 通知偏好：开关邮件/浏览器通知 | ❌ **不通过** | 数据库缺少 notification_email/notification_browser 字段，无相关 API |
| AC-012-4 | 邮箱验证：修改邮箱需验证 | ❌ **不通过** | 无邮箱验证流程，数据库缺少 email_verified 字段 |

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P12-01 | 🔴 严重 | app.js 不存在 | 补全前端个人信息编辑交互 |
| P12-02 | 🟡 中等 | 缺少修改密码功能 | 新增 POST /users/me/change-password 端点 |
| P12-03 | 🟡 中等 | 缺少通知偏好管理 | 数据库增加 notification_email/notification_browser 字段，API 支持更新 |
| P12-04 | 🟡 中等 | 缺少邮箱验证流程 | 实现邮箱验证 Token 机制 |
| P12-05 | 🟢 低 | 头像上传未实现 | ProfileResponse.avatar_url 返回 None，需后续迭代 |

---

## 三、共性问题

### 3.1 前端 app.js 完全缺失 🔴

所有 4 个需求的前端交互逻辑均未实现。index.html 中引用了 app.js，但该文件不存在。这是 Sprint 1 **最大的交付缺口**，导致：
- 登录/注册按钮无响应
- 密码重置流程无法完成
- 消息中心无法加载和交互
- 健康总览无法获取数据
- 个人信息无法编辑

**建议**：将 app.js 的开发列为 Sprint 1 的最高优先级遗留项，或在 Sprint 2 开始时优先完成。

### 3.2 安全相关

| 问题 | 影响 | 建议 |
|------|------|------|
| 密码使用 SHA-256 而非 bcrypt | 彩虹表攻击风险 | 迁移到 passlib[bcrypt] |
| 无频率限制 | 密码重置接口可被滥用 | 增加滑动窗口限流 |
| 无密码强度校验 | 用户可设置弱密码 | 后端增加 validator |

### 3.3 数据模型缺口

| 缺失字段 | 所属表 | 影响需求 |
|---------|--------|---------|
| expires_at | notifications | AC-005-6 消息归档 |
| notification_email | users | AC-012-3 通知偏好 |
| notification_browser | users | AC-012-3 通知偏好 |
| email_verified | users | AC-012-4 邮箱验证 |
| dnd_start / dnd_end | users | 免打扰时段（US-006） |

---

## 四、Sprint 1 完成度评估

| 维度 | 完成度 | 说明 |
|------|--------|------|
| 后端 API | ✅ 95% | 4 个需求的核心 API 均已实现，逻辑正确 |
| 数据模型 | ⚠️ 80% | 基础表已创建，但缺少部分辅助字段（expires_at 等） |
| 前端 UI（HTML） | ✅ 90% | 页面结构完整，弹窗/表单/按钮均已就绪 |
| 前端交互（JS） | ❌ 0% | app.js 完全缺失 |
| 安全性 | ⚠️ 50% | 基本认证可用，但缺少密码强度/频率限制 |
| 测试 | ❌ 0% | 无自动化测试代码 |

**Sprint 1 总体完成度**: 约 **60%**（后端 + 前端 UI 完成，前端交互 + 安全 + 测试缺失）

---

## 五、Sprint 2 建议

1. **最高优先级**：补全 app.js，实现所有 Sprint 1 功能的前端交互
2. **安全加固**：密码加密迁移到 bcrypt，增加密码强度校验和频率限制
3. **数据模型补全**：增加缺失字段，实现消息归档机制
4. **自动化测试**：为核心 API 编写 pytest 测试用例
5. **Sprint 1 遗留项**：修改密码 API、通知偏好、邮箱验证、消息排序

---

**报告撰写人**: ba (Product Owner)  
**审阅状态**: 待 dev 团队确认
