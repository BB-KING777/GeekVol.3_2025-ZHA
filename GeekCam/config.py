"""
システム設定ファイル
"""
import os

# LMStudio/Ollama API設定
API_BASE_URL = "http://localhost:11434/api/chat"  # Ollama用に変更
API_KEY = "dummy-key"  
MODEL_NAME = "gemma3:4b"  # 使用するOllamaモデル

# YOLO顔認識設定
YOLO_MODEL_PATH = "runs/train_yolov11/face_identifier/weights/best.pt"  # 学習済みYOLOモデルのパス
YOLO_CONFIDENCE_THRESHOLD = 0.7  # 顔認識の信頼度閾値
USE_FACE_DETECTION = True  # 顔認識機能を使用するかどうか

# 画像設定
USE_CAMERA = True  # カメラを使用するかどうか（Falseの場合は画像ファイルを使用）
CAMERA_ID = "/dev/video0"  # デフォルトカメラ（Docker環境用）
#CAMERA_ID = 0  # デフォルトカメラ
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 3  # フレームレート

# テスト用画像フォルダ設定（カメラがない場合）
TEST_IMAGES_DIR = "test_images"  # テスト用画像ファイルのディレクトリ
TEST_IMAGES = [  # テスト用画像ファイルのリスト
    "person1.jpg"
]
CURRENT_IMAGE_INDEX = 0  # 現在の画像インデックス

# 音声設定
VOICE_RATE = 150  # 音声の速度
VOICE_VOLUME = 1.0  # 音声の音量

# システム設定
DEBUG_MODE = True  # デバッグモード
SAVE_IMAGES = True  # 画像を保存するかどうか
IMAGE_SAVE_DIR = "captured_images"

# プロンプト設定
SYSTEM_PROMPT = """
あなたは視覚障害者や高齢者を支援するAIです。カメラに映っている人物の特徴を簡潔に説明してください。
以下の情報を含めてください：
1. 性別と推定年齢層
2. 服装の特徴（色、スタイル）
3. 持っているもの（荷物、書類など）
4. 表情や姿勢
5. 明らかな職業的特徴（制服など）
6. 制服から予想できる職業

怪しければ怪しいと教える必要があります。
メガネをかけている、や持っているものの特徴、体形なども教えてください。

簡潔で分かりやすい日本語で、50文字以内で説明してください。
"""

# GPU設定（Ollama用）
OLLAMA_GPU_LAYERS = -1  # -1で全レイヤーをGPUで実行
OLLAMA_GPU_MEMORY = "8192"  # GPU メモリ使用量(MB)

# Docker/システム設定
DOCKER_GPU_SUPPORT = True  # Docker環境でGPU使用するかどうか