"""
セットアップスクリプト - 環境構築自動化
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """ヘッダー表示"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_step(step, text):
    """ステップ表示"""
    print(f"\n[Step {step}] {text}")

def run_command(command, description=""):
    """コマンド実行"""
    if description:
        print(f"実行中: {description}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print("✓ 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失敗: {e}")
        if e.stdout:
            print(f"標準出力: {e.stdout}")
        if e.stderr:
            print(f"標準エラー: {e.stderr}")
        return False

def check_python_version():
    """Python バージョンチェック"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python 3.8以上が必要です (現在: {version.major}.{version.minor})")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_platform():
    """プラットフォーム情報表示"""
    system = platform.system()
    print(f"OS: {system}")
    print(f"アーキテクチャ: {platform.machine()}")
    print(f"プロセッサ: {platform.processor()}")
    return system

def create_directory_structure():
    """ディレクトリ構造作成"""
    directories = [
        "data",
        "data/captures", 
        "data/test_images",
        "data/logs",
        "venv"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✓ ディレクトリ作成: {dir_name}")
        else:
            print(f"- ディレクトリ存在: {dir_name}")

def setup_virtual_environment():
    """仮想環境セットアップ"""
    if not Path("venv").exists():
        print("仮想環境を作成中...")
        if not run_command(f"{sys.executable} -m venv venv", "仮想環境作成"):
            return False
    else:
        print("✓ 仮想環境が既に存在します")
    
    # 仮想環境のアクティベートコマンド取得
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    print(f"仮想環境アクティベート: {activate_cmd}")
    return pip_cmd

def install_dependencies(pip_cmd):
    """依存関係インストール"""
    requirements = [
        "opencv-python==4.8.1.78",
        "requests==2.31.0", 
        "flask==3.0.0",
        "numpy==1.24.3",
        "pillow==10.0.1",
        "pyttsx3==2.90"
    ]
    
    # pip アップグレード
    run_command(f"{pip_cmd} install --upgrade pip", "pip アップグレード")
    
    # 基本依存関係インストール
    for package in requirements:
        if not run_command(f"{pip_cmd} install {package}", f"{package} インストール"):
            print(f"警告: {package} のインストールに失敗しました")
    
    # オプション依存関係（顔認識用）
    print("\n=== オプション依存関係 ===")
    optional_packages = [
        ("mediapipe", "MediaPipe顔認識用"),
        ("face-recognition", "高精度顔認識用（時間がかかる場合があります）")
    ]
    
    for package, description in optional_packages:
        choice = input(f"{description} をインストールしますか? (y/N): ").lower()
        if choice in ['y', 'yes']:
            run_command(f"{pip_cmd} install {package}", f"{package} インストール")

def install_system_dependencies():
    """システム依存関係インストール"""
    system = platform.system()
    
    if system == "Windows":
        print("Windows: システム音声合成は標準で利用可能です")
        
    elif system == "Darwin":  # macOS
        print("macOS: システム音声合成は標準で利用可能です")
        
    elif system == "Linux":
        print("Linux: 音声合成ツールのインストールを確認中...")
        
        # espeak チェック
        if run_command("which espeak", "espeak確認"):
            print("✓ espeak が利用可能です")
        else:
            print("espeakをインストールすることを推奨します:")
            print("  Ubuntu/Debian: sudo apt-get install espeak espeak-data")
            print("  CentOS/RHEL: sudo yum install espeak")

def create_sample_config():
    """設定ファイルサンプル作成"""
    config_content = '''"""
設定ファイル - 環境に応じて調整してください
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

# === カメラ設定 ===
USE_CAMERA = True  # False: テスト画像を使用
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 3

# === Ollama API設定 ===
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"  # 使用するモデル名
REQUEST_TIMEOUT = 30

# === 人物認識設定 ===
USE_FACE_RECOGNITION = True
FACE_RECOGNITION_METHOD = "mediapipe"  # "mediapipe", "opencv_haar", "none"
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

# === 音声コマンド設定（OS別） ===
TTS_COMMANDS = {
    "Windows": [
        'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\\'{text}\\')"'
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
'''
    
    config_path = Path("config.py")
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✓ config.py を作成しました")
    else:
        print("- config.py は既に存在します")

def create_startup_scripts():
    """起動スクリプト作成"""
    # Windows用バッチファイル
    if platform.system() == "Windows":
        bat_content = '''@echo off
echo 訪問者認識システム起動中...
call venv\\Scripts\\activate
python web_app.py
pause
'''
        with open("start_system.bat", 'w', encoding='utf-8') as f:
            f.write(bat_content)
        print("✓ start_system.bat を作成しました")
    
    # Unix系用シェルスクリプト  
    else:
        sh_content = '''#!/bin/bash
echo "訪問者認識システム起動中..."
source venv/bin/activate
python web_app.py
'''
        with open("start_system.sh", 'w', encoding='utf-8') as f:
            f.write(sh_content)
        
        # 実行権限付与
        run_command("chmod +x start_system.sh", "実行権限付与")
        print("✓ start_system.sh を作成しました")

def create_readme():
    """README作成"""
    readme_content = '''# 訪問者認識システム

視覚障害者・高齢者向けの AI powered 玄関訪問者認識システムです。

## 機能

- **リアルタイム映像監視**: Webカメラまたはテスト画像での動作
- **AI画像分析**: Ollama を使用した訪問者の特徴分析
- **顔認識**: MediaPipe/OpenCV による顔検出
- **音声出力**: OS標準またはpyttsx3による読み上げ
- **Webインターフェース**: ブラウザから操作可能

## 必要環境

- Python 3.8以上
- Ollama (AI分析用)
- Webカメラ (オプション)

## セットアップ

1. セットアップスクリプト実行:
   ```bash
   python setup.py
   ```

2. Ollama インストール・起動:
   ```bash
   # Ollama公式サイトからダウンロード・インストール
   ollama pull gemma3:4b
   ollama serve
   ```

## 使用方法

### Windows
```cmd
start_system.bat
```

### macOS/Linux  
```bash
./start_system.sh
```

### 手動起動
```bash
source venv/bin/activate  # Windowsの場合: venv\\Scripts\\activate
python web_app.py
```

ブラウザで http://localhost:8080 にアクセス

## 設定

`config.py` ファイルで各種設定を変更可能:

- カメラ設定
- API設定
- 音声設定
- 顔認識設定

## トラブルシューティング

### カメラが認識されない
- `config.py` の `CAMERA_ID` を変更 (0, 1, 2...)
- テスト画像モードに切り替え: `USE_CAMERA = False`

### 音声が出力されない
- OS標準音声の確認
- `config.py` の音声設定確認

### Ollama接続エラー
- Ollamaサービス起動確認: `ollama serve`
- モデル確認: `ollama list`

## ライセンス

MIT License
'''
    
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ README.md を作成しました")

def main():
    """メインセットアップ処理"""
    print_header("訪問者認識システム セットアップ")
    
    # Step 1: 環境チェック
    print_step(1, "環境チェック")
    if not check_python_version():
        sys.exit(1)
    
    system = check_platform()
    
    # Step 2: ディレクトリ構造作成
    print_step(2, "ディレクトリ構造作成")
    create_directory_structure()
    
    # Step 3: 仮想環境セットアップ
    print_step(3, "仮想環境セットアップ")
    pip_cmd = setup_virtual_environment()
    if not pip_cmd:
        print("仮想環境のセットアップに失敗しました")
        sys.exit(1)
    
    # Step 4: 依存関係インストール
    print_step(4, "依存関係インストール")
    install_dependencies(pip_cmd)
    
    # Step 5: システム依存関係チェック
    print_step(5, "システム依存関係チェック")
    install_system_dependencies()
    
    # Step 6: 設定ファイル作成
    print_step(6, "設定ファイル作成")
    create_sample_config()
    
    # Step 7: 起動スクリプト作成
    print_step(7, "起動スクリプト作成")
    create_startup_scripts()
    
    # Step 8: README作成
    print_step(8, "ドキュメント作成")
    create_readme()
    
    # 完了メッセージ
    print_header("セットアップ完了")
    print("✓ 訪問者認識システムのセットアップが完了しました！")
    print()
    print("次のステップ:")
    print("1. Ollama をインストール・起動してください")
    print("   - https://ollama.ai からダウンロード")
    print("   - ollama pull gemma3:4b")
    print("   - ollama serve")
    print()
    print("2. システムを起動してください:")
    if system == "Windows":
        print("   start_system.bat")
    else:
        print("   ./start_system.sh")
    print()
    print("3. ブラウザで http://localhost:8080 にアクセス")
    print()
    print("詳細は README.md をご確認ください。")

if __name__ == "__main__":
    main()