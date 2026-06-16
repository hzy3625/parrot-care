# ParrotCare Sprint 2 需求文档

**文档版本**: V1.0  
**撰写日期**: 2026-06-16  
**状态**: 已实现  
**Sprint 周期**: 2026-06-12 ~ 2026-06-16  

---

## 一、Sprint 2 目标

在 Sprint 1（用户身份管理 + 站内消息中心 + 健康档案总览）的基础上，Sprint 2 聚焦于 **异常事件的主动推送能力** 和 **AI 音频分类精度升级**，实现从"被动查询"到"主动预警"的产品跃迁。

| 需求 ID | 标题 | 优先级 | 故事点 | 说明 |
|---------|------|--------|--------|------|
| REQ-PARROT-013 | 推送通知系统 | P0 | 8 | 异常事件自动触发邮件 + 浏览器 + 站内消息推送，支持 DND 免打扰 |
| REQ-PARROT-014 | AI 音频分类升级 | P0 | 8 | 从 Mock 分类升级为基于 librosa + PyTorch 的 ML 模型，支持 5 类声音分类 |

**Sprint 2 总故事点**: 16 pts

---

## 二、REQ-PARROT-013：推送通知系统（P0，8 pts）

### 2.1 用户故事

> 作为一名鹦鹉主人，我希望在我的鹦鹉出现异常行为（夜间惊飞、持续尖叫等）时，能够**立即收到通知**，而不是等到下次打开 App 才看到。这样我可以及时查看鹦鹉状况，必要时采取干预措施。

### 2.2 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-013-1 | **异常事件触发推送**：当系统产生 `is_abnormal=true` 的 MediaEvent 时，自动触发推送流程 | 功能 |
| AC-013-2 | **推送内容完整**：通知包含鹦鹉名称、异常类型、事件时间、严重程度 | 功能 |
| AC-013-3 | **用户可配置推送开关**：用户可独立开关 `notification_email` 和 `notification_browser` | 功能 |
| AC-013-4 | **免打扰时段 (DND)**：DND 时段内抑制浏览器通知，邮件不抑制；critical 事件不受 DND 限制 | 功能 |
| AC-013-5 | **浏览器通知支持**：用户开启 browser 开关时，返回浏览器通知数据结构（由前端调用 Notification API 展示） | 功能 |
| AC-013-6 | **邮件通知**：发送 HTML 格式邮件通知，包含紧急标识 | 功能 |
| AC-013-7 | **站内消息同步创建**：每次异常事件推送同时创建站内消息记录 | 功能 |
| AC-013-8 | **推送失败不影响主流程**：推送异常时不阻断音频上传和事件记录 | 非功能 |

### 2.3 技术方案

#### 2.3.1 架构流程

```
音频上传 → classify_audio() → is_abnormal=true
    ↓
PushNotificationService.dispatch_for_event()
    ├── ① 查询鹦鹉 → 查询用户 → 获取推送配置
    ├── ② DND 检查（is_in_dnd）
    ├── ③ 邮件通知（EmailService.send_email，DND 不抑制）
    ├── ④ 站内消息（Notification 表 INSERT）
    └── ⑤ 浏览器通知数据（DND 时段 + 非 critical → 抑制）
    ↓
返回推送结果字典
```

#### 2.3.2 DND 逻辑

```python
def is_in_dnd(dnd_start, dnd_end, check_time):
    if not dnd_start or not dnd_end:
        return False
    if dnd_start <= dnd_end:       # 不跨午夜，如 14:00-16:00
        return dnd_start <= current <= dnd_end
    else:                           # 跨午夜，如 23:00-07:00
        return current >= dnd_start or current <= dnd_end
```

**DND 规则**:
- DND 时段内：浏览器通知被抑制，**邮件正常发送**
- `risk_level == "critical"`：**所有通知正常发送**，不受 DND 限制
- `notification_email = False`：不发送邮件
- `notification_browser = False`：不返回浏览器通知数据
- 站内消息**始终创建**（不受任何开关影响）

#### 2.3.3 推送内容模板

| 渠道 | 内容格式 |
|------|---------|
| 邮件 | HTML 模板：header 颜色按严重程度（critical=红色，其他=橙色），包含鹦鹉名称、品种、异常类型、严重程度、检测时间 |
| 站内消息 | Markdown 格式：`🦜 {鹦鹉名称} 异常行为提醒`，包含异常类型、严重程度、事件 ID |
| 浏览器通知 | JSON 数据：`{title, body, event_id, risk_level, timestamp}` |

### 2.4 API 设计

#### 2.4.1 获取推送设置

```
GET /api/settings/push
Authorization: Bearer {token}

Response 200:
{
    "notification_email": true,
    "notification_browser": true
}
```

