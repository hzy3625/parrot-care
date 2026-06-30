# 音频数据采集方案 - Sprint 4B REQ-019

## 一、现有代码分析总结

### 1.1 现有架构
- **audio_classifier.py**: 主分类服务，集成 ML 模型 + Mock 降级
- **audio_features.py**: 特征提取（librosa MFCC + 频谱特征）
- **audio_model.py**: PyTorch MLP 模型（43 维输入 → 5 类输出）

### 1.2 特征提取方案（已实现）
- **MFCC 特征**: 13 个系数（均值 + 标准差）= 26 维
- **频谱特征**: centroid, rolloff, bandwidth, zero_crossing_rate = 4 维
- **能量特征**: RMS 均值 + 标准差 = 2 维
- **音调特征**: Chroma 均值 = 12 维
- **总维度**: ~43 维（实际可能因 librosa 版本略有差异）

### 1.3 分类类别
| 类别 ID | 类别名称 | 中文 | 是否异常 | 风险等级 |
|--------|---------|------|---------|---------|
| 0 | normal_chirp | 正常鸣叫 | 否 | None |
| 1 | scream | 尖叫 | 是 | high |
| 2 | night_fright | 夜间惊飞 | 是 | critical |
| 3 | plucking | 啄羽 | 是 | medium |
| 4 | silence | 安静 | 否 | None |

### 1.4 当前状态
- ✅ 特征提取代码已完成（audio_features.py）
- ✅ 模型架构已设计（audio_model.py）
- ⚠️ **缺少真实训练数据**（当前使用合成数据 generate_synthetic_features）
- ✅ 运行时模型位于 `ml/models/audio_classifier.pt`

---

## 二、数据采集方案设计

### 2.1 数据需求
**目标**: ≥200 段音频，每类至少 40 段

| 类别 | 目标数量 | 音频特征描述 | 采集难度 |
|------|---------|-------------|---------|
| normal_chirp | 40+ | 中等频率、中等能量、规律节奏 | ⭐ 容易 |
| scream | 40+ | 高频、高能量、尖锐刺耳 | ⭐⭐ 中等 |
| night_fright | 40+ | 突发高能量、不规则节奏、可能有翅膀扑动声 | ⭐⭐⭐ 较难 |
| plucking | 40+ | 低能量、不规则、啄羽声 | ⭐⭐⭐ 较难 |
| silence | 40+ | 极低能量、背景噪声为主 | ⭐ 容易 |

### 2.2 采集来源
1. **用户上传**: 通过前端录音功能采集（主要来源）
   - 用户手动录制鹦鹉声音
   - 标记类别（需前端 UI 支持）

2. **公开数据集**:
   - Xeno-Canto（鸟类声音数据库）- 可获取正常鸣叫
   - YouTube 鸟类视频 - 需手动提取

3. **合成数据**:
   - 使用现有 generate_synthetic_features() 作为辅助训练数据
   - 不替代真实数据，仅用于模型预热

### 2.3 音频格式要求
| 参数 | 要求 | 说明 |
|------|------|------|
| 格式 | WAV / MP3 | librosa 支持主流格式 |
| 采样率 | ≥22050 Hz | librosa 默认采样率 |
| 时长 | 3-10 秒 | 覆盖一个完整事件 |
| 单声道 | Mono | librosa 自动转换为 mono |
| 位深度 | 16-bit 或以上 | 标准 PCM |

### 2.4 数据标注流程
1. 用户录音 → 上传音频文件
2. 用户选择类别标签（5 类单选）
3. 系统提取特征 → 保存到数据库
4. 管理员审核 → 标记为"已验证"
5. 导出训练集 → 训练模型

---

## 三、特征提取代码框架（已实现）

### 3.1 核心函数
```python
extract_audio_features(audio_path) → np.ndarray  # ~43 维向量
get_feature_dim() → int                           # 返回实际维度
```

### 3.2 特征维度详解
| 特征组 | 维度 | 说明 |
|--------|------|------|
| MFCC mean | 13 | 梅尔频率倒谱系数均值 |
| MFCC std | 13 | MFCC 标准差 |
| Spectral centroid | 1 | 频谱中心频率 |
| Spectral rolloff | 1 | 频谱截止频率 |
| Spectral bandwidth | 1 | 频谱带宽 |
| Zero crossing rate | 1 | 过零率 |
| RMS mean | 1 | 能量均值 |
| RMS std | 1 | 能量标准差 |
| Chroma mean | 12 | 12 个半音音调特征 |
| **总计** | **43** | - |

