# -*- coding: utf-8 -*-
"""
Audio classification model tests - Sprint 2 P0-2
Tests feature extraction, model training, prediction, and classifier service.
"""

import pytest
import numpy as np
from pathlib import Path

# Skip if ML dependencies not available
librosa = pytest.importorskip("librosa", reason="librosa not installed")
torch = pytest.importorskip("torch", reason="torch not installed")

from app.services.audio_features import (
    extract_audio_features,
    get_feature_dim,
    generate_synthetic_features,
    CLASS_NAMES,
    ABNORMAL_CLASSES,
    RISK_LEVEL_MAP,
    HAS_LIBROSA,
)
from app.services.audio_model import (
    ParrotAudioClassifier,
    AudioClassifierTrainer,
)
from app.services.audio_classifier import (
    classify_audio,
    generate_suggestion,
)


# ==================== Feature Extraction Tests ====================

class TestAudioFeatures:
    """Audio feature extraction tests."""

    def test_feature_dim(self):
        """Feature dimension is consistent and reasonable."""
        dim = get_feature_dim()
        assert 40 <= dim <= 50  # Should be around 44-46
        assert dim > 30  # At least MFCC + chroma

    def test_generate_synthetic_features(self):
        """Synthetic data generation."""
        features, labels = generate_synthetic_features(n_samples=100, feature_dim=get_feature_dim())
        assert features.shape == (100, 44)
        assert labels.shape == (100,)
        assert len(set(labels)) == 5  # 5 classes

    def test_synthetic_features_has_all_classes(self):
        """Synthetic data contains all classes."""
        _, labels = generate_synthetic_features(n_samples=100)
        unique_labels = set(labels)
        assert unique_labels == {0, 1, 2, 3, 4}

    def test_class_names_complete(self):
        """Class names are complete."""
        assert len(CLASS_NAMES) == 5
        assert CLASS_NAMES[0] == "normal_chirp"
        assert CLASS_NAMES[1] == "scream"
        assert CLASS_NAMES[2] == "night_fright"

    def test_abnormal_classes(self):
        """Abnormal classes defined correctly."""
        assert 1 in ABNORMAL_CLASSES  # scream
        assert 2 in ABNORMAL_CLASSES  # night_fright
        assert 3 in ABNORMAL_CLASSES  # plucking
        assert 0 not in ABNORMAL_CLASSES  # normal_chirp
        assert 4 not in ABNORMAL_CLASSES  # silence

    def test_risk_level_map(self):
        """Risk level mapping correct."""
        assert RISK_LEVEL_MAP[2] == "critical"  # night_fright
        assert RISK_LEVEL_MAP[1] == "high"      # scream
        assert RISK_LEVEL_MAP[3] == "medium"    # plucking
        assert RISK_LEVEL_MAP[0] is None
        assert RISK_LEVEL_MAP[4] is None


# ==================== Model Tests ====================

class TestAudioModel:
    """Model training and prediction tests."""

    @pytest.fixture
    def trainer(self, tmp_path):
        """Create trainer with temp model path."""
        model_path = str(tmp_path / "test_model.pt")
        feature_dim = get_feature_dim()
        return AudioClassifierTrainer(
            input_dim=feature_dim,
            num_classes=5,
            model_path=model_path,
        )

    def test_model_creation(self, trainer):
        """Model created successfully."""
        assert trainer.model is not None

    def test_model_save_load(self, trainer, tmp_path):
        """Model save and load."""
        trainer.save_model()
        assert Path(trainer.model_path).exists()

        new_trainer = AudioClassifierTrainer(
            input_dim=get_feature_dim(),
            num_classes=5,
            model_path=trainer.model_path,
        )
        new_trainer.load_model()

        for p1, p2 in zip(
            trainer.model.parameters(), new_trainer.model.parameters()
        ):
            assert torch.allclose(p1, p2)

    def test_is_model_available(self, trainer, tmp_path):
        """Model availability check."""
        assert trainer.is_model_available() is False
        trainer.save_model()
        assert trainer.is_model_available() is True

    def test_train_and_predict(self, trainer):
        """Train then predict."""
        train_features, train_labels = generate_synthetic_features(
            n_samples=200, feature_dim=get_feature_dim()
        )
        val_features, val_labels = generate_synthetic_features(
            n_samples=50, feature_dim=get_feature_dim()
        )

        history = trainer.train(
            train_features=train_features,
            train_labels=train_labels,
            val_features=val_features,
            val_labels=val_labels,
            epochs=20,
            batch_size=32,
        )

        assert len(history["train_loss"]) == 20
        assert len(history["train_acc"]) == 20
        assert len(history["val_loss"]) == 20
        assert len(history["val_acc"]) == 20

        # Synthetic data is easy to fit
        assert history["train_acc"][-1] > 0.8

        # Predict
        predicted, probs = trainer.predict(val_features)
        assert predicted.shape == (50,)
        assert probs.shape == (50, 5)

        # Probabilities sum to 1
        for i in range(len(probs)):
            assert abs(np.sum(probs[i]) - 1.0) < 1e-5

        # Validation accuracy > 70%
        val_acc = np.mean(predicted == val_labels)
        assert val_acc > 0.7

    def test_predict_single_sample(self, trainer):
        """Single sample prediction."""
        train_features, train_labels = generate_synthetic_features(
            n_samples=100, feature_dim=get_feature_dim()
        )
        trainer.train(train_features, train_labels, epochs=10, batch_size=32)

        single_feature = train_features[0]
        predicted, probs = trainer.predict(single_feature)
        assert predicted.shape == (1,)
        assert probs.shape == (1, 5)

    def test_train_no_validation(self, trainer):
        """Train without validation set."""
        train_features, train_labels = generate_synthetic_features(
            n_samples=100, feature_dim=get_feature_dim()
        )
        history = trainer.train(
            train_features=train_features,
            train_labels=train_labels,
            epochs=5,
            batch_size=32,
        )
        assert len(history["train_loss"]) == 5
        assert len(history["val_loss"]) == 0


# ==================== Classifier Integration Tests ====================

class TestAudioClassifier:
    """Audio classifier service integration tests."""

    def test_generate_suggestion(self):
        """Suggestion generation."""
        assert "夜惊" in generate_suggestion("night_fright", "critical")
        assert "尖叫" in generate_suggestion("scream", "high")
        assert "正常" in generate_suggestion("normal_chirp", None)
        assert "啄羽" in generate_suggestion("plucking", "medium")

    def test_generate_suggestion_unknown(self):
        """Unknown type suggestion."""
        suggestion = generate_suggestion("unknown_type", None)
        assert "兽医" in suggestion

    def test_mock_classify(self):
        """Mock classify returns correct format."""
        result = classify_audio("nonexistent_file.wav")
        assert isinstance(result, tuple)
        assert len(result) == 4

        event_type, confidence, is_abnormal, risk_level = result
        assert isinstance(event_type, str)
        assert isinstance(confidence, float)
        assert isinstance(is_abnormal, bool)
        assert risk_level is None or isinstance(risk_level, str)