#### 2.4.2 更新推送设置

```
PUT /api/settings/push
Authorization: Bearer {token}
Content-Type: application/json

{
    "notification_email": false,
    "notification_browser": true
}

Response 200: 同上
```

#### 2.4.3 获取 DND 设置

```
GET /api/settings/dnd
Authorization: Bearer {token}

Response 200:
{
    "dnd_start": "23:00",
    "dnd_end": "07:00"
}
```

#### 2.4.4 更新 DND 设置

```
PUT /api/settings/dnd
Authorization: Bearer {token}
Content-Type: application/json

{
    "dnd_start": "22:00",
    "dnd_end": "08:00"
}

Response 200: 同上

清空 DND:
{
    "dnd_start": null,
    "dnd_end": null
}
```

### 2.5 数据模型

无需新增表，复用 Sprint 1 已在 `users` 表中新增的字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `users.notification_email` | Boolean | True | 邮件通知开关 |
| `users.notification_browser` | Boolean | True | 浏览器通知开关 |
| `users.dnd_start` | Time (nullable) | NULL | DND 开始时间 |
| `users.dnd_end` | Time (nullable) | NULL | DND 结束时间 |
| `users.email` | String | NULL | 邮件地址 |
| `media_events.is_abnormal` | Boolean | False | 是否异常事件 |
| `media_events.risk_level` | String (nullable) | NULL | 风险等级 |

### 2.6 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/push_notification_service.py` | 新增 | 推送通知核心服务 |
| `backend/app/services/email_service.py` | 新增 | 异步邮件发送服务（支持 Mock 模式） |
| `backend/app/api/settings.py` | 新增 | 用户设置 API（推送配置、DND） |
| `backend/app/api/audio.py` | 变更 | 异常事件触发推送通知集成 |
| `backend/main.py` | 变更 | 注册 `/api/settings` 路由 |
| `backend/tests/test_push_notification.py` | 新增 | 推送服务测试（DND 逻辑 + 分发 + 标签） |
| `backend/tests/test_settings.py` | 新增 | 设置 API 集成测试 |

---

## 三、REQ-PARROT-014：AI 音频分类升级（P0，8 pts）

### 3.1 用户故事

> 作为一名鹦鹉主人，我希望系统能够**准确识别**我的鹦鹉的声音类型（正常鸣叫、尖叫、夜间惊飞、啄羽、安静），并针对异常声音给出相应的健康建议，而不仅仅是简单的"正常/异常"二分法。

### 3.2 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-014-1 | **5 类声音分类**：支持 normal_chirp（正常鸣叫）、scream（尖叫）、night_fright（夜间惊飞）、plucking（啄羽）、silence（安静） | 功能 |
| AC-014-2 | **特征提取**：使用 librosa 提取 MFCC、频谱中心、频谱滚降、过零率、RMS 能量、Chroma 等音频特征 | 功能 |
| AC-014-3 | **ML 模型推理**：使用 PyTorch MLP 模型进行分类，输入特征向量，输出类别概率 | 功能 |
| AC-014-4 | **模型降级机制**：模型文件不存在或 librosa 未安装时，降级为基于时间的 Mock 分类 | 非功能 |
| AC-014-5 | **风险等级映射**：night_fright → critical，scream → high，plucking → medium，normal_chirp/silence → None | 功能 |
| AC-014-6 | **异常标记**：scream、night_fright、plucking 标记为 `is_abnormal=true` | 功能 |
| AC-014-7 | **健康建议生成**：根据事件类型生成对应的中文健康建议 | 功能 |
| AC-014-8 | **合成训练数据**：支持生成合成特征数据用于模型训练和测试 | 非功能 |
| AC-014-9 | **模型保存/加载**：模型可保存为 `.pt` 文件，支持断点续训和最佳模型保存 | 非功能 |

### 3.3 技术方案

#### 3.3.1 模型架构

```
PyTorch MLP（多层感知机）:
Input (~44维特征) → Linear(44→128) → ReLU → Dropout(0.3)
    → Linear(128→64) → ReLU → Dropout(0.2)
    → Linear(64→5) → Softmax → 5 类概率
```

**损失函数**: CrossEntropyLoss  
**优化器**: Adam (lr=1e-3)  
**批次大小**: 32  

#### 3.3.2 特征工程

