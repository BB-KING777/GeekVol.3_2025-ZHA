"""
高精度顔認識対応設定ファイル
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
REGISTRATION_PHOTOS_DIR = DATA_DIR / "registration_photos"

# ディレクトリ作成
for dir_path in [DATA_DIR, CAPTURES_DIR, TEST_IMAGES_DIR, LOGS_DIR, REGISTRATION_PHOTOS_DIR]:
    dir_path.mkdir(exist_ok=True)

# === カメラ設定 ===
USE_CAMERA = True  # False: テスト画像を使用
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 3

# === Ollama API設定 ===
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"
REQUEST_TIMEOUT = 300

# === 高精度顔認識設定 ===
USE_FACE_RECOGNITION = True
FACE_RECOGNITION_METHOD = "advanced"  # "advanced", "mediapipe", "opencv_haar", "none"
FACE_CONFIDENCE_THRESHOLD = 0.7  # 高精度顔認識の信頼度閾値（低いほど厳密）

# 高精度顔認識の詳細設定
ADVANCED_FACE_RECOGNITION = {
    "recognition_threshold": 0.7,  # 既知の人物として認識する最低信頼度
    "max_distance": 0.6,           # 顔の距離の最大値
    "min_face_size": 30,           # 検出する顔の最小サイズ（ピクセル）
    "max_faces_per_image": 10,     # 1つの画像で処理する最大顔数
    "auto_save_unknown": True,     # 未知の人物の画像を自動保存
    "enable_recognition_history": True,  # 認識履歴の記録
    "face_quality_threshold": 0.5, # 顔画像品質の最低閾値
}

# === 音声設定 ===
VOICE_RATE = 150
VOICE_VOLUME = 1.0
USE_SYSTEM_TTS = True

# === システム設定 ===
DEBUG_MODE = True
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080
AUTO_SAVE_CAPTURES = True

# === 訪問者対応設定 ===
VISITOR_RESPONSE_SETTINGS = {
    # 既知の人物への対応
    "known_person_fast_response": True,  # 既知の人物には即座に応答（Ollama不使用）
    "known_person_custom_messages": True,  # 関係性に応じたカスタムメッセージ
    
    # 未知の人物への対応
    "unknown_person_use_ai": True,  # 未知の人物にのみAI分析を使用
    "unknown_person_save_image": True,  # 未知の人物の画像を保存
    
    # 応答時間設定
    "max_known_person_response_time": 10,   # 既知の人物への最大応答時間（秒）
    "max_unknown_person_response_time": 300, # 未知の人物への最大応答時間（秒）
}

# === 関係性別メッセージテンプレート ===
RELATIONSHIP_MESSAGES = {
    "家族": {
        "welcome": "{name}さんです。帰ってきました！",
        "first_time": "{name}さん、初めまして初回認識です。",
        "additional": "おかえりなさい"
    },
    "配達員": {
        "welcome": "配達員の{name}さんです。配達員が来ました。",
        "first_time": "配達員の{name}さんです。初めての配達員です。",
        "additional": "荷物を受け取ってください。"
    },
    "郵便局員": {
        "welcome": "郵便配達の{name}さんがいらっしゃいました。",
        "first_time": "{name}さん、はじめまして。",
        "additional": "郵便物を受け取ってください。"
    },
    "友人": {
        "welcome": "友人の{name}さん、がお越しになりました。",
        "first_time": "{name}さん、はじめまして。",
        "additional": "友人の訪問です。"
    },
    "その他": {
        "welcome": "{name}さん、いらっしゃいませ。",
        "first_time": "{name}さん、はじめまして。",
        "additional": ""
    }
}

# === プロンプト設定 ===
SYSTEM_PROMPT = """
あなたは視覚障害者や高齢者を支援するAIです。カメラに映っている人物の特徴を簡潔に説明してください。

注意: この分析は「未知の訪問者」に対してのみ実行されます。既知の人物は高精度顔認識で即座に識別されます。

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

