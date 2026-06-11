"""
AI音频实时分析服务 - REQ-PARROT-003
实现实时音频流处理、分类、异常检测
"""

import asyncio
import numpy as np
from datetime import datetime, time
from typing import Optional, Dict, List
from dataclasses import dataclass
import json

# 音频分类类型
AUDIO_TYPES = {
    'chirp': {'name': '鸟鸣', 'risk': 0},
    'scream': {'name': '尖叫', 'risk': 1},
    'normal': {'name': '正常', 'risk': 0},
    'night_activity': {'name': '夜间异常', 'risk': 2},
}

# 夜间时间范围 (22:00 - 06:00)
NIGHT_START = time(22, 0)
NIGHT_END = time(6, 0)

@dataclass
class AudioAnalysisResult:
    """音频分析结果"""
    audio_type: str
    classification: str
    confidence: float
    is_night: bool
    risk_level: int
    timestamp: datetime
    parrot_id: str
    event_id: Optional[str] = None

class AudioAnalyzer:
    """实时音频分析器"""
    
    def __init__(self):
        self.model_loaded = False
        self.analysis_history: List[AudioAnalysisResult] = []
    
    async def load_model(self):
        """加载AI模型"""
        # MVP版本使用简化模型
        self.model_loaded = True
        print("[AudioAnalyzer] 模型已加载")
    
    def is_night_time(self) -> bool:
        """检查当前是否是夜间"""
        now = datetime.now().time()
        if now >= NIGHT_START or now <= NIGHT_END:
            return True
        return False
    
    async def analyze_audio_chunk(self, audio_data: bytes, parrot_id: str) -> AudioAnalysisResult:
        """分析音频片段"""
        if not self.model_loaded:
            await self.load_model()
        
        # 简化分析：基于音频特征模拟分类
        # 实际应用中应使用真实AI模型
        
        # 模拟分析结果
        audio_type = self._simulate_classification(audio_data)
        is_night = self.is_night_time()
        
        # 夜间活动判断
        if is_night and audio_type != 'normal':
            audio_type = 'night_activity'
        
        risk_level = AUDIO_TYPES[audio_type]['risk']
        classification = AUDIO_TYPES[audio_type]['name']
        
        result = AudioAnalysisResult(
            audio_type=audio_type,
            classification=classification,
            confidence=0.85,  # 模拟置信度
            is_night=is_night,
            risk_level=risk_level,
            timestamp=datetime.now(),
            parrot_id=parrot_id
        )
        
        self.analysis_history.append(result)
        
        # 高风险事件需要记录
        if risk_level >= 1:
            result.event_id = await self._record_event(result)
        
        return result
    
    def _simulate_classification(self, audio_data: bytes) -> str:
        """模拟音频分类"""
        # MVP版本：简单模拟
        length = len(audio_data)
        
        if length < 1000:
            return 'chirp'
        elif length > 50000:
            return 'scream'
        else:
            return 'normal'
    
    async def _record_event(self, result: AudioAnalysisResult) -> str:
        """记录异常事件"""
        event_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        event_data = {
            'event_id': event_id,
            'parrot_id': result.parrot_id,
            'event_type': result.classification,
            'event_time': result.timestamp.isoformat(),
            'description': f"{result.classification}，置信度{result.confidence:.0%}",
            'is_night': result.is_night,
            'risk_level': result.risk_level
        }
        
        # 保存事件到文件（实际应用中应保存到数据库）
        events_file = 'D:/autoclawworkspace/parrot-care/events.json'
        try:
            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_data) + '\n')
        except Exception as e:
            print(f"保存事件失败: {e}")
        
        return event_id
    
    async def get_parrot_stats(self, parrot_id: str) -> Dict:
        """获取鹦鹉统计数据"""
        parrot_results = [r for r in self.analysis_history if r.parrot_id == parrot_id]
        
        chirp_count = sum(1 for r in parrot_results if r.audio_type == 'chirp')
        scream_count = sum(1 for r in parrot_results if r.audio_type == 'scream')
        night_count = sum(1 for r in parrot_results if r.audio_type == 'night_activity')
        abnormal_count = sum(1 for r in parrot_results if r.risk_level >= 1)
        
        # 健康评分计算
        health_score = 100 - (scream_count * 5) - (night_count * 10) - (abnormal_count * 3)
        health_score = max(0, min(100, health_score))
        
        return {
            'parrot_id': parrot_id,
            'health_score': health_score,
            'chirp_count': chirp_count,
            'scream_count': scream_count,
            'night_activity_count': night_count,
            'abnormal_event_count': abnormal_count,
            'total_analyses': len(parrot_results)
        }
    
    async def clear_history(self, parrot_id: str):
        """清除历史数据"""
        self.analysis_history = [r for r in self.analysis_history if r.parrot_id != parrot_id]

# WebSocket 实时推送服务
class RealtimeNotifier:
    """实时通知服务"""
    
    def __init__(self):
        self.connections: Dict[str, List] = {}  # parrot_id -> connections
    
    async def connect(self, parrot_id: str, websocket):
        """建立连接"""
        if parrot_id not in self.connections:
            self.connections[parrot_id] = []
        self.connections[parrot_id].append(websocket)
        print(f"[Notifier] 新连接: {parrot_id}")
    
    async def disconnect(self, parrot_id: str, websocket):
        """断开连接"""
        if parrot_id in self.connections:
            self.connections[parrot_id].remove(websocket)
            if not self.connections[parrot_id]:
                del self.connections[parrot_id]
    
    async def notify(self, parrot_id: str, result: AudioAnalysisResult):
        """推送分析结果"""
        if parrot_id not in self.connections:
            return
        
        message = {
            'type': 'audio_analysis',
            'data': {
                'audio_type': result.audio_type,
                'classification': result.classification,
                'confidence': result.confidence,
                'is_night': result.is_night,
                'risk_level': result.risk_level,
                'timestamp': result.timestamp.isoformat(),
                'event_id': result.event_id
            }
        }
        
        for ws in self.connections[parrot_id]:
            try:
                await ws.send(json.dumps(message))
            except Exception as e:
                print(f"推送失败: {e}")

# 测试函数
async def test_analyzer():
    """测试分析器"""
    analyzer = AudioAnalyzer()
    await analyzer.load_model()
    
    # 模拟音频数据
    test_audio = bytes([0] * 2000)
    parrot_id = "test_parrot_001"
    
    # 执行分析
    result = await analyzer.analyze_audio_chunk(test_audio, parrot_id)
    
    print(f"分析结果:")
    print(f"  类型: {result.classification}")
    print(f"  置信度: {result.confidence:.0%}")
    print(f"  夜间: {result.is_night}")
    print(f"  风险: {result.risk_level}")
    
    if result.event_id:
        print(f"  事件ID: {result.event_id}")
    
    # 获取统计
    stats = await analyzer.get_parrot_stats(parrot_id)
    print(f"\n统计:")
    print(f"  健康评分: {stats['health_score']}")
    print(f"  鸣叫次数: {stats['chirp_count']}")

if __name__ == "__main__":
    asyncio.run(test_analyzer())