# -*- coding: utf-8 -*-
"""合成训练数据生成脚本 - 用于训练基线模型（无真实数据时）

当尚未采集真实音频数据时，使用此脚本生成合成训练数据。
合成数据可用于训练基线模型，验证模型架构和训练流程。

使用方法:
    python scripts/generate_synthetic_training_data.py \
        --output data/synthetic_training_data.csv \
        --n-samples 1000

生成 CSV 格式:
    file_path, class_name, class_id, feature_0...feature_{dim-1}
"""

import argparse
import csv
import logging
import numpy as np
from pathlib import Path
import sys

# 添加 backend 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from app.services.audio_features import (
        generate_synthetic_features,
        get_feature_dim,
        CLASS_NAMES,
        CLASS_LABELS_CN,
    )
except ImportError as e:
    logger.error(f"导入失败: {e}")
    sys.exit(1)


def generate_training_csv(
    n_samples: int,
    output_path: Path,
    feature_dim: int
):
    """生成 CSV 格式合成训练数据
    
    Args:
        n_samples: 总样本数（每类 n_samples/5）
        output_path: 输出 CSV 文件路径
        feature_dim: 特征维度
    """
    logger.info(f"生成 {n_samples} 个合成样本...")
    
    features, labels = generate_synthetic_features(
        n_samples=n_samples,
        feature_dim=feature_dim
    )
    
    # CSV 头
    headers = ['file_path', 'class_name', 'class_id'] + [f'feature_{i}' for i in range(feature_dim)]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for idx, (feat, label) in enumerate(zip(features, labels)):
            class_name = CLASS_NAMES[label]
            # 虚拟文件路径
            file_path = f"synthetic/{class_name}/synthetic_{idx:04d}.wav"
            row = [file_path, class_name, label] + feat.tolist()
            writer.writerow(row)
    
    logger.info(f"已生成 {n_samples} 条合成数据到 {output_path}")
    
    # 统计摘要
    logger.info("=" * 50)
    logger.info("合成数据摘要:")
    for class_id in range(5):
        count = np.sum(labels == class_id)
        logger.info(f"  {CLASS_NAMES[class_id]} ({CLASS_LABELS_CN[class_id]}): {count} 段")
    logger.info(f"总计: {n_samples} 段")
    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='生成合成训练数据')
    parser.add_argument('--output', type=str, required=True, help='输出 CSV 文件路径')
    parser.add_argument('--n-samples', type=int, default=1000, help='总样本数（默认 1000）')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    feature_dim = get_feature_dim()
    logger.info(f"特征维度: {feature_dim}")
    
    generate_training_csv(args.n_samples, output_path, feature_dim)


if __name__ == '__main__':
    main()