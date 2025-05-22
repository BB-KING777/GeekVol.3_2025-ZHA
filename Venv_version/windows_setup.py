"""
Windows専用セットアップスクリプト - numpy/Pillow問題対応版
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
        print(f"⚠ 警告: {description} で問題が発生しましたが続行します")
        return False

def install_package_safe(pip_cmd, package_name, alternatives=None):
    """安全なパッケージインストール（複数の方法を試行）"""
    if alternatives is None:
        alternatives = []
    
    # 基本インストール試行
    packages_to_try = [package_name] + alternatives
    
    for pkg in packages_to_try:
        print(f"  試行中: {pkg}")
        if run_command(f"{pip_cmd} install {pkg}", f"{pkg} インストール"):
            return True
    
    print(f"  ⚠ {package_name} のインストールに失敗しました（後で手動インストールしてください）")
    return False

def main():
    """Windows専用セットアップ"""
    print_header("Windows専用 訪問者認識システム セットアップ")
    
    # Windows確認
    if platform.system() != "Windows":
        print("このスクリプトはWindows専用です")
        sys.exit(1)
    
    # Step 1: 基本確認
    print_step(1, "環境確認")
    version = sys.version_info
    print(f"Python: {version.major}.{version.minor}.{version.micro}")
    
    # Step 2: ディレクトリ作成
    print_step(2, "ディレクトリ構造作成")
    directories = ["data", "data/captures", "data/test_images", "data/logs"]
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"✓ {dir_name}")
    
    # Step 3: 仮想環境
    print_step(3, "仮想環境セットアップ")
    if not Path("venv").exists():
        run_command(f"{sys.executable} -m venv venv", "仮想環境作成")
    
    pip_cmd = "venv\\Scripts\\pip"
    
    # Step 4: pip関連ツール更新
    print_step(4, "ビルドツール更新")
    run_command(f"{pip_cmd} install --upgrade pip", "pip更新")
    run_command(f"{pip_cmd} install --upgrade setuptools wheel", "ビルドツール更新")
    
    # Step 5: パッケージインストール（安全版）
    print_step(5, "依存関係インストール（Windows対応版）")
    
    # 基本パッケージ
    basic_packages = [
        ("requests", []),
        ("flask", []),
        ("pyttsx3", [])
    ]
    
    for pkg, alternatives in basic_packages:
        install_package_safe(pip_cmd, pkg, alternatives)
    
    # 問題の多いパッケージ（複数の方法を試行）
    problematic_packages = [
        ("numpy", ["numpy --only-binary=all", "numpy --prefer-binary"]),
        ("pillow", ["pillow --only-binary=all", "pillow --prefer-binary"]),
        ("opencv-python", ["opencv-python --only-binary=all", "opencv-python-headless"])
    ]
    
    for pkg, alternatives in problematic_packages:
        install_package_safe(pip_cmd, pkg, alternatives)
    
    # Step 6: オプションパッケージ
    print_step(6, "オプションパッケージ")
    
    choice = input("MediaPipe（顔認識用）をインストールしますか？ (y/N): ").lower()
    if choice in ['y', 'yes']:
        install_package_safe(pip_cmd, "mediapipe", ["mediapipe --only-binary=all"])
    
    # Step 7: 設定ファイル作成
    print_step(7, "設定ファイル作成")
    create_config_file()
    
    # Step 8: 起動スクリプト作成
    print_step(8, "起動スクリプト作成")
    create_startup_scripts()
    
    # Step 9: 動作確認
    print_step(9, "インストール確認")
    test_imports()
    
    print_header("セットアップ完了")
    print("✓ Windowsセットアップが完了しました！")
    print()
    print("次のステップ:")
    print("1. Ollama をインストール・起動:")
    print("   - https://ollama.ai からダウンロード")
    print("   - コマンドプロンプトで: ollama pull gemma3:4b")
    print("   - コマンドプロンプトで: ollama serve")
    print()
    print("2. システム起動:")
    print("   start_system.bat をダブルクリック")
    print("   または")
    print("   python main.py web")
    print()
    print("3. ブラウザで http://localhost:8080 にアクセス")

def create_config_file():
    """Windows用config.py作成"""
    config_content = '''"""
Windows用設定ファイル
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
CAMERA_ID = 0  # Windowsのデフォルトカメラ
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FRAME_RATE = 3

# === Ollama API設定 ===
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"
REQUEST_TIMEOUT = 30

# === 人物認識設定 ===
USE_FACE_RECOGNITION = True
FACE_RECOGNITION_METHOD = "mediapipe"  # "mediapipe", "opencv_haar", "none"
FACE_CONFIDENCE_THRESHOLD = 0.7

# === 音声設定 ===
VOICE_RATE = 150
VOICE_VOLUME = 1.0
USE_SYSTEM_TTS = True  # Windows標準音声合成を使用

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
    
    with open("config.py", 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("✓ config.py 作成")

def create_startup_scripts():
    """Windows用起動スクリプト作成"""
    bat_content = '''@echo off
chcp 65001 > nul
echo 訪問者認識システム起動中...
cd /d "%~dp0"

echo 仮想環境をアクティベート中...
call venv\\Scripts\\activate

echo システム開始...
python main.py web

echo.
echo システムが終了しました。何かキーを押してください...
pause > nul
'''
    
    with open("start_system.bat", 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("✓ start_system.bat 作成")
    
    # テスト用バッチファイル
    test_bat_content = '''@echo off
chcp 65001 > nul
echo システムテスト実行中...
cd /d "%~dp0"
call venv\\Scripts\\activate
python main.py test
pause
'''
    
    with open("test_system.bat", 'w', encoding='utf-8') as f:
        f.write(test_bat_content)
    print("✓ test_system.bat 作成")

def test_imports():
    """インストールされたパッケージのテスト"""
    packages_to_test = [
        ("requests", "requests"),
        ("flask", "flask"),
        ("numpy", "numpy"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("pyttsx3", "pyttsx3")
    ]
    
    print("\n=== パッケージテスト ===")
    for import_name, package_name in packages_to_test:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - インストールされていません")
    
    # MediaPipeテスト（オプション）
    try:
        import mediapipe
        print("✓ mediapipe（オプション）")
    except ImportError:
        print("- mediapipe - インストールされていません（オプション）")

if __name__ == "__main__":
    main()