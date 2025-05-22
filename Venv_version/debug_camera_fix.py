"""
カメラ問題診断・修正スクリプト
"""
import cv2
import time
import sys
from pathlib import Path

def test_camera_basic():
    """基本的なカメラテスト"""
    print("=== カメラ基本テスト ===")
    
    # 複数のカメラIDを試行
    camera_ids = [0, 1, 2]
    working_cameras = []
    
    for camera_id in camera_ids:
        print(f"\nカメラID {camera_id} をテスト中...")
        
        try:
            # Windows用の設定
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✓ カメラID {camera_id}: 動作OK ({width}x{height})")
                    working_cameras.append(camera_id)
                    
                    # テスト画像保存
                    cv2.imwrite(f"camera_test_{camera_id}.jpg", frame)
                    print(f"  テスト画像保存: camera_test_{camera_id}.jpg")
                else:
                    print(f"✗ カメラID {camera_id}: フレーム取得失敗")
            else:
                print(f"✗ カメラID {camera_id}: 開けません")
            
            cap.release()
            
        except Exception as e:
            print(f"✗ カメラID {camera_id}: エラー - {e}")
    
    return working_cameras

def test_frame_buffer_simulation():
    """フレームバッファシミュレーションテスト"""
    print("\n=== フレームバッファテスト ===")
    
    try:
        # 実際のシステムモジュールをインポート
        from camera_module import CameraManager, FrameBuffer
        from models import CameraFrame
        
        # カメラマネージャーテスト
        camera_manager = CameraManager()
        
        print("カメラマネージャー初期化中...")
        if camera_manager.start():
            print("✓ カメラマネージャー初期化成功")
            
            # フレーム取得テスト
            print("フレーム取得テスト中...")
            for i in range(5):
                frame = camera_manager.get_frame()
                if frame:
                    print(f"✓ フレーム {i+1}: {frame.width}x{frame.height} ({frame.source})")
                    
                    # テスト画像保存
                    import cv2
                    cv2.imwrite(f"frame_test_{i+1}.jpg", frame.image)
                else:
                    print(f"✗ フレーム {i+1}: 取得失敗")
                time.sleep(1)
            
            # 現在フレーム取得テスト
            current_frame = camera_manager.get_current_frame()
            if current_frame:
                print("✓ 現在フレーム取得成功")
                cv2.imwrite("current_frame_test.jpg", current_frame.image)
            else:
                print("✗ 現在フレーム取得失敗")
            
            camera_manager.stop()
        else:
            print("✗ カメラマネージャー初期化失敗")
            
    except Exception as e:
        print(f"✗ フレームバッファテストエラー: {e}")

