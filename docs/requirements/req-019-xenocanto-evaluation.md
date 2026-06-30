# REQ-019 Xeno-Canto 公开数据集接入评估

**编写:** dev | **日期:** 2026-06-23 | **目的:** 评估接入 Xeno-Canto 数据集的工作量、可行性和许可问题

---

## 一、Xeno-Canto 概述

[Xeno-Canto](https://xeno-canto.org) 是全球最大的野生动物声音共享数据库，包含 **500,000+ 鸟类录音**，覆盖全球鸟种。社区驱动， recordings 由全球鸟类爱好者和研究者上传。

### 关键特点
- **数据量:** 500,000+ 录音，覆盖 10,000+ 鸟种
- **鹦鹉相关:** Psittacidae（鹦鹉科）录音丰富，预估数千段
- **API:** 提供 REST API（v2/v3），支持按物种、属、行为类型搜索
- **Python 工具:** 有社区开发的 `xcapi` 和 `xeno-canto-py` 库

---

## 二、API 接入方案

### 2.1 API 版本

| 版本 | 状态 | 认证 | 说明 |
|------|------|------|------|
| v2 | 已废弃(返回404) | 无需 | 旧版 API，不再可用 |
| v3 | **当前版本** | 需要 API Key | 2024+ 启用，需注册获取 key |

### 2.2 API v3 接入流程

1. **注册账号:** 在 xeno-canto.org 注册（免费）
2. **获取 API Key:** 在账户设置页面申请
3. **API 端点:** `https://xeno-canto.org/api/3/recordings?query={query}&page={page}`
4. **查询参数:** 支持物种名、属名、行为类型、地区等

### 2.3 Python 工具选择

| 工具 | 说明 | 推荐度 |
|------|------|--------|
| `xcapi` | 官方推荐，轻量级 Python CLI | ⭐⭐⭐ |
| `xeno-canto-py` | 第三方 API wrapper，支持批量下载 | ⭐⭐⭐⭐ |
| 直接调用 API | urllib/requests 直调 | ⭐⭐⭐ |

**推荐:** 先用 `xeno-canto-py` 或直接 API 调用，避免额外依赖。

### 2.4 数据下载脚本设计

```python
# ml/datasets/download_xenocanto_data.py (拟开发)
# 1. 按鹦鹉科(Psittacidae)搜索录音
# 2. 下载音频文件到 ml/datasets/audio/{category}/
# 3. 提取特征并合并到训练数据
```

---

## 三、数据匹配评估

### 3.1 ParrotCare 5 类分类 vs Xeno-Canto 数据

| ParrotCare 类别 | Xeno-Canto 对应 | 可获取性 | 数据量预估 |
|----------------|----------------|---------|-----------|
| normal_chirp（正常鸣叫） | 鹦鹉 call/song 录音 | ✅ 容易 | 1000+ |
| scream（尖叫） | 鹦鹉 alarm/aggressive call | ⚠️ 中等 | 100-300 |
| night_fright（夜间惊飞） | 无直接对应类别 | ❌ 困难 | <50 |
| plucking（啄羽） | 无直接对应类别 | ❌ 不可获取 | ~0 |
| silence（安静） | 无对应（非生物声） | ❌ 不可获取 | 0 |

### 3.2 数据匹配结论

- **可直接获取:** normal_chirp（鹦鹉鸣叫录音丰富）
- **部分可获取:** scream（鹦鹉警报/攻击叫声有部分对应）
- **不可获取:** night_fright、plucking、silence — 这些是特定行为场景，Xeno-Canto 不覆盖

### 3.3 调整策略

建议将 Xeno-Canto 数据用于：
1. **normal_chirp 类别:** 下载鹦鹉日常鸣叫录音（最丰富）
2. **scream 类别:** 下载鹦鹉警报叫声录音（部分匹配）
3. **数据增强:** 作为预训练数据，迁移学习到 ParrotCare 模型

不可获取的类别（night_fright/plucking/silence）仍需真实采集。

---

## 四、版权与许可分析

### 4.1 Xeno-Canto 许可模式

Xeno-Canto 录音采用多种 Creative Commons 许可，**每条录音可能不同**：

| 许可类型 | 含义 | 商业使用 | ParrotCare 适用？ |
|---------|------|---------|------------------|
| CC-BY 4.0 | 署名即可使用 | ✅ 允许 | ✅ 可用 |
| CC-BY-NC 4.0 | 署名-非商业使用 | ❌ 禁止 | ⚠️ 看 ParrotCare 定位 |
| CC-BY-NC-SA 4.0 | 署名-非商业-相同共享 | ❌ 禁止商业 | ⚠️ 看 ParrotCare 定位 |
| CC-BY-SA 4.0 | 署名-相同共享 | ✅ 允许（需同许可） | ✅ 可用 |

### 4.2 关键许可问题

**ParrotCare 是商业项目还是非商业项目？**
- 如果 **非商业**（个人使用/研究/开源）: CC-BY-NC 录音可用
- 如果 **商业**（付费产品/SAAS）: 只能用 CC-BY 和 CC-BY-SA 录音

**建议:**
1. 下载时过滤只取 CC-BY 和 CC-BY-SA 许可的录音（确保商业安全）
2. 或者明确 ParrotCare 为非商业开源项目，使用所有 CC 录音
3. **必须标注数据来源** — 使用 Xeno-Canto 数据需在项目中注明

### 4.3 API 使用条款
- API v3 需要 API Key，可能有速率限制
- 大批量下载需遵守 fair use 政策
- 建议：分批下载，每次间隔 1-2 秒

---

## 五、工作量评估 (SP)

| 任务 | 工作量(SP) | 说明 |
|------|-----------|------|
| 注册 Xeno-Canto 账号 + 获取 API Key | 0.5 | 需 Owner 提供邮箱注册 |
| 开发下载脚本 | 2 | API 调用 + 音频下载 + 分类存储 |
| 数据清洗 + 格式转换 | 1 | 采样率统一、时长裁剪、格式转换 |
| 特征提取 + 合并训练数据 | 1 | 使用现有 batch_extract_features.py |
| 模型重训练（迁移学习） | 1.5 | 在基线模型基础上 fine-tune |
| 许可过滤 + 数据来源标注 | 0.5 | 过滤 CC-BY 录音，文档记录 |
| **合计** | **6.5 SP** | |

---

## 六、风险与对策

| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| API Key 申请被拒 | 无法通过 API 下载 | 低 | 改用网页手动下载 |
| 鹦鹉录音分类不精确 | 数据标签不准确 | 中 | 人工审核 + 试听抽样 |
| 许可限制 | 商业使用受限 | 中 | 过滤 CC-BY/CC-BY-SA 录音 |
| 5 类中仅 2 类可获取数据 | 模型覆盖不全 | 高 | normal_chirp + scream 先训练，其余等待真实数据 |
| 音频质量参差 | 特征提取噪声 | 中 | 质量筛选 + 数据清洗 |

---

## 七、建议方案

### 方案 A: Xeno-Canto 接入（推荐）
1. 注册 API Key
2. 开发下载脚本，搜索 Psittacidae 科录音
3. 筛选 CC-BY/CC-BY-SA 许可
4. 下载 normal_chirp 和 scream 类别数据
5. 特征提取 + 模型 fine-tune
6. **预计获得 200-500 段有效数据（2/5 类别）**
7. 工作量: 6.5 SP

### 方案 B: 混合方案
1. Xeno-Canto 获取 normal_chirp + scream 数据
2. 合成数据继续补充 night_fright/plucking/silence
3. 迁移学习: 先用 Xeno-Canto 数据预训练，再用合成数据 fine-tune
4. 等待 Owner 决策真实数据采集方案后补充

### 方案 C: 仅合成数据（当前方案）
- 不接入外部数据，维持现状
- 模型仅在合成数据上有效，真实场景表现未知
- **不推荐** — 无法验证真实场景效果

---

## 八、下一步行动

| 步骤 | 前置条件 | 负责 |
|------|---------|------|
| 1. 确认 ParrotCare 商业定位 | Owner 决策 | PO |
| 2. 注册 Xeno-Canto 账号 | 邮箱 | dev/Owner |
| 3. 获取 API Key | 账号注册完成 | dev |
| 4. 开发下载脚本 | API Key | dev |
| 5. 下载 + 清洗数据 | 脚本完成 | dev |
| 6. 模型 fine-tune | 数据准备完成 | dev |

**dev 可立即开始:** 步骤 4 的脚本框架开发（不依赖 API Key，先用 mock 数据测试脚本逻辑）。

---

## 九、Docker 本地验证状态

**PO 要求:** 在本地 `docker compose up` 做完整验证。

**当前环境状态:**
- ❌ Docker Desktop 未安装（机器上没有 docker 命令）
- ❌ Docker Compose 不可用

**阻塞:** 需要 Owner 在本机安装 Docker Desktop，或提供有 Docker 环境的机器。

**可在无 Docker 情况下做的准备工作:**
1. ✅ 检查 .env 配置完整性
2. ✅ 验证 Dockerfile 语法正确性
3. ✅ 验证 infra/docker-compose.yml 配置正确性
4. ⏳ 实际 `docker compose up` — 等待 Docker 环境

---

**结论:** Xeno-Canto 接入可行，建议采用方案 A/B。Docker 验证被环境阻塞，需 Owner 安装 Docker Desktop。
