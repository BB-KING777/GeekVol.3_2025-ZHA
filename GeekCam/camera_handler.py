"""
カメラ操作モジュール: Webカメラまたは画像ファイルからの画像取得を管理
"""
import cv2
import os
import time
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import config

class CameraHandler:
    def __init__(self):
        """カメラハンドラの初期化"""
        self.camera = None
        self.is_running = False
        self.last_capture_time = 0
        
        # テスト画像関連
        self.test_images_loaded = False
        self.test_image_frames = []
        self.current_test_image_index = 0

    def start(self):
        """カメラまたはテスト画像の初期化"""
        if config.USE_CAMERA:
            # カメラモードの場合
            try:
                self.camera = cv2.VideoCapture(config.CAMERA_ID)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                
                if not self.camera.isOpened():
                    print("カメラの起動に失敗しました。デバイスID:", config.CAMERA_ID)
                    return False
                    
                self.is_running = True
                print("カメラの起動に成功しました")
                return True
            except Exception as e:
                print(f"カメラの起動中にエラーが発生しました: {e}")
                return False
        else:
            # テスト画像モードの場合
            try:
                self._load_test_images()
                self.is_running = True
                print(f"{len(self.test_image_frames)}枚のテスト画像を読み込みました")
                return True
            except Exception as e:
                print(f"テスト画像の読み込み中にエラーが発生しました: {e}")
                return False

    def _load_test_images(self):
        """テスト用画像を読み込む"""
        self.test_image_frames = []
        
        # テスト画像ディレクトリが存在しない場合は作成
        if not os.path.exists(config.TEST_IMAGES_DIR):
            os.makedirs(config.TEST_IMAGES_DIR)
            print(f"テスト画像ディレクトリを作成しました: {config.TEST_IMAGES_DIR}")
            print("テスト画像をディレクトリに配置してください")
            
            # サンプル画像がない場合はダミー画像を作成
            if not config.TEST_IMAGES:
                dummy_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
                cv2.putText(dummy_image, "Sample Test Image", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                self.test_image_frames.append(dummy_image)
                # ダミー画像を保存
                cv2.imwrite(os.path.join(config.TEST_IMAGES_DIR, "sample.jpg"), dummy_image)
                print("サンプルテスト画像を作成しました")
            return
            
        # 指定されたテスト画像を読み込む
        for image_file in config.TEST_IMAGES:
            image_path = os.path.join(config.TEST_IMAGES_DIR, image_file)
            if os.path.exists(image_path):
                image = cv2.imread(image_path)
                if image is not None:
                    self.test_image_frames.append(image)
                    print(f"テスト画像を読み込みました: {image_file}")
                else:
                    print(f"画像の読み込みに失敗しました: {image_file}")
            else:
                print(f"画像ファイルが見つかりません: {image_file}")
                
        # テスト画像がない場合はディレクトリ内のすべての画像を読み込む
        if not self.test_image_frames:
            print("指定されたテスト画像がないため、ディレクトリ内の画像を検索します")
            for file in os.listdir(config.TEST_IMAGES_DIR):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(config.TEST_IMAGES_DIR, file)
                    image = cv2.imread(image_path)
                    if image is not None:
                        self.test_image_frames.append(image)
                        print(f"テスト画像を読み込みました: {file}")
        
        # それでもテスト画像がない場合はダミー画像を作成
        if not self.test_image_frames:
            dummy_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
            cv2.putText(dummy_image, "No Test Images Found", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            self.test_image_frames.append(dummy_image)
            # ダミー画像を保存
            cv2.imwrite(os.path.join(config.TEST_IMAGES_DIR, "dummy.jpg"), dummy_image)
            print("テスト画像が見つからないため、ダミー画像を作成しました")
        
        self.test_images_loaded = True

    def stop(self):
        """カメラの停止またはテスト画像リソースの解放"""
        if config.USE_CAMERA and self.camera and self.is_running:
            self.camera.release()
        
        self.is_running = False
        print("システムを停止しました")

    def capture_frame(self):
        """現在のフレームをキャプチャ（カメラまたはテスト画像）"""
        if not self.is_running:
            print("システムが起動していません")
            return None

        # フレームレート制限
        current_time = time.time()
        if (current_time - self.last_capture_time) < (1.0 / config.FRAME_RATE):
            return None

        self.last_capture_time = current_time
        
        if config.USE_CAMERA:
            # カメラからフレームを取得
            ret, frame = self.camera.read()
            if not ret:
                print("フレームの取得に失敗しました")
                return None
        else:
            # テスト画像から次の画像を取得
            if not self.test_image_frames:
                print("テスト画像がありません")
                return None
                
            # ローテーションで次の画像を選択
            frame = self.test_image_frames[self.current_test_image_index]
            self.current_test_image_index = (self.current_test_image_index + 1) % len(self.test_image_frames)
            print(f"テスト画像 {self.current_test_image_index}/{len(self.test_image_frames)} を使用")
        
        # デバッグモードで画像を保存
        if config.SAVE_IMAGES and config.DEBUG_MODE:
            self._save_image(frame)
            
        return frame

    def _save_image(self, frame):
        """デバッグ用に画像を保存"""
        if not os.path.exists(config.IMAGE_SAVE_DIR):
            os.makedirs(config.IMAGE_SAVE_DIR)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(config.IMAGE_SAVE_DIR, f"capture_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        print(f"画像を保存しました: {filename}")

    def get_base64_image(self, frame=None):
        """フレームをBase64エンコードした文字列を取得"""
        if frame is None:
            frame = self.capture_frame()
            
        if frame is None:
            return None
            
        # OpenCVはBGR、PILはRGBなので変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Base64エンコード
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return img_str