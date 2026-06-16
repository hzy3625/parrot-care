# -*- coding: utf-8 -*-
"""音频特征提取 - 使用 librosa 提取 MFCC、频谱等特征"""

import numpy as np
from typing import Dict, Optional

try:
    import librosa
    import librosa.feature
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


def extract_audio_features(
    audio_path: Optional[str] = None,
    audio_data: Optional[np.ndarray] = None,
    sr: int = 22050,
    n_mfcc: int = 13
) -> np.ndarray:
    """提取音频特征向量
    
    Args:
        audio_path: 音频文件路径
        audio_data: 原始音频数据 (numpy array)
        sr: 采样率
        n_mfcc: MFCC 系数数量
    
    Returns:
        特征向量 (numpy array, shape: (feature_dim,))
    """
    if audio_path is None and audio_data is None:
        raise ValueError("需要提供 audio_path 或 audio_data")
    
    if not HAS_LIBROSA:
        raise ImportError("librosa 未安装，请运行: pip install librosa")
    
    # 加载音频
    if audio_path:
        y, sr_loaded = librosa.load(audio_path, sr=sr, mono=True)
    else:
        y = audio_data.astype(np.float32)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
    
    # 1. MFCC (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfcc_mean = np.mean(mfccs, axis=1)
    mfcc_std = np.std(mfccs, axis=1)
    
    # 2. Spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
    
    # 3. RMS Energy
    rms = librosa.feature.rms(y=y)[0]
    
    # 4. Chroma features (音调特征)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    
    # 拼接所有特征
    features = np.concatenate([
        mfcc_mean,           # 13
        mfcc_std,            # 13
        [np.mean(spectral_centroid)],   # 1
        [np.mean(spectral_rolloff)],    # 1
        [np.mean(spectral_bandwidth)],  # 1
        [np.mean(zero_crossing_rate)],  # 1
        [np.mean(rms)],                 # 1
        [np.std(rms)],                  # 1
        chroma_mean,         # 12
    ])
    
    return features


_cached_feature_dim: int = None

def get_feature_dim(n_mfcc: int = 13) -> int:
    """获取特征向量维度 (动态计算并缓存)
    
    由于不同 librosa 版本返回的特征维度可能略有差异，
    这里通过实际提取一个样本的维度来确定。
    """
    global _cached_feature_dim
    if _cached_feature_dim is not None:
        return _cached_feature_dim
    
    if not HAS_LIBROSA:
        _cached_feature_dim = n_mfcc * 2 + 18  # fallback
        return _cached_feature_dim
    
    # Generate 0.1s of silence to measure actual feature dim
    y = np.zeros(2205)  # 0.1s at 22050 Hz
    mfccs = librosa.feature.mfcc(y=y, sr=22050, n_mfcc=n_mfcc)
    chroma = librosa.feature.chroma_stft(y=y, sr=22050)
    
    _cached_feature_dim = (
        mfccs.shape[0] +  # mfcc mean
        mfccs.shape[0] +  # mfcc std
        3 +  # spectral centroid, rolloff, bandwidth
        1 +  # zcr
        2 +  # rms mean + std
        chroma.shape[0]  # chroma mean
    )
    return _cached_feature_dim


def generate_synthetic_features(
    n_samples: int = 100,
    feature_dim: Optional[int] = None
) -> tuple:
    """生成合成训练数据（用于演示和测试）
    
    生成 5 类鹦鹉声音的模拟特征：
    - 0: normal_chirp (正常鸣叫)
    - 1: scream (尖叫)
    - 2: night_fright (夜间惊飞)
    - 3: plucking (啄羽)
    - 4: silence (安静)
    
    Returns:
        (features, labels): features shape (n_samples, feature_dim), labels shape (n_samples,)
    """
    if feature_dim is None:
        feature_dim = get_feature_dim()
    
    samples_per_class = n_samples // 5
    features = []
    labels = []
    
    rng = np.random.RandomState(42)
    
    for class_idx in range(5):
        for _ in range(samples_per_class):
            feat = _generate_class_features(class_idx, rng, feature_dim)
            features.append(feat)
            labels.append(class_idx)
    
    return np.array(features), np.array(labels)


def _generate_class_features(class_idx: int, rng: np.random.RandomState, dim: int) -> np.ndarray:
    """为特定类别生成模拟特征"""
    base = rng.randn(dim) * 0.5
    
    if class_idx == 0:  # normal_chirp - 中等能量，中等频率
        base[0:3] += 2.0   # MFCC 1-3 较高
        base[26] += 0.3    # spectral_centroid 中等
        base[29] += 0.2    # zero_crossing_rate 中等
        base[30] += 0.1    # RMS 中等
    elif class_idx == 1:  # scream - 高能量，高频
        base[0:3] += 5.0   # MFCC 很高
        base[26] += 1.5    # spectral_centroid 高
        base[28] += 1.0    # spectral_bandwidth 高
        base[29] += 0.8    # zero_crossing_rate 高
        base[30] += 1.5    # RMS 高
        base[31] += 0.5    # RMS std 高
    elif class_idx == 2:  # night_fright - 突发高能量
        base[0:3] += 4.0
        base[26] += 1.0
        base[29] += 0.6
        base[30] += 1.2
        base[31] += 0.8
    elif class_idx == 3:  # plucking - 低能量，不规则
        base[0:3] += 0.5
        base[26] -= 0.5
        base[29] += 0.3
        base[30] -= 0.3
    elif class_idx == 4:  # silence - 极低能量
        base[0:3] -= 2.0
        base[26] -= 1.0
        base[29] -= 0.5
        base[30] -= 1.5
        base[31] -= 0.5
    
    return base


# 类别映射
CLASS_NAMES = {
    0: "normal_chirp",
    1: "scream",
    2: "night_fright",
    3: "plucking",
    4: "silence",
}

CLASS_LABELS_CN = {
    0: "正常鸣叫",
    1: "尖叫",
    2: "夜间惊飞",
    3: "啄羽",
    4: "安静",
}

# 异常类别（非正常）
ABNORMAL_CLASSES = {1, 2, 3}

# 风险等级映射
RISK_LEVEL_MAP = {
    0: None,       # normal_chirp
    1: "high",     # scream
    2: "critical", # night_fright
    3: "medium",   # plucking
    4: None,       # silence
}
