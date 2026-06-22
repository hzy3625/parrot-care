# 音频数据采集指南

本目录用于采集鹦鹉声音训练数据。采集完成后将用于训练音频分类模型。

## 目录结构

```
data/audio/
├── normal_chirp/    # 正常鸣叫（≥40段）
├── scream/          # 尖叫（≥40段）
├── night_fright/    # 夜间惊飞（≥40段）
├── plucking/        # 啄羽（≥40段）
├── silence/         # 安静（≥40段）
```

## 采集要求

### 最低数量
- **总计 ≥200 段**（每类 ≥40 段）
- 建议：每类 100+ 段以获得更好效果

### 音频格式
- **格式**: WAV（首选）、MP3、FLAC、OGG
- **采样率**: 22050 Hz 或更高
- **时长**: 1-10 秒（建议 3-5 秒）
- **单声道**: 单声道录音

### 录音设备
- 手机录音即可（iPhone/Android）
- 外接麦克风更好（提高质量）
- 避免背景噪声干扰

## 各类别说明

### 1. normal_chirp（正常鸣叫）
- 鹦鹉日常鸣叫、说话、轻声互动
- 采集时机：白天、喂食时、互动时
- 特征：中等能量、频率适中

### 2. scream（尖叫）
- 高频、高能量叫声
- 采集时机：受惊、求关注、紧张时
- 特征：高能量、高频

### 3. night_fright（夜间惊飞）
- 夜间突然惊醒、剧烈动作声
- 采集时机：关灯后、夜间突发
- 特征：突发高能量、不规则

### 4. plucking（啄羽）
- 啄羽毛、啄笼子的声音
- 采集时机：观察到啄羽行为时
- 特征：低能量、不规律

### 5. silence（安静）
- 无明显声音的环境录音
- 采集时机：鹦鹉安静休息时
- 特征：极低能量

## 采集流程

### 1. 准备录音设备
```bash
# 手机录音设置
- 关闭降噪功能（避免失真）
- 选择最高采样率
- 固定设备位置（减少移动噪声）
```

### 2. 录音操作
```bash
# 录音时注意：
- 距离鹦鹉 0.5-2 米
- 录制 3-5 秒片段
- 标记类别（方便分类）
- 避免重叠（每段独立事件）
```

### 3. 文件命名
```
建议命名格式：
normal_chirp_001.wav
normal_chirp_002.wav
scream_001.wav
...
```

### 4. 分类存放
将录音文件放入对应类别目录：
```
data/audio/normal_chirp/normal_chirp_001.wav
data/audio/scream/scream_001.wav
...
```

## 特征提取（自动化）

采集完成后，使用批量提取脚本：

```bash
# 进入项目目录
cd dev/parrot-care

# 安装依赖（如未安装）
pip install librosa torch numpy

# 提取特征并生成训练数据
python scripts/batch_extract_features.py \
    --input-dir data/audio \
    --output data/training_data.csv

# 查看提取结果
# CSV 包含：file_path, class_name, class_id, feature_0...feature_42
```

## 模型训练

特征提取后，使用合成数据训练基线模型：

```bash
# 训练基线模型（先使用合成数据）
python backend/train_model.py \
    --epochs 50 \
    --batch-size 32 \
    --model-path models/audio_classifier.pt

# 后续用真实数据训练（替换 train_model.py 中的数据源）
```

## 数据验证清单

完成采集后，检查以下内容：

- [ ] 每类 ≥40 段录音
- [ ] 文件格式正确（WAV/MP3）
- [ ] 文件已放入正确目录
- [ ] 录音质量良好（无背景噪声）
- [ ] 标签准确（类别正确）

## 联系支持

如有问题，请联系开发团队。