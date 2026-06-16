# ParrotCare Sprint 2 验收报告

**文档版本**: V1.0  
**验收人**: dev 团队  
**验收日期**: 2026-06-16  
**Sprint Goal**: 完成推送通知系统（P0-1）+ AI 音频分类升级（P0-2）

---

## 一、验收结论总览

| 需求 ID | 标题 | 优先级 | 故事点 | 验收结论 | 说明 |
|---------|------|--------|--------|----------|------|
| REQ-PARROT-013 | 推送通知系统 | P0 | 8 | ✅ **通过** | 推送服务、邮件通知、DND 免打扰、设置 API 全部实现，30 个测试用例全部通过 |
| REQ-PARROT-014 | AI 音频分类升级 | P0 | 8 | ✅ **通过** | 5 类音频分类、ML 模型 + Mock 降级、特征提取、建议生成全部实现，15 个测试用例全部通过 |

**总体结论**: ✅ **Sprint 2 通过**。两个 P0 需求的核心功能均已实现，后端逻辑完整，自动化测试覆盖全面（Sprint 2 新增 45 个测试用例，项目总计 68 个测试全部通过）。

---

## 二、详细验收结果

### 2.1 REQ-PARROT-013：推送通知系统（P0，8 pts）— ✅ 通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/services/push_notification_service.py | PushNotificationService 核心服务类 | ✅ 通过 |
| backend/app/services/push_notification_service.py | DND 检查逻辑（含跨午夜） | ✅ 通过 |
| backend/app/services/push_notification_service.py | dispatch_for_event 异常事件分发 | ✅ 通过 |
| backend/app/services/push_notification_service.py | HTML 邮件模板（含紧急标识） | ✅ 通过 |
| backend/app/services/email_service.py | 异步 SMTP 邮件发送 + Mock 模式 | ✅ 通过 |
| backend/app/api/settings.py | GET/PUT /api/settings/push 推送配置 | ✅ 通过 |
| backend/app/api/settings.py | GET/PUT /api/settings/dnd 免打扰配置 | ✅ 通过 |
| backend/app/api/audio.py | 异常事件触发推送集成 | ✅ 通过 |
| backend/main.py | /api/settings 路由注册 | ✅ 通过 |
| backend/app/models/database.py | users 表 DND/通知字段 | ✅ 通过 |
| backend/tests/test_push_notification.py | DND 逻辑 + 分发 + 标签测试（17 用例） | ✅ 通过 |
| backend/tests/test_settings.py | API 集成测试（13 用例） | ✅ 通过 |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-013-1 | 异常事件触发推送 | ✅ 通过 | dispatch_for_event 检查 is_abnormal，自动查询用户后分发通知 |
| AC-013-2 | 推送内容完整 | ✅ 通过 | 包含鹦鹉名称、异常类型（中文映射）、严重程度、事件时间、事件 ID |
| AC-013-3 | 用户可配置推送开关 | ✅ 通过 | GET/PUT /api/settings/push 支持独立开关 email 和 browser |
| AC-013-4 | 免打扰时段 (DND) | ✅ 通过 | 跨午夜逻辑正确（23:00-07:00），DND 抑制浏览器通知，邮件不抑制；critical 事件 bypass DND |
| AC-013-5 | 浏览器通知支持 | ✅ 通过 | 返回 {title, body, event_id, risk_level, timestamp} 数据结构 |
| AC-013-6 | 邮件通知 | ✅ 通过 | HTML 模板按风险等级着色（critical=红色），包含鹦鹉详情 |
| AC-013-7 | 站内消息同步创建 | ✅ 通过 | 每次异常事件均创建 Notification 记录，不受任何开关影响 |
| AC-013-8 | 推送失败不影响主流程 | ✅ 通过 | audio.py 中 try/except 包裹推送调用，异常时 pass 不阻断 |

#### 测试覆盖

| 测试类 | 用例数 | 状态 |
|--------|--------|------|
| TestDndLogic（DND 边界测试） | 9 | ✅ 全部通过 |
| TestPushDispatch（推送分发） | 6 | ✅ 全部通过 |
| TestEventLabels（标签映射） | 2 | ✅ 全部通过 |
| TestPushSettings（推送配置 API） | 6 | ✅ 全部通过 |
| TestDndSettings（DND 配置 API） | 7 | ✅ 全部通过 |
| **REQ-013 小计** | **30** | **✅ 30/30** |

#### DND 逻辑亮点

- 正确支持跨午夜场景（如 23:00-07:00），dnd_start > dnd_end 时使用 `current >= start OR current <= end`
- 边界值测试通过（DND 开始/结束时间点均视为在 DND 内）
- DND 时段内：浏览器通知抑制 ✅，邮件不抑制 ✅
- `risk_level == "critical"` 完全 bypass DND 检查 ✅
- 推送开关关闭时对应渠道不发送，但站内消息始终创建 ✅

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P13-01 | 🟢 低 | email 模板中使用 datetime.utcnow()（Python 3.12+ 已废弃） | 改为 datetime.now(datetime.timezone.utc) |
| P13-02 | 🟢 低 | 推送服务使用全局单例而非 FastAPI 依赖注入的独立实例 | 可考虑每次请求创建独立实例以支持多 SMTP 配置 |