### 3.3 使用示例
```python
from app.services.audio_features import extract_audio_features

features = extract_audio_features(audio_path="path/to/audio.wav")
print(f"特征维度: {features.shape}")  # (43,)
```

---

## 四、数据存储设计

### 4.1 数据库表结构建议
```sql
CREATE TABLE audio_samples (
    id SERIAL PRIMARY KEY,
    audio_path VARCHAR(255) NOT NULL,      -- 音频文件路径（MinIO）
    event_type VARCHAR(50) NOT NULL,       -- 类别标签
    confidence FLOAT DEFAULT 0.0,          -- 用户标注置信度（可选）
    features JSONB,                        -- 提取的特征向量
    is_verified BOOLEAN DEFAULT FALSE,     -- 是否已验证
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    verified_by INTEGER REFERENCES users(id)
);
```

### 4.2 MinIO 存储
- Bucket: `parrot-audio`
- Path pattern: `{event_type}/{YYYY-MM-DD}/{uuid}.wav`
- 举例: `normal_chirp/2026-06-22/a1b2c3d4.wav`

---

## 五、采集时间计划

### Sprint 4B 时间线（预估）
| 周次 | 任务 | 目标 |
|------|------|------|
| Week 1 | 前端录音 UI + 数据上传接口 | 完成采集工具 |
| Week 2 | 用户测试 + 初步采集（50 段） | 验证流程可行 |
| Week 3 | 批量采集（150 段） | 达到 200 段目标 |
| Week 4 | 数据清洗 + 特征提取 | 准备训练集 |

### MVP 目标
- **Week 2 结束**: 50 段数据 → 先训练一个初步模型
- **Week 4 结束**: 200 段数据 → 正式模型训练

---

## 六、技术风险与对策

### 6.1 采集风险
| 风险 | 影响 | 对策 |
|------|------|------|
| 夜间惊飞数据难采集 | 模型精度下降 | 模拟场景（关灯后突然开灯） |
| 啄羽声音不明显 | 特征提取困难 | 高灵敏度麦克风 + 放大音频 |
| 用户标注错误 | 数据质量下降 | 多人验证 + 管理员审核 |
| 数据不平衡 | 模型偏向多数类 | 增加少数类采集 + 过采样 |

### 6.2 技术对策
1. **数据增强**:
   - 音频剪辑、变速、加噪声
   - 使用 librosa.effects 进行增强

2. **过采样**:
   - 使用 SMOTE 或随机复制少数类

3. **迁移学习**:
   - 如数据不足，考虑预训练的音频模型（如 YAMNet）

---

## 七、下一步行动

### 7.1 Sprint 4B 任务清单
1. ✅ 分析现有代码（已完成）
2. ✅ 设计数据采集方案（已完成）
3. ✅ 准备特征提取框架（已实现）
4. 🔲 前端录音 UI 开发
5. 🔲 数据上传接口开发（POST /api/audio/upload）
6. 🔲 数据标注审核系统
7. 🔲 批量特征提取脚本
8. 🔲 模型训练脚本优化

### 7.2 立即可执行的任务
- **前端录音组件**: 使用 Web Audio API 录制鹦鹉声音
- **上传接口**: POST /api/audio/upload → 提取特征 → 存储
- **数据导出脚本**: 从数据库导出训练集 CSV

---

## 八、附录：类别特征分布（预期）

### 8.1 MFCC 特征分布（假设）
| 类别 | MFCC 1-3 | 频谱中心 | RMS |
|------|----------|---------|-----|
| normal_chirp | 中等 | 中等 | 中等 |
| scream | 高 | 高 | 高 |
| night_fright | 高（突发） | 高（突变） | 高（方差大） |
| plucking | 低 | 低 | 低 |
| silence | 极低 | 极低 | 极低 |

### 8.2 可区分性分析
- **normal_chirp vs scream**: 频谱中心 + 过零率明显不同
- **scream vs night_fright**: RMS 标准差不同（突发 vs 持续）
- **plucking vs silence**: RMS 能量差异明显
- **挑战**: night_fright 和 scream 可能重叠，需更多特征区分

---

**总结**: 数据采集是 Sprint 4B 的核心任务。现有代码架构已完善，但缺少真实数据。建议优先开发前端录音 UI，通过用户参与采集达到 200 段目标。
