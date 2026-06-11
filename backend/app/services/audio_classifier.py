"""
音频分类服务 - MVP简化版本
"""

# MVP 版本：使用简单规则判断，不依赖 librosa
# 后续版本：加载训练好的模型

def classify_audio(audio_path: str) -> tuple:
    """
    分类音频并返回结果
    
    Returns:
        (event_type, confidence, is_abnormal, risk_level)
    """
    # MVP 版本：模拟分类结果
    # 后续版本：使用 librosa + PyTorch 进行实际分析
    
    from datetime import datetime
    hour = datetime.now().hour
    
    # 夜间检测
    if hour >= 21 or hour < 6:
        return ("night_scream", 0.85, True, "high")
    
    # 白天模拟
    return ("normal_chirp", 0.90, False, None)


def generate_suggestion(event_type: str, risk_level: str) -> str:
    """生成建议"""
    suggestions = {
        "night_scream": "疑似夜惊，建议检查光线、噪声和笼布遮挡情况。",
        "high_frequency_scream": "高频尖叫，可能应激或求关注，观察环境变化。",
        "violent_flapping": "剧烈扑翅，可能受惊吓，检查周围干扰源。",
        "cage_collision": "撞笼，可能应激或空间不足，观察行为状态。",
        "normal_chirp": "正常鸣叫，无需处理。",
        "silent": "安静状态，继续观察。"
    }
    return suggestions.get(event_type, "建议观察鹦鹉状态，必要时咨询兽医。")