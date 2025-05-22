"""
カメラ管理モジュール - プラットフォーム非依存
"""
import cv2
import time
import threading
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

import config
from models import CameraFrame

logger = logging.getLogger(__name__)

class CameraManager:
    """カメラとテスト画像の統一管理"""
    
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.test_images = []
        self.current_test_index = 0
        self.last_frame_time = 0
        self.frame_lock = threading.Lock()
        self.current_frame = None
        
    def start(self) -> bool:
        """カメラまたはテスト画像の初期化"""
        try:
            if config.USE_CAMERA:
                return self._start_camera()
            else:
                return self._load_test_images()
        except Exception as e:
            logger.error(f"カメラ初期化エラー: {e}")
            return False
    
    def _start_camera(self) -> bool:
        """カメラ初期化"""
        try:
            # プラットフォーム別のカメラ設定
            if config.IS_WINDOWS:
                self.camera = cv2.VideoCapture(config.CAMERA_ID, cv2.CAP_DSHOW)
            else:
                self.camera = cv2.VideoCapture(config.CAMERA_ID)
            
            if not self.camera.isOpened():
                logger.error(f"カメラ {config.CAMERA_ID} を開けませんでした")
                return False
            
            # カメラ設定
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # テストフレーム取得
            ret, frame = self.camera.read()
            if not ret:
                logger.error("テストフレームの取得に失敗")
                return False
            
            self.is_running = True
            logger.info("カメラ初期化成功")
            return True
            
        except Exception as e:
            logger.error(f"カメラ初期化エラー: {e}")
            return False
    
    def _load_test_images(self) -> bool:
        """テスト画像読み込み"""
        try:
            self.test_images = []
            test_dir = config.TEST_IMAGES_DIR
            
            # 画像ファイルを探す
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            for ext in image_extensions:
                for image_path in test_dir.glob(f"*{ext}"):
                    image = cv2.imread(str(image_path))
                    if image is not None:
                        self.test_images.append(image)
                        logger.info(f"テスト画像読み込み: {image_path.name}")
            
            # テスト画像がない場合は作成
            if not self.test_images:
                self._create_sample_images()
                # 再読み込み
                for ext in image_extensions:
                    for image_path in test_dir.glob(f"*{ext}"):
                        image = cv2.imread(str(image_path))
                        if image is not None:
                            self.test_images.append(image)
            
            if self.test_images:
                self.is_running = True
                logger.info(f"{len(self.test_images)}枚のテスト画像を読み込み")
                return True
            else:
                logger.error("テスト画像が見つかりません")
                return False
                
        except Exception as e:
            logger.error(f"テスト画像読み込みエラー: {e}")
            return False
    
    def _create_sample_images(self):
        """サンプル画像作成"""
        logger.info("サンプル画像を作成中...")
        
        samples = [
            {
                "name": "delivery_person.jpg",
                "color": (0, 0, 200),  # 赤い制服
                "text": "Delivery Person",
                "has_package": True
            },
            {
                "name": "business_person.jpg", 
                "color": (50, 50, 50),  # 黒いスーツ
                "text": "Business Person",
                "has_package": False
            },
            {
                "name": "postal_worker.jpg",
                "color": (0, 120, 255),  # オレンジ制服
                "text": "Postal Worker", 
                "has_package": True
            }
        ]
        
        for sample in samples:
            img = np.ones((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8) * 255
            
            # 人物シルエット
            cv2.rectangle(img, (200, 100), (440, 400), sample["color"], -1)
            # 顔
            cv2.circle(img, (320, 150), 50, (200, 180, 140), -1)
            # パッケージ（必要な場合）
            if sample["has_package"]:
                cv2.rectangle(img, (250, 250), (390, 300), (200, 200, 200), -1)
            
            # テキスト
            cv2.putText(img, sample["text"], (220, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # 保存
            save_path = config.TEST_IMAGES_DIR / sample["name"]
            cv2.imwrite(str(save_path), img)
        
        logger.info("サンプル画像作成完了")
    
    def get_frame(self) -> Optional[CameraFrame]:
        """現在のフレームを取得"""
        if not self.is_running:
            return None
        
        # フレームレート制限
        current_time = time.time()
        if (current_time - self.last_frame_time) < (1.0 / config.FRAME_RATE):
            return None
        
        self.last_frame_time = current_time
        
        try:
            if config.USE_CAMERA:
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("カメラフレーム取得失敗")
                    return None
                source = "camera"
            else:
                if not self.test_images:
                    return None
                frame = self.test_images[self.current_test_index].copy()
                self.current_test_index = (self.current_test_index + 1) % len(self.test_images)
                source = "test_image"
            
            # タイムスタンプ追加
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp_str, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # CameraFrameオブジェクト作成
            camera_frame = CameraFrame(
                image=frame,
                timestamp=datetime.now(),
                width=frame.shape[1],
                height=frame.shape[0],
                source=source
            )
            
            # 現在フレーム更新
            with self.frame_lock:
                self.current_frame = camera_frame
            
            return camera_frame
            
        except Exception as e:
            logger.error(f"フレーム取得エラー: {e}")
            return None
    
    def get_current_frame(self) -> Optional[CameraFrame]:
        """最新フレームを取得（スレッドセーフ）"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame else None
    
    def stop(self):
        """カメラ停止"""
        self.is_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        logger.info("カメラ停止")

class FrameBuffer:
    """フレームバッファ管理"""
    
    def __init__(self, max_frames: int = 30):
        self.max_frames = max_frames
        self.frames = []
        self.lock = threading.Lock()
    
    def add_frame(self, frame: CameraFrame):
        """フレーム追加"""
        with self.lock:
            self.frames.append(frame)
            
            # 古いフレームを削除
            while len(self.frames) > self.max_frames:
                self.frames.pop(0)
    
    def get_latest_frame(self) -> Optional[CameraFrame]:
        """最新フレーム取得"""
        with self.lock:
            return self.frames[-1].copy() if self.frames else None
    
    def get_frame_by_offset(self, seconds_offset: float) -> Optional[CameraFrame]:
        """指定秒数オフセットのフレーム取得"""
        with self.lock:
            if not self.frames:
                return None
            
            target_time = datetime.now().timestamp() + seconds_offset
            best_frame = None
            min_diff = float('inf')
            
            for frame in self.frames:
                frame_time = frame.timestamp.timestamp()
                diff = abs(frame_time - target_time)
                if diff < min_diff:
                    min_diff = diff
                    best_frame = frame
            
            return best_frame.copy() if best_frame else None