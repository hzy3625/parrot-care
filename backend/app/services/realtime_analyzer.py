"""
AI闊抽瀹炴椂鍒嗘瀽鏈嶅姟 - REQ-PARROT-003
瀹炵幇瀹炴椂闊抽娴佸鐞嗐€佸垎绫汇€佸紓甯告娴?
"""

import asyncio
import numpy as np
from datetime import datetime, time
from typing import Optional, Dict, List
from dataclasses import dataclass
import json

# 闊抽鍒嗙被绫诲瀷
AUDIO_TYPES = {
    'chirp': {'name': '楦熼福', 'risk': 0},
    'scream': {'name': '灏栧彨', 'risk': 1},
    'normal': {'name': '姝ｅ父', 'risk': 0},
    'night_activity': {'name': '澶滈棿寮傚父', 'risk': 2},
}

# 澶滈棿鏃堕棿鑼冨洿 (22:00 - 06:00)
NIGHT_START = time(22, 0)
NIGHT_END = time(6, 0)

@dataclass
class AudioAnalysisResult:
    """闊抽鍒嗘瀽缁撴灉"""
    audio_type: str
    classification: str
    confidence: float
    is_night: bool
    risk_level: int
    timestamp: datetime
    parrot_id: str
    event_id: Optional[str] = None