# === 音声コマンド設定（OS別） ===
TTS_COMMANDS = {
    "Windows": [
        'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
    ],
    "Darwin": [  # macOS
        'say "{text}"'
    ],
    "Linux": [
        'espeak -v ja "{text}"',
        'festival --tts "{text}"'
    ]
}

CURRENT_TTS_COMMANDS = TTS_COMMANDS.get(PLATFORM, [])

# === データベース設定 ===
DATABASE_SETTINGS = {
    "face_database_path": DATA_DIR / "face_database.db",
    "face_encodings_path": DATA_DIR / "face_encodings.pkl",
    "backup_interval_hours": 24,  # データベースのバックアップ間隔
    "cleanup_old_history_days": 90,  # 古い認識履歴の削除期間
    "max_recognition_history": 10000,  # 最大認識履歴数
}

# === パフォーマンス設定 ===
PERFORMANCE_SETTINGS = {
    "face_detection_interval": 0.1,  # 顔検出の実行間隔（秒）
    "frame_buffer_size": 30,         # フレームバッファサイズ
    "max_concurrent_recognitions": 1, # 同時実行する認識処理数
    "image_resize_for_analysis": True, # 分析用の画像リサイズ
    "analysis_image_width": 640,      # 分析用画像の幅
    "analysis_image_height": 480,     # 分析用画像の高さ
}

# === セキュリティ設定 ===
SECURITY_SETTINGS = {
    "save_unknown_faces": True,       # 未知の顔画像を保存
    "anonymize_saved_images": False,  # 保存画像の匿名化
    "encrypt_face_database": False,   # 顔データベースの暗号化
    "require_confirmation_for_delete": True,  # 削除時の確認
    "max_failed_recognitions": 5,     # 認識失敗の最大回数
}

# === ログ設定 ===
LOGGING_SETTINGS = {
    "log_level": "INFO",
    "log_to_file": True,
    "log_file_path": LOGS_DIR / "advanced_face_recognition.log",
    "max_log_file_size": 10 * 1024 * 1024,  # 10MB
    "log_backup_count": 5,
    "log_recognition_events": True,
    "log_system_performance": True,
}

# === Webインターフェース設定 ===
WEB_INTERFACE_SETTINGS = {
    "show_confidence_scores": True,     # 信頼度スコアの表示
    "show_recognition_history": True,   # 認識履歴の表示
    "enable_person_management": True,   # 人物管理機能
    "show_system_statistics": True,     # システム統計の表示
    "enable_real_time_preview": True,   # リアルタイムプレビュー
    "face_detection_overlay": True,     # 顔検出の枠表示
}

# === 通知設定 ===
NOTIFICATION_SETTINGS = {
    "notify_known_persons": True,       # 既知の人物の通知
    "notify_unknown_persons": True,     # 未知の人物の通知
    "notify_system_errors": True,       # システムエラーの通知
    "notification_sound": True,         # 通知音
    "save_notification_log": True,      # 通知ログの保存
}

# === 実験的機能 ===
EXPERIMENTAL_FEATURES = {
    "face_emotion_detection": False,    # 表情検出（実験的）
    "face_age_estimation": False,       # 年齢推定（実験的）
    "face_mask_detection": False,       # マスク検出（実験的）
    "multiple_camera_support": False,   # 複数カメラサポート（実験的）
}

# === バックアップ設定 ===
BACKUP_SETTINGS = {
    "auto_backup": True,
    "backup_directory": DATA_DIR / "backups",
    "backup_interval_hours": 24,
    "keep_backup_days": 30,
    "backup_face_database": True,
    "backup_recognition_history": True,
    "backup_configuration": True,
}

# バックアップディレクトリ作成
if BACKUP_SETTINGS["auto_backup"]:
    BACKUP_SETTINGS["backup_directory"].mkdir(exist_ok=True)