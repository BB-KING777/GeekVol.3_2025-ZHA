"""
データモデル - モジュール間のデータ交換用
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
import datetime
import numpy as np

@dataclass
class CameraFrame:
    """カメラフレームデータ"""
    image: np.ndarray
    timestamp: datetime.datetime
    width: int
    height: int
    source: str  # "camera" or "test_image"
    
    def copy(self):
        """フレームのコピーを作成"""
        return CameraFrame(
            image=self.image.copy(),
            timestamp=self.timestamp,
            width=self.width,
            height=self.height,
            source=self.source
        )

@dataclass
class FaceDetection:
    """顔検出結果"""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    person_id: Optional[str] = None  # 既知の人物の場合
    landmarks: Optional[List[Tuple[int, int]]] = None

@dataclass
class PersonRecognitionResult:
    """人物認識結果"""
    is_known_person: bool
    person_id: Optional[str] = None
    confidence: float = 0.0
    face_detections: List[FaceDetection] = None
    method_used: str = "none"  # 使用した認識手法
    
    def __post_init__(self):
        if self.face_detections is None:
            self.face_detections = []

@dataclass
class AnalysisResult:
    """総合分析結果"""
    timestamp: datetime.datetime
    frame: CameraFrame
    person_recognition: PersonRecognitionResult
    ai_description: str
    processing_time: float
    
    def get_message(self) -> str:
        """ユーザー向けメッセージを生成"""
        if self.person_recognition.is_known_person:
            return f"{self.person_recognition.person_id}さんがいらっしゃいました。"
        else:
            return f"未知の訪問者です。{self.ai_description}"

@dataclass
class SystemStatus:
    """システム状態"""
    is_running: bool = False
    is_processing: bool = False
    camera_active: bool = False
    last_error: Optional[str] = None
    frame_count: int = 0
    last_analysis: Optional[datetime.datetime] = None

@dataclass
class AudioRequest:
    """音声出力リクエスト"""
    text: str
    priority: int = 1  # 1=高, 2=中, 3=低
    method: str = "system"  # "system", "pyttsx3"
    
@dataclass
class APIResponse:
    """API応答データ"""
    success: bool
    content: str = ""
    error_message: str = ""
    response_time: float = 0.0
    model_used: str = ""