class AudioAnalyzer:
    """瀹炴椂闊抽鍒嗘瀽鍣?""
    
    def __init__(self):
        self.model_loaded = False
        self.analysis_history: List[AudioAnalysisResult] = []
    
    async def load_model(self):
        """鍔犺浇AI妯″瀷"""
        # MVP鐗堟湰浣跨敤绠€鍖栨ā鍨?
        self.model_loaded = True
        print("[AudioAnalyzer] 妯″瀷宸插姞杞?)
    
    def is_night_time(self) -> bool:
        """妫€鏌ュ綋鍓嶆槸鍚︽槸澶滈棿"""
        now = datetime.now().time()
        if now >= NIGHT_START or now <= NIGHT_END:
            return True
        return False
    
    async def analyze_audio_chunk(self, audio_data: bytes, parrot_id: str) -> AudioAnalysisResult:
        """鍒嗘瀽闊抽鐗囨"""
        if not self.model_loaded:
            await self.load_model()
        
        # 绠€鍖栧垎鏋愶細鍩轰簬闊抽鐗瑰緛妯℃嫙鍒嗙被
        # 瀹為檯搴旂敤涓簲浣跨敤鐪熷疄AI妯″瀷
        
        # 妯℃嫙鍒嗘瀽缁撴灉
        audio_type = self._simulate_classification(audio_data)
        is_night = self.is_night_time()
        
        # 澶滈棿娲诲姩鍒ゆ柇
        if is_night and audio_type != 'normal':
            audio_type = 'night_activity'
        
        risk_level = AUDIO_TYPES[audio_type]['risk']
        classification = AUDIO_TYPES[audio_type]['name']
        
        result = AudioAnalysisResult(
            audio_type=audio_type,
            classification=classification,
            confidence=0.85,  # 妯℃嫙缃俊搴?
            is_night=is_night,
            risk_level=risk_level,
            timestamp=datetime.now(),
            parrot_id=parrot_id
        )
        
        self.analysis_history.append(result)
        
        # 楂橀闄╀簨浠堕渶瑕佽褰?
        if risk_level >= 1:
            result.event_id = await self._record_event(result)
        
        return result
    
    def _simulate_classification(self, audio_data: bytes) -> str:
        """妯℃嫙闊抽鍒嗙被"""
        # MVP鐗堟湰锛氱畝鍗曟ā鎷?
        length = len(audio_data)
        
        if length < 1000:
            return 'chirp'
        elif length > 50000:
            return 'scream'
        else:
            return 'normal'
    
    async def _record_event(self, result: AudioAnalysisResult) -> str:
        """璁板綍寮傚父浜嬩欢"""
        event_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        event_data = {
            'event_id': event_id,
            'parrot_id': result.parrot_id,
            'event_type': result.classification,
            'event_time': result.timestamp.isoformat(),
            'description': f"{result.classification}锛岀疆淇″害{result.confidence:.0%}",
            'is_night': result.is_night,
            'risk_level': result.risk_level
        }
        
        # 淇濆瓨浜嬩欢鍒版枃浠讹紙瀹為檯搴旂敤涓簲淇濆瓨鍒版暟鎹簱锛?
        events_file = 'D:/autoclawworkspace/parrot-care/events.json'
        try:
            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_data) + '\n')
        except Exception as e:
            print(f"淇濆瓨浜嬩欢澶辫触: {e}")
        
        return event_id
    
    async def get_parrot_stats(self, parrot_id: str) -> Dict:
        """鑾峰彇楣﹂箟缁熻鏁版嵁"""
        parrot_results = [r for r in self.analysis_history if r.parrot_id == parrot_id]
        
        chirp_count = sum(1 for r in parrot_results if r.audio_type == 'chirp')
        scream_count = sum(1 for r in parrot_results if r.audio_type == 'scream')
        night_count = sum(1 for r in parrot_results if r.audio_type == 'night_activity')
        abnormal_count = sum(1 for r in parrot_results if r.risk_level >= 1)
        
        # 鍋ュ悍璇勫垎璁＄畻
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
        """娓呴櫎鍘嗗彶鏁版嵁"""
        self.analysis_history = [r for r in self.analysis_history if r.parrot_id != parrot_id]

# WebSocket 瀹炴椂鎺ㄩ€佹湇鍔?
class RealtimeNotifier:
    """瀹炴椂閫氱煡鏈嶅姟"""
    
    def __init__(self):
        self.connections: Dict[str, List] = {}  # parrot_id -> connections
    
    async def connect(self, parrot_id: str, websocket):
        """寤虹珛杩炴帴"""
        if parrot_id not in self.connections:
            self.connections[parrot_id] = []
        self.connections[parrot_id].append(websocket)
        print(f"[Notifier] 鏂拌繛鎺? {parrot_id}")
    
    async def disconnect(self, parrot_id: str, websocket):
        """鏂紑杩炴帴"""
        if parrot_id in self.connections:
            self.connections[parrot_id].remove(websocket)
            if not self.connections[parrot_id]:
                del self.connections[parrot_id]
    
    async def notify(self, parrot_id: str, result: AudioAnalysisResult):
        """鎺ㄩ€佸垎鏋愮粨鏋?""
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
                print(f"鎺ㄩ€佸け璐? {e}")

# 娴嬭瘯鍑芥暟
async def test_analyzer():
    """娴嬭瘯鍒嗘瀽鍣?""
    analyzer = AudioAnalyzer()
    await analyzer.load_model()
    
    # 妯℃嫙闊抽鏁版嵁
    test_audio = bytes([0] * 2000)
    parrot_id = "test_parrot_001"
    
    # 鎵ц鍒嗘瀽
    result = await analyzer.analyze_audio_chunk(test_audio, parrot_id)
    
    print(f"鍒嗘瀽缁撴灉:")
    print(f"  绫诲瀷: {result.classification}")
    print(f"  缃俊搴? {result.confidence:.0%}")
    print(f"  澶滈棿: {result.is_night}")
    print(f"  椋庨櫓: {result.risk_level}")
    
    if result.event_id:
        print(f"  浜嬩欢ID: {result.event_id}")
    
    # 鑾峰彇缁熻
    stats = await analyzer.get_parrot_stats(parrot_id)
    print(f"\n缁熻:")
    print(f"  鍋ュ悍璇勫垎: {stats['health_score']}")
    print(f"  楦ｅ彨娆℃暟: {stats['chirp_count']}")

if __name__ == "__main__":
    asyncio.run(test_analyzer())