---

### 2.2 REQ-PARROT-014：AI 音频分类升级（P0，8 pts）— ✅ 通过

#### 代码审查

| 文件 | 检查项 | 结果 |
|------|--------|------|
| backend/app/services/audio_classifier.py | classify_audio 分类入口 + Mock 降级 | ✅ 通过 |
| backend/app/services/audio_classifier.py | generate_suggestion 建议生成 | ✅ 通过 |
| backend/app/services/audio_features.py | librosa 特征提取（MFCC + 频谱 + Chroma） | ✅ 通过 |
| backend/app/services/audio_features.py | 特征维度动态计算 get_feature_dim() | ✅ 通过 |
| backend/app/services/audio_features.py | 合成训练数据生成 | ✅ 通过 |
| backend/app/services/audio_features.py | 类别映射 + 异常标记 + 风险等级 | ✅ 通过 |
| backend/app/services/audio_model.py | ParrotAudioClassifier MLP 模型定义 | ✅ 通过 |
| backend/app/services/audio_model.py | AudioClassifierTrainer 训练/预测/保存/加载 | ✅ 通过 |
| backend/app/api/audio.py | AI 分类集成 + 推送通知触发 | ✅ 通过 |
| backend/tests/test_audio_model.py | 特征 + 模型 + 分类器测试（15 用例） | ✅ 通过 |

#### 验收标准逐项检查

| AC | 描述 | 结论 | 详情 |
|----|------|------|------|
| AC-014-1 | 5 类声音分类 | ✅ 通过 | CLASS_NAMES 定义 5 类：normal_chirp, scream, night_fright, plucking, silence |
| AC-014-2 | 特征提取 | ✅ 通过 | MFCC(13+13) + 频谱(3) + ZCR(1) + RMS(2) + Chroma(12) ≈ 44 维 |
| AC-014-3 | ML 模型推理 | ✅ 通过 | MLP 3 层（44→128→64→5），softmax 输出概率，验证准确率 >70% |
| AC-014-4 | 模型降级机制 | ✅ 通过 | 模型不存在/依赖缺失时降级为基于时间的 Mock 分类 |
| AC-014-5 | 风险等级映射 | ✅ 通过 | night_fright→critical, scream→high, plucking→medium, 正常→None |
| AC-014-6 | 异常标记 | ✅ 通过 | ABNORMAL_CLASSES = {1, 2, 3} 对应 scream, night_fright, plucking |
| AC-014-7 | 健康建议生成 | ✅ 通过 | 每种事件类型有对应中文建议，unknown 类型有兜底建议 |
| AC-014-8 | 合成训练数据 | ✅ 通过 | generate_synthetic_features 生成带类别偏置的模拟特征 |
| AC-014-9 | 模型保存/加载 | ✅ 通过 | 保存为 .pt 文件，含 model_state_dict + 元数据，支持断点续训 |

#### 测试覆盖

| 测试类 | 用例数 | 状态 |
|--------|--------|------|
| TestAudioFeatures（特征提取） | 6 | ✅ 全部通过 |
| TestAudioModel（模型训练/预测） | 6 | ✅ 全部通过 |
| TestAudioClassifier（分类器集成） | 3 | ✅ 全部通过 |
| **REQ-014 小计** | **15** | **✅ 15/15** |

#### 模型性能亮点

- 使用合成数据训练 20 个 epoch 后，训练准确率 >80%
- 验证集准确率 >70%（合成数据分类任务较简单）
- 概率输出归一化正确（Σ = 1.0 ± 1e-5）
- 单样本预测接口正确
- 模型文件保存/加载后权重完全一致

#### 问题列表

| # | 严重程度 | 问题 | 建议 |
|---|---------|------|------|
| P14-01 | 🟢 低 | librosa 空频率集警告（测试用零信号时触发） | 不影响功能，测试中可忽略 |
| P14-02 | 🟢 低 | 当前模型为基线 MLP，未使用更先进的架构（CNN/RNN/Transformer） | 后续迭代可考虑升级模型架构 |

---

## 三、测试覆盖情况

### 3.1 Sprint 2 新增测试

| 测试文件 | 测试类/函数数 | 用例数 | 状态 |
|---------|-------------|--------|------|
| tests/test_push_notification.py | 3 个测试类 | 17 | ✅ 17/17 通过 |
| tests/test_settings.py | 2 个测试类 | 13 | ✅ 13/13 通过 |
| tests/test_audio_model.py | 3 个测试类 | 15 | ✅ 15/15 通过 |
| **Sprint 2 新增** | **8** | **45** | **✅ 45/45** |

### 3.2 全量测试

