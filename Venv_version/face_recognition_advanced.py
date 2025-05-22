"""
高精度顔認識システム - face_recognition ライブラリ使用
"""
import cv2
import numpy as np
import json
import logging
import pickle
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import threading

import config
from models import CameraFrame, FaceDetection, PersonRecognitionResult

logger = logging.getLogger(__name__)

class AdvancedFaceRecognizer:
    """高精度顔認識システム（face_recognition ライブラリ使用）"""
    
    def __init__(self):
        self.face_recognition = None
        self.face_encodings_db = {}  # 顔エンコーディングデータベース
        self.person_metadata = {}    # 人物メタデータ
        self.db_path = config.DATA_DIR / "face_database.db"
        self.encodings_path = config.DATA_DIR / "face_encodings.pkl"
        self.lock = threading.Lock()
        
        # 認識設定
        self.recognition_threshold = 0.6  # 低いほど厳密
        self.max_distance = 0.6
        
        self._initialize()
    
    def _initialize(self):
        """システム初期化"""
        try:
            import face_recognition
            self.face_recognition = face_recognition
            logger.info("face_recognition ライブラリを初期化")
            
            # データベース初期化
            self._init_database()
            
            # 既存のエンコーディング読み込み
            self._load_face_encodings()
            
        except ImportError:
            logger.warning("face_recognition ライブラリがインストールされていません")
            logger.info("インストール: pip install face-recognition")
        except Exception as e:
            logger.error(f"高精度顔認識初期化エラー: {e}")
    
    def _init_database(self):
        """SQLiteデータベース初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 人物テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    relationship TEXT,
                    notes TEXT,
                    created_date TEXT,
                    last_seen TEXT,
                    recognition_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # 顔画像テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    encoding_vector BLOB,
                    quality_score REAL,
                    added_date TEXT,
                    FOREIGN KEY (person_id) REFERENCES persons (person_id)
                )
            ''')
            
            # 認識履歴テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recognition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    confidence REAL,
                    image_path TEXT,
                    FOREIGN KEY (person_id) REFERENCES persons (person_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("顔認識データベース初期化完了")
            
        except Exception as e:
            logger.error(f"データベース初期化エラー: {e}")
    
    def _load_face_encodings(self):
        """保存された顔エンコーディングを読み込み"""
        try:
            if self.encodings_path.exists():
                with open(self.encodings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.face_encodings_db = data.get('encodings', {})
                    self.person_metadata = data.get('metadata', {})
                logger.info(f"顔エンコーディング読み込み完了: {len(self.face_encodings_db)}人")
            else:
                logger.info("顔エンコーディングファイルが存在しません（初回起動）")
                
        except Exception as e:
            logger.error(f"顔エンコーディング読み込みエラー: {e}")
            self.face_encodings_db = {}
            self.person_metadata = {}
    
    def _save_face_encodings(self):
        """顔エンコーディングを保存"""
        try:
            data = {
                'encodings': self.face_encodings_db,
                'metadata': self.person_metadata,
                'saved_date': datetime.now().isoformat()
            }
            
            with open(self.encodings_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info("顔エンコーディング保存完了")
            
        except Exception as e:
            logger.error(f"顔エンコーディング保存エラー: {e}")
    
    def is_available(self) -> bool:
        """利用可能性チェック"""
        return self.face_recognition is not None
    
    def register_person(self, person_id: str, name: str, image_paths: List[str], 
                       relationship: str = "", notes: str = "") -> bool:
        """新しい人物を登録"""
        if not self.is_available():
            logger.error("face_recognition ライブラリが利用できません")
            return False
        
        try:
            with self.lock:
                encodings = []
                successful_images = []
                
                # 各画像から顔エンコーディングを抽出
                for image_path in image_paths:
                    try:
                        image = self.face_recognition.load_image_file(image_path)
                        face_encodings = self.face_recognition.face_encodings(image)
                        
                        if len(face_encodings) == 1:
                            encodings.append(face_encodings[0])
                            successful_images.append(image_path)
                            logger.info(f"顔エンコーディング抽出成功: {image_path}")
                        elif len(face_encodings) == 0:
                            logger.warning(f"顔が検出されませんでした: {image_path}")
                        else:
                            logger.warning(f"複数の顔が検出されました: {image_path}")
                            
                    except Exception as e:
                        logger.error(f"画像処理エラー {image_path}: {e}")
                
                if not encodings:
                    logger.error(f"有効な顔エンコーディングが取得できませんでした: {person_id}")
                    return False
                
                # データベースに登録
                self._save_person_to_db(person_id, name, relationship, notes)
                
                # 顔エンコーディングを保存
                self.face_encodings_db[person_id] = encodings
                self.person_metadata[person_id] = {
                    'name': name,
                    'relationship': relationship,
                    'notes': notes,
                    'registered_date': datetime.now().isoformat(),
                    'image_count': len(encodings),
                    'image_paths': successful_images
                }
                
                # ファイルに保存
                self._save_face_encodings()
                
                logger.info(f"人物登録完了: {person_id} ({name}) - {len(encodings)}枚の画像")
                return True
                
        except Exception as e:
            logger.error(f"人物登録エラー: {e}")
            return False
    
    def _save_person_to_db(self, person_id: str, name: str, relationship: str, notes: str):
        """人物情報をデータベースに保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO persons 
                (person_id, name, relationship, notes, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (person_id, name, relationship, notes, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
    
    def recognize_faces(self, frame: CameraFrame) -> List[FaceDetection]:
        """フレーム内の顔を認識"""
        if not self.is_available() or not self.face_encodings_db:
            return []
        
        try:
            # OpenCV BGR から RGB に変換
            rgb_image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
            
            # 顔の位置と顔エンコーディングを取得
            face_locations = self.face_recognition.face_locations(rgb_image)
            face_encodings = self.face_recognition.face_encodings(rgb_image, face_locations)
            
            detections = []
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # 既知の顔との比較
                person_id, confidence = self._match_face(face_encoding)
                
                detection = FaceDetection(
                    bbox=(left, top, right, bottom),
                    confidence=confidence,
                    person_id=person_id
                )
                detections.append(detection)
                
                # 認識履歴を記録
                if person_id:
                    self._record_recognition(person_id, confidence)
            
            return detections
            
        except Exception as e:
            logger.error(f"顔認識エラー: {e}")
            return []
    
    def _match_face(self, face_encoding) -> Tuple[Optional[str], float]:
        """顔エンコーディングを既知の顔と照合"""
        best_match_person_id = None
        best_confidence = 0.0
        min_distance = float('inf')
        
        for person_id, known_encodings in self.face_encodings_db.items():
            # 各登録画像との距離を計算
            distances = self.face_recognition.face_distance(known_encodings, face_encoding)
            
            # 最も近い距離を取得
            min_person_distance = min(distances)
            
            if min_person_distance < min_distance and min_person_distance < self.max_distance:
                min_distance = min_person_distance
                best_match_person_id = person_id
                # 距離を信頼度に変換（0-1の範囲）
                best_confidence = max(0.0, 1.0 - min_person_distance / self.max_distance)
        
        return best_match_person_id, best_confidence
    
    def _record_recognition(self, person_id: str, confidence: float):
        """認識履歴を記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 認識履歴を追加
            cursor.execute('''
                INSERT INTO recognition_history 
                (person_id, timestamp, confidence)
                VALUES (?, ?, ?)
            ''', (person_id, datetime.now().isoformat(), confidence))
            
            # 人物の認識回数を更新
            cursor.execute('''
                UPDATE persons 
                SET recognition_count = recognition_count + 1,
                    last_seen = ?
                WHERE person_id = ?
            ''', (datetime.now().isoformat(), person_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"認識履歴記録エラー: {e}")
    
    def recognize_person(self, frame: CameraFrame) -> PersonRecognitionResult:
        """人物認識実行"""
        face_detections = self.recognize_faces(frame)
        
        # 最も信頼度の高い認識結果を選択
        best_detection = None
        for detection in face_detections:
            if detection.person_id and (best_detection is None or 
                                       detection.confidence > best_detection.confidence):
                best_detection = detection
        
        if best_detection and best_detection.confidence > self.recognition_threshold:
            return PersonRecognitionResult(
                is_known_person=True,
                person_id=best_detection.person_id,
                confidence=best_detection.confidence,
                face_detections=face_detections,
                method_used="face_recognition_advanced"
            )
        else:
            return PersonRecognitionResult(
                is_known_person=False,
                face_detections=face_detections,
                method_used="face_recognition_advanced"
            )
    
    def get_person_info(self, person_id: str) -> Optional[Dict]:
        """人物情報を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM persons WHERE person_id = ?
            ''', (person_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'person_id': result[1],
                    'name': result[2],
                    'relationship': result[3],
                    'notes': result[4],
                    'created_date': result[5],
                    'last_seen': result[6],
                    'recognition_count': result[7],
                    'is_active': result[8]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"人物情報取得エラー: {e}")
            return None
    
    def get_all_persons(self) -> List[Dict]:
        """全ての登録人物を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM persons WHERE is_active = 1
                ORDER BY recognition_count DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            persons = []
            for result in results:
                persons.append({
                    'person_id': result[1],
                    'name': result[2],
                    'relationship': result[3],
                    'notes': result[4],
                    'created_date': result[5],
                    'last_seen': result[6],
                    'recognition_count': result[7]
                })
            
            return persons
            
        except Exception as e:
            logger.error(f"人物一覧取得エラー: {e}")
            return []
    
    def delete_person(self, person_id: str) -> bool:
        """人物を削除"""
        try:
            with self.lock:
                # メモリから削除
                if person_id in self.face_encodings_db:
                    del self.face_encodings_db[person_id]
                
                if person_id in self.person_metadata:
                    del self.person_metadata[person_id]
                
                # データベースで無効化
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE persons SET is_active = 0 WHERE person_id = ?
                ''', (person_id,))
                
                conn.commit()
                conn.close()
                
                # ファイルを更新
                self._save_face_encodings()
                
                logger.info(f"人物削除完了: {person_id}")
                return True
                
        except Exception as e:
            logger.error(f"人物削除エラー: {e}")
            return False
    
    def get_recognition_stats(self) -> Dict:
        """認識統計を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 総認識回数
            cursor.execute('SELECT SUM(recognition_count) FROM persons')
            total_recognitions = cursor.fetchone()[0] or 0
            
            # 登録人数
            cursor.execute('SELECT COUNT(*) FROM persons WHERE is_active = 1')
            total_persons = cursor.fetchone()[0] or 0
            
            # 今日の認識回数
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM recognition_history 
                WHERE timestamp LIKE ?
            ''', (f"{today}%",))
            today_recognitions = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_persons': total_persons,
                'total_recognitions': total_recognitions,
                'today_recognitions': today_recognitions,
                'database_path': str(self.db_path),
                'encodings_count': len(self.face_encodings_db)
            }
            
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}
    
    def draw_detections(self, frame: CameraFrame, detections: List[FaceDetection]) -> np.ndarray:
        """検出結果を画像に描画"""
        result_image = frame.image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            
            # 枠の色を決定
            if detection.person_id:
                # 既知の人物は緑
                color = (0, 255, 0)
                person_info = self.get_person_info(detection.person_id)
                name = person_info['name'] if person_info else detection.person_id
                label = f"{name} ({detection.confidence:.2f})"
            else:
                # 未知の人物は赤
                color = (0, 0, 255)
                label = f"Unknown ({detection.confidence:.2f})"
            
            # 顔の枠
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # ラベル背景
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # ラベルテキスト
            cv2.putText(result_image, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_image