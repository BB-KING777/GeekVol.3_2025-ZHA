"""
カメラ管理モジュール - 修正版（動作していたコードを基に改良）
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
    """カメラとテスト画像の統一管理 - 修正版"""
    
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
                return self._start_camera_simple()
            else:
                return self._load_test_images()
        except Exception as e:
            logger.error(f"カメラ初期化エラー: {e}")
            return False
    
    def _start_camera_simple(self) -> bool:
        """シンプルなカメラ初期化（動作していたコードを基に）"""
        try:
            # 複数の方法を順番に試行
            camera_configs = [
                # 方法1: シンプルな初期化（元のコード）
                (config.CAMERA_ID, None),
                # 方法2: DirectShow指定
                (config.CAMERA_ID, cv2.CAP_DSHOW),
                # 方法3: 別のカメラID
                (0, None),
                (1, None),
            ]
            
            for camera_id, backend in camera_configs:
                try:
                    logger.info(f"カメラテスト: ID={camera_id}, Backend={backend}")
                    
                    if backend is None:
                        self.camera = cv2.VideoCapture(camera_id)
                    else:
                        self.camera = cv2.VideoCapture(camera_id, backend)
                    
                    if not self.camera.isOpened():
                        if self.camera:
                            self.camera.release()
                        continue
                    
                    # カメラ設定（元のコードと同じ）
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                    
                    # テストフレーム取得
                    ret, frame = self.camera.read()
                    if not ret or frame is None:
                        self.camera.release()
                        continue
                    
                    self.is_running = True
                    logger.info(f"カメラ初期化成功: ID={camera_id}, Backend={backend}")
                    logger.info(f"フレームサイズ: {frame.shape[1]}x{frame.shape[0]}")
                    return True
                    
                except Exception as e:
                    logger.warning(f"カメラ設定失敗 ID={camera_id}, Backend={backend}: {e}")
                    if self.camera:
                        self.camera.release()
                        self.camera = None
                    continue
            
            logger.error("すべてのカメラ設定が失敗しました")
            return False
            
        except Exception as e:
            logger.error(f"カメラ初期化エラー: {e}")
            return False
    
    def _load_test_images(self) -> bool:
        """テスト画像読み込み（元のコードを改良）"""
        try:
            self.test_images = []
            test_dir = config.TEST_IMAGES_DIR
            
            # ディレクトリが存在しない場合は作成
            if not test_dir.exists():
                test_dir.mkdir(parents=True)
                logger.info(f"テスト画像ディレクトリを作成: {test_dir}")
            
            # 画像ファイルを探す
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            found_images = []
            
            for ext in image_extensions:
                for image_path in test_dir.glob(f"*{ext}"):
                    found_images.append(image_path)
                for image_path in test_dir.glob(f"*{ext.upper()}"):
                    found_images.append(image_path)
            
            # 画像を読み込み
            for image_path in found_images:
                try:
                    image = cv2.imread(str(image_path))
                    if image is not None:
                        self.test_images.append(image)
                        logger.info(f"テスト画像読み込み: {image_path.name}")
                except Exception as e:
                    logger.warning(f"画像読み込み失敗 {image_path.name}: {e}")
            
            # テスト画像がない場合はサンプルを作成
            if not self.test_images:
                logger.info("テスト画像が見つからないため、サンプルを作成します")
                self._create_sample_images()
                
                # 再読み込み
                for ext in image_extensions:
                    for image_path in test_dir.glob(f"*{ext}"):
                        image = cv2.imread(str(image_path))
                        if image is not None:
                            self.test_images.append(image)
            
            if self.test_images:
                self.is_running = True
                logger.info(f"{len(self.test_images)}枚のテスト画像を読み込みました")
                return True
            else:
                logger.error("テスト画像の読み込みに失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"テスト画像読み込みエラー: {e}")
            return False
    
    def _create_sample_images(self):
        """サンプル画像作成（元のコードを改良）"""
        logger.info("サンプル画像を作成中...")
        
        samples = [
            {
                "name": "test_delivery.jpg",
                "color": (0, 0, 200),  # 赤い制服
                "text": "Delivery Person",
                "has_package": True
            },
            {
                "name": "test_visitor.jpg", 
                "color": (50, 50, 50),  # 黒いスーツ
                "text": "Business Visitor",
                "has_package": False
            },
            {
                "name": "test_postman.jpg",
                "color": (0, 120, 255),  # オレンジ制服
                "text": "Postal Worker", 
                "has_package": True
            }
        ]
        
        for sample in samples:
            # キャンバス作成
            img = np.ones((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8) * 240
            
            # 人物シルエット
            cv2.rectangle(img, (200, 100), (440, 400), sample["color"], -1)
            # 顔
            cv2.circle(img, (320, 150), 50, (200, 180, 140), -1)
            # パッケージ（必要な場合）
            if sample["has_package"]:
                cv2.rectangle(img, (250, 250), (390, 300), (150, 150, 150), -1)
                cv2.putText(img, "Package", (260, 280), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # テキスト
            cv2.putText(img, sample["text"], (180, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # タイムスタンプ
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(img, f"Sample: {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 128, 0), 2)
            
            # 保存
            save_path = config.TEST_IMAGES_DIR / sample["name"]
            cv2.imwrite(str(save_path), img)
            logger.info(f"サンプル画像作成: {sample['name']}")
    
    def get_frame(self) -> Optional[CameraFrame]:
        """現在のフレームを取得（元のコードの動作を維持）"""
        if not self.is_running:
            return None
        
        # フレームレート制限
        current_time = time.time()
        if (current_time - self.last_frame_time) < (1.0 / config.FRAME_RATE):
            return None
        
        self.last_frame_time = current_time
        
        try:
            if config.USE_CAMERA:
                # カメラからフレーム取得
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    logger.error("カメラフレーム取得失敗")
                    return None
                source = "camera"
            else:
                # テスト画像からフレーム取得
                if not self.test_images:
                    return None
                frame = self.test_images[self.current_test_index].copy()
                self.current_test_index = (self.current_test_index + 1) % len(self.test_images)
                source = "test_image"
                logger.debug(f"テスト画像 {self.current_test_index}/{len(self.test_images)} を使用")
            
            # タイムスタンプ追加（元のコードと同じ）
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp_str, (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
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