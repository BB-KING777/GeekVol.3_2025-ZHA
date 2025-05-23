#!/bin/bash

echo "==========================="
echo " Linux環境セットアップ修正"
echo "==========================="

# 現在の仮想環境を確認
echo "1. 仮想環境状態確認"
if [ -d "venv" ]; then
    echo "✓ venv ディレクトリが存在します"
else
    echo "✗ venv ディレクトリが見つかりません"
    echo "仮想環境を作成します..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
echo "2. 仮想環境アクティベート"
source venv/bin/activate

# pipの存在確認
echo "3. pip確認"
if [ -f "venv/bin/pip" ]; then
    echo "✓ venv/bin/pip が存在します"
else
    echo "✗ venv/bin/pip が見つかりません"
    echo "仮想環境を再作成します..."
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
fi

# pipアップグレード
echo "4. pipアップグレード"
venv/bin/pip install --upgrade pip

# 基本パッケージインストール
echo "5. 基本パッケージインストール"
venv/bin/pip install opencv-python
venv/bin/pip install requests
venv/bin/pip install flask
venv/bin/pip install numpy
venv/bin/pip install pillow
venv/bin/pip install pyttsx3

# Linux音声合成確認
echo "6. Linux音声合成確認"
if command -v espeak >/dev/null 2>&1; then
    echo "✓ espeak が利用可能です"
else
    echo "⚠ espeak がインストールされていません"
    echo "音声出力にはespeakをインストールすることを推奨します："
    echo "  sudo apt-get install espeak espeak-data"
fi

# MediaPipeインストール（オプション）
echo "7. MediaPipeインストール（オプション）"
read -p "MediaPipe（顔認識用）をインストールしますか？ (y/N): " choice
if [[ $choice =~ ^[Yy]$ ]]; then
    venv/bin/pip install mediapipe
    echo "✓ MediaPipeインストール完了"
fi

echo "8. Linux用設定ファイル作成"
# Linux用設定ファイルを作成
cat > config.py << 'EOF'
"""
Linux用設定ファイル
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

# === カメラ設定 ===
USE_CAMERA = True  # False: テスト画像を使用
CAMERA_ID = 0  # Linuxのデフォルトカメラ
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 3

# === Ollama API設定 ===
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"
REQUEST_TIMEOUT = 300

# === 人物認識設定 ===
USE_FACE_RECOGNITION = True
FACE_RECOGNITION_METHOD = "opencv_haar"  # Linuxでは安定性のためHaarを推奨
FACE_CONFIDENCE_THRESHOLD = 0.7

# === 音声設定 ===
VOICE_RATE = 150
VOICE_VOLUME = 1.0
USE_SYSTEM_TTS = True  # Linux標準音声合成を使用

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

# === Linux音声コマンド ===
TTS_COMMANDS = {
    "Linux": [
        'espeak -v ja "{text}"',
        'festival --tts "{text}"',
        'spd-say "{text}"'
    ]
}

CURRENT_TTS_COMMANDS = TTS_COMMANDS.get(PLATFORM, [])
EOF

echo "✓ Linux用config.py作成完了"

# 起動スクリプト作成
echo "9. Linux用起動スクリプト作成"
cat > start_system.sh << 'EOF'
#!/bin/bash
echo "訪問者認識システム起動中（Linux版）..."
cd "$(dirname "$0")"

echo "仮想環境をアクティベート中..."
source venv/bin/activate

echo "システム開始..."
python main.py web

echo "システムが終了しました。Enterキーを押してください..."
read
EOF

chmod +x start_system.sh
echo "✓ start_system.sh作成完了"

# テスト用スクリプト作成
cat > test_system.sh << 'EOF'
#!/bin/bash
echo "システムテスト実行中（Linux版）..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py test
echo "テスト完了。Enterキーを押してください..."
read
EOF

chmod +x test_system.sh
echo "✓ test_system.sh作成完了"

echo ""
echo "============================"
echo " Linux環境セットアップ完了"
echo "============================"
echo "✓ 仮想環境構築"
echo "✓ 依存関係インストール"
echo "✓ Linux用設定ファイル作成"
echo "✓ 起動スクリプト作成"
echo ""
echo "次のステップ："
echo "1. Ollamaインストール（まだの場合）："
echo "   curl -fsSL https://ollama.ai/install.sh | sh"
echo "   ollama pull gemma3:4b"
echo "   ollama serve"
echo ""
echo "2. 音声合成インストール（推奨）："
echo "   sudo apt-get install espeak espeak-data"
echo ""
echo "3. システム起動："
echo "   ./start_system.sh"
echo "   または"
echo "   source venv/bin/activate && python main.py web"
echo ""
echo "4. ブラウザでアクセス："
echo "   http://localhost:8080"