| 测试文件 | 用例数 | 状态 |
|---------|--------|------|
| test_sprint1.py | 23 | ✅ 全部通过 |
| tests/test_push_notification.py | 17 | ✅ 全部通过 |
| tests/test_settings.py | 13 | ✅ 全部通过 |
| tests/test_audio_model.py | 15 | ✅ 全部通过 |
| **总计** | **68** | **✅ 68/68** |

**测试执行环境**: Python 3.13.12, pytest 9.0.3, pytest-asyncio 1.4.0  
**测试执行时间**: ~18 秒  
**警告**: 18 条（均为 DeprecationWarning，不影响功能）

### 3.3 测试覆盖维度

| 维度 | 覆盖情况 |
|------|---------|
| DND 边界场景 | 跨午夜、边界时间点、DND 内外 ✅ |
| 推送分发 | 正常事件跳过、异常事件分发、DND 抑制、critical bypass、开关关闭 ✅ |
| API 认证 | 未授权访问返回 401/403 ✅ |
| API CRUD | 推送设置 GET/PUT、DND 设置 GET/PUT ✅ |
| 参数校验 | 无效时间格式返回 400 ✅ |
| 部分更新 | 只传一个字段时另一个保持不变 ✅ |
| 特征提取 | 维度一致性、合成数据完整性、类别定义 ✅ |
| 模型训练 | 训练循环、保存/加载、预测、有无验证集 ✅ |
| 分类器集成 | 建议生成、未知类型兜底、Mock 分类 ✅ |

---

## 四、遗留问题列表

| # | 严重程度 | 所属需求 | 问题 | 影响 | 建议 |
|---|---------|---------|------|------|------|
| ISS-01 | 🟢 低 | REQ-013 | datetime.utcnow() 在多处使用（Python 3.12+ 已废弃） | 无功能影响，仅警告 | 迁移到 datetime.now(datetime.timezone.utc) |
| ISS-02 | 🟢 低 | REQ-013 | PushNotificationService 使用全局单例 | 不支持多 SMTP 配置 | 可改为 FastAPI 依赖注入每次创建 |
| ISS-03 | 🟢 低 | REQ-014 | 当前使用基线 MLP 模型 | 分类精度有限（合成数据） | 后续迭代考虑 CNN/RNN 架构 |
| ISS-04 | 🟡 中等 | REQ-014 | Mock 分类逻辑过于简单（仅基于时间） | 演示环境可用，生产需真实模型 | 训练真实数据集后替换 Mock 逻辑 |
| ISS-05 | 🟡 中等 | REQ-013 | 前端浏览器通知逻辑未实现 | 用户无法在前端看到浏览器通知 | Sprint 3 补全 app.js 浏览器通知集成 |
| ISS-06 | 🟡 中等 | REQ-013 | WebSocket 实时推送未集成 | 当前浏览器通知数据需前端轮询或 SSE 获取 | 后续集成 WebSocket 或 SSE 推送 |

---

## 五、Sprint 2 完成度评估

| 维度 | 完成度 | 说明 |
|------|--------|------|
| 后端 API | ✅ 100% | 推送通知 + AI 分类所有 API 均已实现并测试通过 |
| 数据模型 | ✅ 100% | 复用 Sprint 1 新增字段，无需额外表结构变更 |
| 业务逻辑 | ✅ 100% | DND、降级、推送分发、ML 分类核心逻辑完整 |
| 测试覆盖 | ✅ 100% | Sprint 2 新增 45 个测试用例，全量 68/68 通过 |
| 前端集成 | ⚠️ 30% | 浏览器通知前端 JS 逻辑未实现（依赖 Sprint 1 app.js 遗留项） |
| 实时推送 | ❌ 0% | WebSocket 实时推送未实现（设计文档提及，暂未开发） |

**Sprint 2 总体完成度**: **约 85%**（后端功能完整，前端 + 实时推送待后续迭代）

---

## 六、Sprint 2 亮点

1. **DND 逻辑完善**：正确处理跨午夜场景、边界值、critical 事件 bypass
2. **降级策略合理**：AI 分类在模型不可用时优雅降级为 Mock，保证系统可用性
3. **推送失败容错**：推送异常不阻断主业务流程（音频上传 + 事件记录）
4. **测试覆盖全面**：DND 边界、API 认证、模型训练/加载、特征提取均有测试
5. **代码组织清晰**：服务层（services）与 API 层（api）分离，职责明确

---

## 七、Sprint 3 建议

1. **最高优先级**：补全 app.js，实现所有前端交互逻辑（Sprint 1 + Sprint 2 遗留）
2. **浏览器通知集成**：前端调用 Notification API 展示推送通知
3. **WebSocket 实时推送**：实现在线用户即时推送
4. **真实模型训练**：收集真实鹦鹉音频数据，训练替代 Mock 分类器
5. **模型升级**：考虑 CNN 或 Transformer 架构提升分类精度
6. **datetime 迁移**：全局替换 utcnow() 为 timezone-aware 版本

---

**报告撰写人**: dev 团队  
**审阅状态**: 待 PO 确认
