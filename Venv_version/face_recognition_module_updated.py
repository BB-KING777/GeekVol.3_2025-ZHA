"""
顔認識モジュール - 高精度顔認識統合版
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

class AdvancedFaceRecognizer(FaceRecognizer):
    """高精度顔認識（face_recognition ライブラリ使用）"""
    
    def __init__(self):
        try:
            from face_recognition_advanced import AdvancedFaceRecognizer as AdvancedRecognizer
            self.recognizer = AdvancedRecognizer()
            logger.info("高精度顔認識システムを初期化")
        except ImportError:
            logger.warning("face_recognition ライブラリがインストールされていません")
            self.recognizer = None
        except Exception as e:
            logger.error(f"高精度顔認識初期化エラー: {e}")
            self.recognizer = None
    
    def is_available(self) -> bool:
        """利用可能性チェック"""
        return self.recognizer is not None and self.recognizer.is_available()
    
    def detect_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        """顔検出"""
        if not self.is_available():
            return []
        
        try:
            return self.recognizer.recognize_faces(frame)
        except Exception as e:
            logger.error(f"高精度顔検出エラー: {e}")
            return []
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識"""
        if not self.is_available():
            return PersonRecognitionResult(
                is_known_person=False,
                method_used="advanced_unavailable"
            )
        
        try:
            result = self.recognizer.recognize_person(frame)
            
            # 既知の人物が見つかった場合、詳細情報を取得
            if result.is_known_person:
                person_info = self.recognizer.get_person_info(result.person_id)
                if person_info:
                    # 認識メッセージをカスタマイズ
                    result.custom_message = self._create_welcome_message(person_info)
            
            return result
            
        except Exception as e:
            logger.error(f"高精度人物認識エラー: {e}")
            return PersonRecognitionResult(
                is_known_person=False,
                method_used="advanced_error"
            )
    
    def _create_welcome_message(self, person_info: Dict) -> str:
        """個人に合わせた歓迎メッセージを作成"""
        name = person_info['name']
        relationship = person_info.get('relationship', '')
        notes = person_info.get('notes', '')
        recognition_count = person_info.get('recognition_count', 0)
        
        if relationship == '家族':
            if recognition_count == 1:
                return f"{name}さん、おかえりなさい！初回認識です。"
            else:
                return f"{name}さん、おかえりなさい！"
        
        elif relationship == '配達員':
            return f"{name}さん、いつもありがとうございます。荷物の配達ですね。"
        
        elif relationship == '郵便局員':
            return f"{name}さん、いつもお疲れ様です。郵便物をありがとうございます。"
        
        elif relationship == '友人':
            return f"{name}さん、いらっしゃいませ！お元気でしたか？"
        
        else:
            return f"{name}さん、いらっしゃいませ。"
    
    def get_registered_persons(self) -> List[Dict]:
        """登録済み人物一覧を取得"""
        if not self.is_available():
            return []
        
        return self.recognizer.get_all_persons()
    
    def get_recognition_stats(self) -> Dict:
        """認識統計を取得"""
        if not self.is_available():
            return {}
        
        return self.recognizer.get_recognition_stats()

class MediaPipeFaceRecognizer(FaceRecognizer):
    """MediaPipe による顔認識（既存）"""
    
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
                model_selection=1,
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
        """人物認識（顔検出のみ）"""
        face_detections = self.detect_faces(frame)
        
        return PersonRecognitionResult(
            is_known_person=False,
            face_detections=face_detections,
            method_used="mediapipe"
        )

class OpenCVHaarFaceRecognizer(FaceRecognizer):
    """OpenCV Haar Cascade による顔認識（既存）"""
    
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
                    confidence=0.8
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
    """顔認識システム管理（統合版）"""
    
    def __init__(self):
        self.recognizers = {}
        self.active_recognizer = None
        self.known_faces_db = {}
        self._initialize_recognizers()
        self._load_known_faces()
    
    def _initialize_recognizers(self):
        """認識システム初期化"""
        # 高精度顔認識を最優先に設定
        recognizer_classes = [
            ("advanced", AdvancedFaceRecognizer),      # 最優先
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
                    
                    # 高精度顔認識が利用可能な場合は優先的に使用
                    if name == "advanced" and recognizer.is_available():
                        self.active_recognizer = recognizer
                        logger.info(f"高精度顔認識をアクティブに設定")
                        break
                    
                    # 最初に利用可能なものをアクティブに（高精度が使えない場合）
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
        """既知の顔データベース読み込み（下位互換性）"""
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
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識実行"""
        if not config.USE_FACE_RECOGNITION or not self.active_recognizer:
            return PersonRecognitionResult(is_known_person=False, method_used="disabled")
        
        try:
            # アクティブな認識システムで実行
            result = self.active_recognizer.recognize_person(frame)
            
            # 高精度顔認識で既知の人物が見つかった場合、カスタムメッセージを設定
            if (result.is_known_person and 
                hasattr(self.active_recognizer, '_create_welcome_message') and
                hasattr(result, 'custom_message')):
                
                # カスタムメッセージが設定されている場合はそれを使用
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
    
    def get_current_method(self) -> str:
        """現在の認識手法を取得"""
        for name, recognizer in self.recognizers.items():
            if recognizer == self.active_recognizer:
                return name
        return "unknown"
    
    def is_advanced_available(self) -> bool:
        """高精度顔認識が利用可能か"""
        return "advanced" in self.recognizers
    
    def get_registered_persons(self) -> List[Dict]:
        """登録済み人物一覧を取得"""
        if self.is_advanced_available():
            return self.recognizers["advanced"].get_registered_persons()
        return []
    
    def get_recognition_stats(self) -> Dict:
        """認識統計を取得"""
        if self.is_advanced_available():
            return self.recognizers["advanced"].get_recognition_stats()
        return {}
    
    def draw_detections(self, frame: CameraFrame, detections: List[FaceDetection]) -> np.ndarray:
        """検出結果を画像に描画"""
        result_image = frame.image.copy()
        
        # 高精度顔認識が利用可能な場合は専用の描画メソッドを使用
        if (self.is_advanced_available() and 
            hasattr(self.recognizers["advanced"], 'recognizer') and
            self.recognizers["advanced"].recognizer):
            try:
                return self.recognizers["advanced"].recognizer.draw_detections(frame, detections)
            except:
                pass
        
        # フォールバック描画
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            
            # バウンディングボックス
            color = (0, 255, 0) if detection.person_id else (0, 0, 255)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 信頼度表示
            confidence_text = f"{detection.confidence:.2f}"
            cv2.putText(result_image, confidence_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 人物名（既知の場合）
            if detection.person_id:
                cv2.putText(result_image, detection.person_id, (x1, y2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        return result_image