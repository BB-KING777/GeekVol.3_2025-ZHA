"""
YOLO顔認識モジュール: 知っている人かどうかを判定
"""
import cv2
import numpy as np
from ultralytics import YOLO
import os
try:
    import config
except ImportError:
    # configファイルがない場合のデフォルト設定
    class Config:
        YOLO_MODEL_PATH = "runs/train_yolov11/face_identifier/weights/best.pt"
        YOLO_CONFIDENCE_THRESHOLD = 0.7
        DEBUG_MODE = True
    config = Config()

class FaceDetector:
    def __init__(self):
        """YOLO顔認識の初期化"""
        self.model = None
        self.class_names = {}
        self.model_path = config.YOLO_MODEL_PATH
        self.confidence_threshold = config.YOLO_CONFIDENCE_THRESHOLD
        self.load_model()
        
    def load_model(self):
        """YOLOモデルの読み込み"""
        try:
            if os.path.exists(self.model_path):
                print(f"YOLOモデルを読み込み中: {self.model_path}")
                self.model = YOLO(self.model_path)
                self.class_names = self.model.names
                print(f"登録済みユーザー: {self.class_names}")
                print("YOLO顔認識モジュールの初期化が完了しました")
            else:
                print(f"YOLOモデルが見つかりません: {self.model_path}")
                print("顔認識機能は無効化されます")
                self.model = None
        except Exception as e:
            print(f"YOLOモデルの読み込みに失敗しました: {e}")
            self.model = None
    
    def detect_known_faces(self, frame):
        """
        フレームから既知の顔を検出
        
        Returns:
            dict: {
                'known_faces': [{'name': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}],
                'has_known_faces': bool,
                'detection_frame': frame with annotations
            }
        """
        result = {
            'known_faces': [],
            'has_known_faces': False,
            'detection_frame': frame.copy()
        }
        
        if self.model is None:
            return result
            
        try:
            # YOLO推論実行
            results = self.model(frame, verbose=False)[0]
            
            if len(results.boxes) == 0:
                return result
            
            # 検出された顔を処理
            for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
                confidence = float(conf)
                
                if confidence < self.confidence_threshold:
                    continue
                    
                # バウンディングボックス
                x1, y1, x2, y2 = map(int, box.tolist())
                
                # クラス名（ユーザー名）を取得
                class_id = int(cls.item())
                user_name = self.class_names.get(class_id, f"unknown_{class_id}")
                
                face_info = {
                    'name': user_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                }
                
                result['known_faces'].append(face_info)
                
                # 検出結果を画像に描画
                color = (0, 255, 0)  # 緑色で既知の顔
                cv2.rectangle(result['detection_frame'], (x1, y1), (x2, y2), color, 2)
                
                # ラベル描画
                label = f"{user_name} ({confidence:.2f})"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(result['detection_frame'], 
                            (x1, y1 - label_size[1] - 10), 
                            (x1 + label_size[0], y1), 
                            color, -1)
                cv2.putText(result['detection_frame'], label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            result['has_known_faces'] = len(result['known_faces']) > 0
            
            if config.DEBUG_MODE:
                print(f"YOLO検出結果: {len(result['known_faces'])}人の既知の顔を検出")
                for face in result['known_faces']:
                    print(f"  - {face['name']}: {face['confidence']:.3f}")
                    
        except Exception as e:
            print(f"YOLO顔検出でエラーが発生しました: {e}")
            
        return result
    
    def is_model_available(self):
        """モデルが利用可能かどうか"""
        return self.model is not None
    
    def get_known_users(self):
        """登録済みユーザーのリストを取得"""
        if self.model is None:
            return []
        return list(self.class_names.values())