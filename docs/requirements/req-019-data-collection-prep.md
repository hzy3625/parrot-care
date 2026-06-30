# REQ-019 数据采集准备 - 完成汇报

## 任务完成情况

### ✅ 1. 检查现有音频分类代码

已检查现有代码结构，发现完整的音频分类系统：

**核心模块:**
- `apps/api/app/services/audio_features.py` - 特征提取（MFCC + 频谱特征）
- `apps/api/app/services/audio_classifier.py` - 分类服务（ML + Mock 降级）
- `apps/api/app/services/audio_model.py` - PyTorch MLP 模型
- `ml/training/train_model.py` - 模型训练脚本
- `ml/training/batch_extract_features.py` - 批量特征提取

**分类类别:**
| ID | 英文名 | 中文名 | 说明 |
|----|---------|--------|------|
| 0 | normal_chirp | 正常鸣叫 | 日常鸣叫、说话 |
| 1 | scream | 尖叫 | 高频、高能量 |
| 2 | night_fright | 夜间惊飞 | 突发、不规则 |
| 3 | plucking | 啄羽 | 低能量、不规律 |
| 4 | silence | 安静 | 极低能量 |

**特征维度: 43**
- MFCC mean/std (13 + 13 = 26)
- Spectral centroid (1)
- Spectral rolloff (1)
- Spectral bandwidth (1)
- Zero-crossing rate (1)
- RMS mean/std (2)
- Chroma mean (12)

### ✅ 2. 创建数据采集目录结构

已创建目录：
```
ml/datasets/audio/
├── normal_chirp/    # 正常鸣叫
├── scream/          # 尖叫
├── night_fright/    # 夜间惊飞
├── plucking/        # 啄羽
├── silence/         # 安静
└── README.md        # 数据采集指南
```

### ✅ 3. 创建特征提取脚本框架

现有脚本已完整：
- `ml/training/batch_extract_features.py` - 扫描音频、提取特征、导出 CSV
- 支持 WAV/MP3/FLAC/OGG 格式
- 输出格式：file_path, class_name, class_id, feature_0...feature_42

### ✅ 4. 创建合成数据生成器

已创建：
- `ml/training/generate_synthetic_training_data.py` - 新增独立脚本
- 可生成 1000+ 合成样本（每类 200）
- 输出 CSV 格式与真实数据一致
- 用于训练基线模型、验证流程

---

## 下一步计划（用户任务）

### 用户需要采集 ≥200 段真实音频数据

**采集要求:**
- 总计 ≥200 段（每类 ≥40 段）
- 建议每类 100+ 段
- 格式：WAV（首选）、MP3
- 时长：1-10 秒（建议 3-5 秒）
- 单声道录音

**采集流程:**
1. 使用手机录音（距离 0.5-2 米）
2. 录制各类鹦鹉声音
3. 分类放入对应目录
4. 使用 `batch_extract_features.py` 提取特征
5. 使用 `train_model.py` 训练模型

**详细指南:** `ml/datasets/audio/README.md`

---

## 使用指南

### 1. 基线训练（无真实数据时）

```bash
cd dev/parrot-care

# 安装依赖
pip install librosa torch numpy

# 生成合成训练数据
python ml/training/generate_synthetic_training_data.py \
    --output ml/datasets/synthetic_training_data.csv \
    --n-samples 1000

# 训练基线模型
python ml/training/train_model.py \
    --epochs 50 \
    --batch-size 32 \
    --model-path ml/models/audio_classifier.pt
```

### 2. 真实数据训练（采集后）

```bash
cd dev/parrot-care

# 提取真实音频特征
python ml/training/batch_extract_features.py \
    --input-dir ml/datasets/audio \
    --output data/training_data.csv

# 修改 train_model.py 使用真实数据
# （将 generate_synthetic_features 替换为 CSV 加载）

# 训练模型
python ml/training/train_model.py \
    --epochs 50 \
    --batch-size 32 \
    --model-path ml/models/audio_classifier.pt
```

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `ml/datasets/audio/{5个类别目录}/` | 音频数据存放目录 |
| `ml/datasets/audio/README.md` | 数据采集指南 |
| `ml/training/batch_extract_features.py` | 批量特征提取 |
| `ml/training/generate_synthetic_training_data.py` | 合成数据生成 |
| `ml/training/train_model.py` | 模型训练 |
| `apps/api/app/services/audio_features.py` | 特征提取 |
| `apps/api/app/services/audio_model.py` | ML 模型 |

---

## 总结

- ✅ 所有准备工作已完成
- ✅ 目录结构已创建
- ✅ 脚本框架已完整
- ⏳ 用户需要采集 ≥200 段真实音频数据
- 📖 详细指南见 `ml/datasets/audio/README.md`