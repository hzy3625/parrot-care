# -*- coding: utf-8 -*-
"""批量音频特征提取脚本 - 用于准备训练数据

使用方法:
    python ml/training/batch_extract_features.py --input-dir ml/datasets/audio --output /tmp/training_data.csv

功能:
    1. 扫描音频文件夹（按类别子目录组织）
    2. 提取 MFCC + 频谱特征
    3. 导出 CSV 格式训练数据

数据集结构要求:
    data/raw_audio/
        normal_chirp/
            audio1.wav
            audio2.wav
        scream/
            audio1.wav
        ...
"""

import argparse
import csv
import logging
from pathlib import Path
import sys

# 从 monorepo 中加载 API 共享的音频特征实现
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from app.services.audio_features import (
        extract_audio_features,
        get_feature_dim,
        CLASS_NAMES,
        CLASS_LABELS_CN,
        HAS_LIBROSA
    )
except ImportError as e:
    logger.error(f"导入失败: {e}")
    logger.error("请确保 librosa 已安装: pip install librosa")
    sys.exit(1)

CLASS_NAME_TO_ID = {name: class_id for class_id, name in CLASS_NAMES.items()}


def scan_audio_files(input_dir: Path) -> dict:
    """扫描音频文件夹，返回按类别组织的文件列表

    Args:
        input_dir: 输入目录路径

    Returns:
        {class_name: [file_paths]}
    """
    audio_files = {}

    for class_dir in input_dir.iterdir():
        if not class_dir.is_dir():
            continue

        class_name = class_dir.name
        if class_name not in CLASS_NAMES.values():
            logger.warning(f"未知类别目录: {class_name}, 跳过")
            continue

        files = []
        for audio_file in class_dir.glob("*"):
            if audio_file.suffix.lower() in ['.wav', '.mp3', '.flac', '.ogg']:
                files.append(str(audio_file))

        if files:
            audio_files[class_name] = files
            logger.info(f"类别 '{class_name}': 找到 {len(files)} 个音频文件")

    return audio_files


def extract_batch(audio_files: dict) -> list:
    """批量提取特征

    Args:
        audio_files: {class_name: [file_paths]}

    Returns:
        [(file_path, class_name, features_list)]
    """
    results = []
    total_files = sum(len(files) for files in audio_files.values())

    processed = 0
    failed = 0

    for class_name, files in audio_files.items():
        for file_path in files:
            try:
                features = extract_audio_features(audio_path=file_path)
                results.append((file_path, class_name, features.tolist()))
                processed += 1

                if processed % 10 == 0:
                    logger.info(f"进度: {processed}/{total_files}")
            except Exception as e:
                logger.error(f"提取失败: {file_path} - {e}")
                failed += 1

    logger.info(f"完成: 处理 {processed} 个文件, 失败 {failed} 个")
    return results


def export_csv(results: list, output_path: Path, feature_dim: int):
    """导出 CSV 格式训练数据

    CSV 格式:
        file_path, class_name, class_id, feature_0, feature_1, ..., feature_{dim-1}
    """
    headers = ['file_path', 'class_name', 'class_id'] + [f'feature_{i}' for i in range(feature_dim)]

    # 类别名称 → ID
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for file_path, class_name, features in results:
            class_id = CLASS_NAME_TO_ID[class_name]
            row = [file_path, class_name, class_id] + features
            writer.writerow(row)

    logger.info(f"已导出 {len(results)} 条数据到 {output_path}")


def main():
    if not HAS_LIBROSA:
        logger.error("librosa 未安装，请运行: pip install librosa")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='批量音频特征提取')
    parser.add_argument('--input-dir', type=str, required=True, help='输入音频目录')
    parser.add_argument('--output', type=str, required=True, help='输出 CSV 文件路径')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        sys.exit(1)

    # 1. 扫描音频文件
    logger.info(f"扫描音频文件: {input_dir}")
    audio_files = scan_audio_files(input_dir)

    if not audio_files:
        logger.error("未找到任何音频文件")
        sys.exit(1)

    # 2. 批量提取特征
    logger.info("开始提取特征...")
    results = extract_batch(audio_files)

    if not results:
        logger.error("没有成功提取任何特征")
        sys.exit(1)

    # 3. 导出 CSV
    feature_dim = get_feature_dim()
    logger.info(f"特征维度: {feature_dim}")
    export_csv(results, output_path, feature_dim)

    # 4. 统计摘要
    logger.info("=" * 50)
    logger.info("数据采集摘要:")
    for class_name, files in audio_files.items():
        count = len([r for r in results if r[1] == class_name])
        logger.info(f"  {class_name} ({CLASS_LABELS_CN[CLASS_NAME_TO_ID[class_name]]}): {count} 段")
    logger.info(f"总计: {len(results)} 段")
    logger.info("=" * 50)


if __name__ == '__main__':
    main()
