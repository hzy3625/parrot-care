# -*- coding: utf-8 -*-
"""音频分类服务 - 集成 ML 模型 + 降级 Mock

优先使用训练好的 PyTorch 模型进行分类。
如果模型不可用或 librosa 未安装，降级为基于时间的 Mock 分类。
"""

import logging
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# 尝试导入 ML 相关模块
try:
    import numpy as np
    from app.services.audio_features import (
        extract_audio_features,
        get_feature_dim,
        CLASS_NAMES,
        ABNORMAL_CLASSES,
        RISK_LEVEL_MAP,
        HAS_LIBROSA,
    )
    from app.services.audio_model import AudioClassifierTrainer
    HAS_ML = True
except ImportError:
    HAS_ML = False
    HAS_LIBROSA = False

# 全局模型实例
_model_trainer: Optional[Any] = None
_model_loaded = False


def _get_model_trainer(model_path: Optional[str] = None) -> Optional[Any]:
    """获取或创建模型训练器（单例模式）"""
    global _model_trainer, _model_loaded

    if _model_loaded:
        return _model_trainer

    if not HAS_ML:
        logger.warning("ML 模块不可用，使用 Mock 分类")
        _model_loaded = True
        return None

    try:
        if model_path is None:
            from app.config import settings
            model_path = settings.AUDIO_MODEL_PATH

        trainer = AudioClassifierTrainer(model_path=model_path)

        if trainer.is_model_available():
            trainer.load_model()
            logger.info(f"音频分类模型已加载: {model_path}")
            _model_trainer = trainer
            _model_loaded = True
            return trainer
        else:
            logger.warning(f"模型文件不存在: {model_path}，使用 Mock 分类")
            _model_loaded = True
            return None
    except Exception as e:
        logger.error(f"加载模型失败: {e}，使用 Mock 分类")
        _model_loaded = True
        return None


def classify_audio(audio_path: str) -> Tuple[str, float, bool, Optional[str]]:
    """分类音频

    Args:
        audio_path: 音频文件路径

    Returns:
        (event_type, confidence, is_abnormal, risk_level)
    """
    trainer = _get_model_trainer()

    if trainer is not None and HAS_LIBROSA:
        try:
            # 使用 ML 模型分类
            feature_dim = get_feature_dim()
            features = extract_audio_features(audio_path=audio_path)
            predicted, probs = trainer.predict(features)

            class_idx = int(predicted[0])
            confidence = float(np.max(probs[0]))
            event_type = CLASS_NAMES.get(class_idx, "unknown")
            is_abnormal = class_idx in ABNORMAL_CLASSES
            risk_level = RISK_LEVEL_MAP.get(class_idx, None)

            logger.info(
                f"ML 分类结果: {event_type}, 置信度={confidence:.4f}, "
                f"异常={is_abnormal}, 风险={risk_level}"
            )
            return (event_type, confidence, is_abnormal, risk_level)
        except Exception as e:
            logger.error(f"ML 分类失败，降级为 Mock: {e}")

    # 降级为 Mock 分类
    return _mock_classify_audio(audio_path)


def _mock_classify_audio(audio_path: str) -> Tuple[str, float, bool, Optional[str]]:
    """Mock 音频分类（降级版本）"""
    from datetime import datetime
    hour = datetime.now().hour

    if hour >= 21 or hour < 6:
        return ("night_fright", 0.85, True, "critical")

    return ("normal_chirp", 0.90, False, None)


def generate_suggestion(event_type: str, risk_level: str) -> str:
    """生成建议"""
    suggestions = {
        "night_fright": "疑似夜惊，建议检查光线、噪声和笼布遮挡情况。",
        "scream": "高频尖叫，可能应激或求关注，观察环境变化。",
        "plucking": "啄羽行为，可能压力过大或营养不良，建议观察并咨询兽医。",
        "normal_chirp": "正常鸣叫，无需处理。",
        "silence": "安静状态，继续观察。",
    }
    return suggestions.get(event_type, "建议观察鹦鹉状态，必要时咨询兽医。")
