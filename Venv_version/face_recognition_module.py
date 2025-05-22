"""
顔認識モジュール - 複数手法対応、プラグイン式
"""
import cv2
import numpy as np
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

import config
from models import CameraFrame, FaceDetection, PersonRecognitionResult

logger = logging.getLogger(__name__)

class FaceRecognizer(ABC):
    """顔認識の基底クラス"""
    
    @abstractmethod
    def detect_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        """顔検出を実行"""
        pass
    
    @abstractmethod
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識を実行"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """認識システムが利用可能か"""
        pass

class MediaPipeFaceRecognizer(FaceRecognizer):
    """MediaPipe による顔認識"""
    
    def __init__(self):
        self.mp_face_detection = None
        self.mp_drawing = None
        self.face_detection = None
        self._initialize()
    
    def _initialize(self):
        """MediaPipe初期化"""
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 0: 2m以内, 1: 5m以内
                min_detection_confidence=config.FACE_CONFIDENCE_THRESHOLD
            )
            logger.info("MediaPipe顔認識を初期化")
        except ImportError:
            logger.warning("MediaPipeがインストールされていません")
        except Exception as e:
            logger.error(f"MediaPipe初期化エラー: {e}")
    
    def is_available(self) -> bool:
        """利用可能性チェック"""
        return self.face_detection is not None
    
    def detect_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        """顔検出"""
        if not self.is_available():
            return []
        
        try:
            # BGR -> RGB変換
            rgb_image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_image)
            
            detections = []
            if results.detections:
                h, w = frame.height, frame.width
                
                for detection in results.detections:
                    # バウンディングボックス取得
                    bbox = detection.location_data.relative_bounding_box
                    x1 = int(bbox.xmin * w)
                    y1 = int(bbox.ymin * h)
                    x2 = int((bbox.xmin + bbox.width) * w)
                    y2 = int((bbox.ymin + bbox.height) * h)
                    
                    # 境界チェック
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    face_det = FaceDetection(
                        bbox=(x1, y1, x2, y2),
                        confidence=detection.score[0]
                    )
                    detections.append(face_det)
            
            return detections
            
        except Exception as e:
            logger.error(f"MediaPipe顔検出エラー: {e}")
            return []
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識（顔検出のみ、識別は未実装）"""
        face_detections = self.detect_faces(frame)
        
        return PersonRecognitionResult(
            is_known_person=False,  # MediaPipeだけでは識別不可
            face_detections=face_detections,
            method_used="mediapipe"
        )

