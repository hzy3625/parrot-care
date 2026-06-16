# -*- coding: utf-8 -*-
"""Train script for ParrotCare audio classification baseline model.

Usage:
    python train_model.py [--epochs 50] [--batch-size 32] [--model-path models/audio_classifier.pt]

Default: trains on synthetic data. Replace generate_synthetic_features with real data loader when available.
"""

import argparse
import logging
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.audio_features import (
    generate_synthetic_features,
    get_feature_dim,
    CLASS_NAMES,
    CLASS_LABELS_CN,
)
from app.services.audio_model import AudioClassifierTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def train_baseline_model(
    epochs: int = 50,
    batch_size: int = 32,
    model_path: str = "models/audio_classifier.pt",
    n_train: int = 800,
    n_val: int = 200,
):
    """Train baseline model."""
    feature_dim = get_feature_dim()
    logger.info(f"Feature dim: {feature_dim}")
    logger.info(f"Num classes: {len(CLASS_NAMES)}")
    logger.info(f"Classes: {CLASS_LABELS_CN}")

    # Generate synthetic training data
    logger.info(f"Generating {n_train} training samples...")
    train_features, train_labels = generate_synthetic_features(
        n_samples=n_train, feature_dim=feature_dim
    )

    # Generate validation data
    logger.info(f"Generating {n_val} validation samples...")
    val_features, val_labels = generate_synthetic_features(
        n_samples=n_val, feature_dim=feature_dim
    )

    # Create trainer
    trainer = AudioClassifierTrainer(
        input_dim=feature_dim,
        num_classes=len(CLASS_NAMES),
        model_path=model_path,
    )

    # Train
    logger.info(f"Starting training (epochs={epochs}, batch_size={batch_size})...")
    history = trainer.train(
        train_features=train_features,
        train_labels=train_labels,
        val_features=val_features,
        val_labels=val_labels,
        epochs=epochs,
        batch_size=batch_size,
    )

    # Output final results
    final_train_acc = history["train_acc"][-1]
    final_val_acc = history["val_acc"][-1] if history["val_acc"] else "N/A"
    logger.info(
        f"Training complete! Final train acc: {final_train_acc:.4f}, "
        f"Val acc: {final_val_acc}"
    )

    # Test inference
    logger.info("Testing inference...")
    # Use different seed for test data by adding offset
    test_features = train_features[:50] + 0.01  # slight perturbation
    test_labels = train_labels[:50]
    predicted, probs = trainer.predict(test_features)
    test_acc = np.mean(predicted == test_labels)
    logger.info(f"Test accuracy: {test_acc:.4f}")

    # Show prediction examples
    for i in range(min(5, len(test_features))):
        class_name = CLASS_NAMES.get(predicted[i], "unknown")
        confidence = np.max(probs[i])
        true_label = CLASS_LABELS_CN.get(test_labels[i], "?")
        logger.info(
            f"  Sample {i}: predicted={class_name} ({CLASS_LABELS_CN.get(predicted[i], '?')}), "
            f"true={true_label}, confidence={confidence:.4f}"
        )

    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train parrot audio classification model")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--model-path", type=str, default="models/audio_classifier.pt", help="Model save path")
    parser.add_argument("--n-train", type=int, default=800, help="Training samples")
    parser.add_argument("--n-val", type=int, default=200, help="Validation samples")

    args = parser.parse_args()

    train_baseline_model(
        epochs=args.epochs,
        batch_size=args.batch_size,
        model_path=args.model_path,
        n_train=args.n_train,
        n_val=args.n_val,
    )
