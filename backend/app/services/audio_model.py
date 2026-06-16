# -*- coding: utf-8 -*-
"""鹦鹉音频分类模型 - PyTorch 基线模型

使用简单的 MLP（多层感知机）作为基线分类器。
输入：音频特征向量（MFCC + 频谱特征，~43维）
输出：5 类分类（正常鸣叫、尖叫、夜间惊飞、啄羽、安静）
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 设备选择
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ParrotAudioClassifier(nn.Module):
    """鹦鹉音频分类 MLP 模型
    
    结构：Input → Linear(44→128) → ReLU → Dropout → Linear(128→64) → ReLU → Dropout → Linear(64→5)
    """
    
    def __init__(self, input_dim: int = None, num_classes: int = 5, hidden_dim: int = 128):
        if input_dim is None:
            from app.services.audio_features import get_feature_dim
            input_dim = get_feature_dim()
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_classes),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)
    
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """返回类别概率"""
        logits = self.forward(x)
        return torch.softmax(logits, dim=-1)


class AudioClassifierTrainer:
    """训练器 - 负责模型训练、评估、保存/加载"""
    
    def __init__(
        self,
        input_dim: int = 43,
        num_classes: int = 5,
        learning_rate: float = 1e-3,
        model_path: Optional[str] = None
    ):
        self.model = ParrotAudioClassifier(
            input_dim=input_dim,
            num_classes=num_classes
        ).to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.model_path = model_path or "models/audio_classifier.pt"
    
    def train(
        self,
        train_features: np.ndarray,
        train_labels: np.ndarray,
        val_features: Optional[np.ndarray] = None,
        val_labels: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32,
    ) -> dict:
        """训练模型
        
        Args:
            train_features: 训练特征 (n_samples, feature_dim)
            train_labels: 训练标签 (n_samples,)
            val_features: 验证特征（可选）
            val_labels: 验证标签（可选）
            epochs: 训练轮数
            batch_size: 批次大小
        
        Returns:
            训练历史字典
        """
        # 转换为 Tensor
        X_train = torch.FloatTensor(train_features).to(device)
        y_train = torch.LongTensor(train_labels).to(device)
        
        train_dataset = TensorDataset(X_train, y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        # 验证集
        if val_features is not None and val_labels is not None:
            X_val = torch.FloatTensor(val_features).to(device)
            y_val = torch.LongTensor(val_labels).to(device)
        
        history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
        
        best_val_acc = 0.0
        
        for epoch in range(epochs):
            # 训练阶段
            self.model.train()
            epoch_loss = 0.0
            correct = 0
            total = 0
            
            for batch_X, batch_y in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item() * batch_X.size(0)
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == batch_y).sum().item()
                total += batch_y.size(0)
            
            avg_loss = epoch_loss / total
            accuracy = correct / total
            history["train_loss"].append(avg_loss)
            history["train_acc"].append(accuracy)
            
            # 验证阶段
            if val_features is not None:
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_val)
                    val_loss = self.criterion(val_outputs, y_val).item()
                    _, val_predicted = torch.max(val_outputs, 1)
                    val_correct = (val_predicted == y_val).sum().item()
                    val_acc = val_correct / len(y_val)
                
                history["val_loss"].append(val_loss)
                history["val_acc"].append(val_acc)
                
                # 保存最佳模型
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    self.save_model()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch [{epoch+1}/{epochs}] "
                        f"Train Loss: {avg_loss:.4f}, Train Acc: {accuracy:.4f} | "
                        f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
                    )
            else:
                # 没有验证集时，每轮保存
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch [{epoch+1}/{epochs}] "
                        f"Train Loss: {avg_loss:.4f}, Train Acc: {accuracy:.4f}"
                    )
                self.save_model()
        
        return history
    
    def predict(
        self,
        features: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """预测类别
        
        Args:
            features: 特征向量 (n_samples, feature_dim) 或 (feature_dim,)
        
        Returns:
            (predicted_classes, probabilities)
        """
        self.model.eval()
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        X = torch.FloatTensor(features).to(device)
        
        with torch.no_grad():
            probs = self.model.predict_proba(X)
            _, predicted = torch.max(probs, 1)
        
        return predicted.cpu().numpy(), probs.cpu().numpy()
    
    def save_model(self, path: Optional[str] = None):
        """保存模型"""
        save_path = path or self.model_path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "input_dim": self.model.network[0].in_features,
            "num_classes": self.model.network[-1].out_features,
        }, save_path)
        logger.info(f"模型已保存至 {save_path}")
    
    def load_model(self, path: Optional[str] = None):
        """加载模型"""
        load_path = path or self.model_path
        if not Path(load_path).exists():
            raise FileNotFoundError(f"模型文件不存在: {load_path}")
        
        checkpoint = torch.load(load_path, map_location=device, weights_only=True)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        logger.info(f"模型已加载自 {load_path}")
    
    def is_model_available(self, path: Optional[str] = None) -> bool:
        """检查模型文件是否存在"""
        check_path = path or self.model_path
        return Path(check_path).exists()