class OpenCVHaarFaceRecognizer(FaceRecognizer):
    """OpenCV Haar Cascade による顔認識"""
    
    def __init__(self):
        self.face_cascade = None
        self._initialize()
    
    def _initialize(self):
        """OpenCV Haar Cascade初期化"""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("Haar Cascadeの読み込みに失敗")
                self.face_cascade = None
            else:
                logger.info("OpenCV Haar Cascade顔認識を初期化")
                
        except Exception as e:
            logger.error(f"OpenCV Haar Cascade初期化エラー: {e}")
    
    def is_available(self) -> bool:
        """利用可能性チェック"""
        return self.face_cascade is not None
    
    def detect_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        """顔検出"""
        if not self.is_available():
            return []
        
        try:
            # グレースケール変換
            gray = cv2.cvtColor(frame.image, cv2.COLOR_BGR2GRAY)
            
            # 顔検出
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            detections = []
            for (x, y, w, h) in faces:
                face_det = FaceDetection(
                    bbox=(x, y, x + w, y + h),
                    confidence=0.8  # Haar Cascadeは信頼度を返さないので固定値
                )
                detections.append(face_det)
            
            return detections
            
        except Exception as e:
            logger.error(f"OpenCV Haar顔検出エラー: {e}")
            return []
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識（顔検出のみ）"""
        face_detections = self.detect_faces(frame)
        
        return PersonRecognitionResult(
            is_known_person=False,
            face_detections=face_detections,
            method_used="opencv_haar"
        )

class NoFaceRecognizer(FaceRecognizer):
    """顔認識なし（フォールバック）"""
    
    def is_available(self) -> bool:
        return True
    
    def detect_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        return []
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        return PersonRecognitionResult(
            is_known_person=False,
            method_used="none"
        )

class FaceRecognitionManager:
    """顔認識システム管理"""
    
    def __init__(self):
        self.recognizers = {}
        self.active_recognizer = None
        self.known_faces_db = {}
        self._initialize_recognizers()
        self._load_known_faces()
    
    def _initialize_recognizers(self):
        """認識システム初期化"""
        # 利用可能な認識システムを順次試す
        recognizer_classes = [
            ("mediapipe", MediaPipeFaceRecognizer),
            ("opencv_haar", OpenCVHaarFaceRecognizer),
            ("none", NoFaceRecognizer)
        ]
        
        for name, recognizer_class in recognizer_classes:
            try:
                recognizer = recognizer_class()
                if recognizer.is_available():
                    self.recognizers[name] = recognizer
                    logger.info(f"顔認識システム '{name}' を初期化")
                    
                    # 最初に利用可能なものをアクティブに
                    if self.active_recognizer is None:
                        self.active_recognizer = recognizer
                        logger.info(f"アクティブ顔認識: {name}")
                        
            except Exception as e:
                logger.error(f"顔認識システム '{name}' 初期化エラー: {e}")
        
        # フォールバック
        if self.active_recognizer is None:
            self.active_recognizer = NoFaceRecognizer()
            logger.warning("全ての顔認識システムが利用不可、フォールバックを使用")
    
    def _load_known_faces(self):
        """既知の顔データベース読み込み"""
        try:
            db_path = config.DATA_DIR / "known_faces.json"
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    self.known_faces_db = json.load(f)
                logger.info(f"既知の顔データベース読み込み: {len(self.known_faces_db)}人")
            else:
                self.known_faces_db = {}
                logger.info("既知の顔データベースなし")
        except Exception as e:
            logger.error(f"既知の顔データベース読み込みエラー: {e}")
            self.known_faces_db = {}
    
    def save_known_faces(self):
        """既知の顔データベース保存"""
        try:
            db_path = config.DATA_DIR / "known_faces.json"
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(self.known_faces_db, f, ensure_ascii=False, indent=2)
            logger.info("既知の顔データベース保存完了")
        except Exception as e:
            logger.error(f"既知の顔データベース保存エラー: {e}")
    
    def add_known_person(self, person_id: str, name: str, face_features: Any = None):
        """既知の人物を追加"""
        self.known_faces_db[person_id] = {
            "name": name,
            "added_date": datetime.now().isoformat(),
            "features": face_features  # 将来的な特徴量保存用
        }
        self.save_known_faces()
        logger.info(f"既知の人物を追加: {person_id} - {name}")
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識実行"""
        if not config.USE_FACE_RECOGNITION or not self.active_recognizer:
            return PersonRecognitionResult(is_known_person=False, method_used="disabled")
        
        try:
            # 基本的な顔検出を実行
            result = self.active_recognizer.recognize_person(frame)
            
            # 既知の人物との照合（簡易版 - 将来的に特徴量マッチングに拡張可能）
            if result.face_detections and self.known_faces_db:
                # 現時点では顔が検出されても既知人物判定は行わない
                # 将来的にここで特徴量比較を実装
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"人物認識エラー: {e}")
            return PersonRecognitionResult(is_known_person=False, method_used="error")
    
    def get_available_methods(self) -> List[str]:
        """利用可能な認識手法リスト"""
        return list(self.recognizers.keys())
    
    def switch_method(self, method_name: str) -> bool:
        """認識手法切り替え"""
        if method_name in self.recognizers:
            self.active_recognizer = self.recognizers[method_name]
            logger.info(f"顔認識手法を切り替え: {method_name}")
            return True
        return False
    
    def draw_detections(self, frame: CameraFrame, detections: List[FaceDetection]) -> np.ndarray:
        """検出結果を画像に描画"""
        result_image = frame.image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            
            # バウンディングボックス
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 信頼度表示
            confidence_text = f"{detection.confidence:.2f}"
            cv2.putText(result_image, confidence_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 人物ID（既知の場合）
            if detection.person_id:
                person_name = self.known_faces_db.get(detection.person_id, {}).get("name", detection.person_id)
                cv2.putText(result_image, person_name, (x1, y2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        return result_image