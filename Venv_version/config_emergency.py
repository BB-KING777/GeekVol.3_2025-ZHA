"""
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
        'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
    ]
}

CURRENT_TTS_COMMANDS = TTS_COMMANDS.get(PLATFORM, [])