| 特征组 | 维度 | 说明 |
|--------|------|------|
| MFCC Mean | 13 | Mel 频率倒谱系数均值 |
| MFCC Std | 13 | Mel 频率倒谱系数标准差 |
| Spectral Centroid | 1 | 频谱中心（频率重心） |
| Spectral Rolloff | 1 | 频谱滚降点 |
| Spectral Bandwidth | 1 | 频谱带宽 |
| Zero Crossing Rate | 1 | 过零率 |
| RMS Mean | 1 | 均方根能量均值 |
| RMS Std | 1 | 均方根能量标准差 |
| Chroma Mean | 12 | 音高色度均值 |
| **总计** | **~44** | 动态计算（librosa 版本差异） |

#### 3.3.3 分类流程

```python
classify_audio(audio_path):
    1. 尝试加载 PyTorch 模型（单例模式）
    2. 如果模型可用 + librosa 已安装:
       a. extract_audio_features() → 特征向量
       b. model.predict() → (predicted_class, probabilities)
       c. 映射到 event_type, is_abnormal, risk_level
    3. 如果模型不可用:
       降级为 _mock_classify_audio()（基于当前时间判断）
```

#### 3.3.4 Mock 分类逻辑（降级方案）

| 条件 | 返回 |
|------|------|
| 21:00 ≤ hour 或 hour < 06:00 | `("night_fright", 0.85, True, "critical")` |
| 其他时段 | `("normal_chirp", 0.90, False, None)` |

#### 3.3.5 类别映射表

| 类别 ID | 英文名称 | 中文名称 | 风险等级 | 是否异常 |
|---------|---------|---------|---------|---------|
| 0 | normal_chirp | 正常鸣叫 | None | 否 |
| 1 | scream | 尖叫 | high | 是 |
| 2 | night_fright | 夜间惊飞 | critical | 是 |
| 3 | plucking | 啄羽 | medium | 是 |
| 4 | silence | 安静 | None | 否 |

### 3.4 健康建议

| 事件类型 | 建议 |
|---------|------|
| night_fright | 疑似夜惊，建议检查光线、噪声和笼布遮挡情况 |
| scream | 高频尖叫，可能应激或求关注，观察环境变化 |
| plucking | 啄羽行为，可能压力过大或营养不良，建议观察并咨询兽医 |
| normal_chirp | 正常鸣叫，无需处理 |
| silence | 安静状态，继续观察 |
| unknown | 建议观察鹦鹉状态，必要时咨询兽医 |

### 3.5 API 集成

音频上传端点 `POST /api/audio/upload` 在 Sprint 2 中增强：

1. 保存上传的音频文件
2. 调用 `classify_audio(audio_path)` 获取分类结果
3. 创建 `MediaEvent` 记录（包含 `is_abnormal`, `risk_level`, `confidence`）
4. 如果是异常事件，调用 `PushNotificationService.dispatch_for_event()` 触发推送
5. 返回事件结果（含健康建议）

### 3.6 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/audio_classifier.py` | 新增 | 音频分类服务（ML + Mock 降级） |
| `backend/app/services/audio_features.py` | 新增 | 音频特征提取（librosa） |
| `backend/app/services/audio_model.py` | 新增 | PyTorch MLP 模型 + 训练器 |
| `backend/app/api/audio.py` | 变更 | 集成 AI 分类 + 推送通知 |
| `backend/tests/test_audio_model.py` | 新增 | 模型 + 特征 + 分类器测试 |

---

## 四、故事点估算

### 4.1 估算方法

使用 Fibonacci 序列（1, 2, 3, 5, 8, 13），综合考虑：
- **功能复杂度**：逻辑复杂度、算法难度
- **工作量**：代码量、测试覆盖
- **不确定性**：技术风险、依赖外部因素

### 4.2 详细估算

| 需求 | 故事点 | 估算依据 |
|------|--------|---------|
| **REQ-PARROT-013 推送通知系统** | **8** | |
| ├─ PushNotificationService 核心逻辑 | 3 | DND 检查（含跨午夜）、多通道分发 |
| ├─ EmailService 邮件服务 | 2 | 异步 SMTP + HTML 模板 + Mock 模式 |
| ├─ Settings API（推送+DND CRUD） | 2 | 4 个端点 + 参数校验 + 认证 |
| └─ 集成测试 | 1 | DND 边界测试 + API 集成测试 |
| **REQ-PARROT-014 AI 音频分类升级** | **8** | |
| ├─ 音频特征提取（audio_features.py） | 2 | librosa 多组特征提取 + 维度计算 |
| ├─ PyTorch MLP 模型 + 训练器 | 3 | 模型定义、训练循环、保存/加载 |
| ├─ 分类服务集成（classifier.py） | 1 | ML + Mock 降级 + 建议生成 |
| └─ 测试覆盖 | 2 | 特征、模型、分类器三组测试 |
| **Sprint 2 总计** | **16** | |

---

**文档撰写人**: dev 团队  
**审阅状态**: 待 PO 确认