def create_test_images():
    """テスト画像を作成"""
    print("\n=== テスト画像作成 ===")
    
    test_images_dir = Path("data/test_images")
    test_images_dir.mkdir(parents=True, exist_ok=True)
    
    import numpy as np
    
    # サンプル画像作成
    test_scenarios = [
        {
            "filename": "test_delivery.jpg",
            "description": "配達員",
            "uniform_color": (0, 0, 200),  # 赤
            "has_package": True
        },
        {
            "filename": "test_visitor.jpg", 
            "description": "来客",
            "uniform_color": (50, 50, 50),  # グレー
            "has_package": False
        },
        {
            "filename": "test_postman.jpg",
            "description": "郵便配達",
            "uniform_color": (0, 120, 255),  # オレンジ
            "has_package": True
        }
    ]
    
    for scenario in test_scenarios:
        # 画像作成 (640x480)
        img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # 人物シルエット
        cv2.rectangle(img, (200, 100), (440, 400), scenario["uniform_color"], -1)
        
        # 顔
        cv2.circle(img, (320, 150), 50, (200, 180, 140), -1)
        
        # パッケージ
        if scenario["has_package"]:
            cv2.rectangle(img, (250, 250), (390, 300), (200, 200, 200), -1)
        
        # テキスト
        cv2.putText(img, scenario["description"], (220, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # タイムスタンプ
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 保存
        filepath = test_images_dir / scenario["filename"]
        cv2.imwrite(str(filepath), img)
        print(f"✓ 作成: {filepath}")
    
    return len(test_scenarios)

def fix_config_for_testing():
    """テスト用設定修正"""
    print("\n=== 設定ファイル修正 ===")
    
    config_fix = '''
# config.py の一部を修正 (末尾に追加)

# === デバッグ用設定追加 ===
CAMERA_RETRY_COUNT = 3
FRAME_BUFFER_DEBUG = True
FORCE_TEST_MODE = False  # Trueにするとテスト画像強制使用

# === カメラ設定修正 ===
# USE_CAMERA = False  # これを有効にするとテスト画像モード
'''
    
    print("config.pyに以下を追加することを推奨:")
    print(config_fix)
    
    # config.pyが存在するかチェック
    if Path("config.py").exists():
        print("✓ config.py が存在します")
    else:
        print("✗ config.py が見つかりません")

def create_emergency_config():
    """緊急用設定ファイル作成"""
    emergency_config = '''"""
緊急用設定ファイル - カメラ問題対応版
"""
import os
import platform
from pathlib import Path

# === システム情報 ===
PLATFORM = platform.system()
IS_WINDOWS = PLATFORM == "Windows"
IS_MACOS = PLATFORM == "Darwin"

# === ディレクトリ設定 ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CAPTURES_DIR = DATA_DIR / "captures"
TEST_IMAGES_DIR = DATA_DIR / "test_images"
LOGS_DIR = DATA_DIR / "logs"

# ディレクトリ作成
for dir_path in [DATA_DIR, CAPTURES_DIR, TEST_IMAGES_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# === カメラ設定（問題対応版） ===
USE_CAMERA = False  # まずはテスト画像で動作確認
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 2  # フレームレートを下げて安定化

# === Ollama API設定 ===
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"
REQUEST_TIMEOUT = 30

# === 人物認識設定 ===
USE_FACE_RECOGNITION = True
FACE_RECOGNITION_METHOD = "opencv_haar"
FACE_CONFIDENCE_THRESHOLD = 0.7

# === 音声設定 ===
VOICE_RATE = 150
VOICE_VOLUME = 1.0
USE_SYSTEM_TTS = True

# === システム設定 ===
DEBUG_MODE = True
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080
AUTO_SAVE_CAPTURES = True

# === プロンプト設定 ===
SYSTEM_PROMPT = """
あなたは視覚障害者や高齢者を支援するAIです。カメラに映っている人物の特徴を簡潔に説明してください。

以下の情報を含めてください：
1. 性別と推定年齢層
2. 服装の特徴（色、スタイル）
3. 持っているもの（荷物、書類など）
4. 表情や姿勢
5. 明らかな職業的特徴（制服など）
6. 制服から予想できる職業

怪しい場合は正直に伝えてください。
メガネ、持ち物、体型なども教えてください。

簡潔で分かりやすい日本語で、80文字以内で説明してください。
"""

# === Windows音声コマンド ===
TTS_COMMANDS = {
    "Windows": [
        'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\\'{text}\\')"'
    ]
}

CURRENT_TTS_COMMANDS = TTS_COMMANDS.get(PLATFORM, [])
'''
    
    with open("config_emergency.py", 'w', encoding='utf-8') as f:
        f.write(emergency_config)
    print("✓ config_emergency.py を作成しました")

def main():
    """メイン診断処理"""
    print("=" * 60)
    print(" カメラ問題診断・修正ツール")
    print("=" * 60)
    
    # Step 1: 基本カメラテスト
    working_cameras = test_camera_basic()
    
    if working_cameras:
        print(f"\n✓ 動作するカメラが見つかりました: {working_cameras}")
        recommended_id = working_cameras[0]
        print(f"推奨カメラID: {recommended_id}")
    else:
        print("\n⚠ 動作するカメラが見つかりませんでした")
        print("→ テスト画像モードを使用します")
    
    # Step 2: テスト画像作成
    image_count = create_test_images()
    print(f"\n✓ {image_count}個のテスト画像を作成しました")
    
    # Step 3: フレームバッファテスト
    test_frame_buffer_simulation()
    
    # Step 4: 設定修正提案
    fix_config_for_testing()
    
    # Step 5: 緊急用設定作成
    create_emergency_config()
    
    print("\n" + "=" * 60)
    print(" 修正提案")
    print("=" * 60)
    
    if working_cameras:
        print("🔧 カメラが動作する場合:")
        print(f"   config.py で CAMERA_ID = {working_cameras[0]} に設定")
        print("   USE_CAMERA = True のまま使用")
    else:
        print("🔧 カメラが動作しない場合:")
        print("   config.py で USE_CAMERA = False に設定")
        print("   または config_emergency.py を config.py にリネーム")
    
    print("\n📝 次のステップ:")
    print("1. 設定を修正")
    print("2. システム再起動: python main.py web")
    print("3. ブラウザで動作確認")
    
    if working_cameras:
        print("\n🎥 カメラテスト画像を確認してください:")
        for camera_id in working_cameras:
            print(f"   camera_test_{camera_id}.jpg")

if __name__ == "__main__":
    main()
