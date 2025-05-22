"""
NumPy/OpenCV 互換性修正スクリプト
"""
import subprocess
import sys

def run_command(command, description=""):
    """コマンド実行"""
    print(f"実行中: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失敗: {e}")
        if e.stdout:
            print(f"出力: {e.stdout}")
        if e.stderr:
            print(f"エラー: {e.stderr}")
        return False

def fix_numpy_opencv_compatibility():
    """NumPy/OpenCV互換性修正"""
    print("=" * 60)
    print(" NumPy/OpenCV 互換性修正")
    print("=" * 60)
    
    pip_cmd = "venv\\Scripts\\pip"
    
    # Step 1: 問題のあるパッケージをアンインストール
    print("\n[Step 1] 問題パッケージのアンインストール")
    packages_to_remove = ["opencv-python", "opencv-contrib-python", "numpy"]
    
    for package in packages_to_remove:
        run_command(f"{pip_cmd} uninstall {package} -y", f"{package} アンインストール")
    
    # Step 2: 互換性のあるバージョンをインストール
    print("\n[Step 2] 互換性バージョンのインストール")
    
    # NumPy 1.x (OpenCVと互換性あり)
    if not run_command(f"{pip_cmd} install 'numpy<2'", "NumPy 1.x インストール"):
        # フォールバック: 特定バージョン
        run_command(f"{pip_cmd} install numpy==1.24.3", "NumPy 1.24.3 インストール")
    
    # OpenCV (NumPy 1.x互換)
    opencv_versions = [
        "opencv-python",
        "opencv-python==4.8.1.78", 
        "opencv-python-headless"
    ]
    
    opencv_installed = False
    for opencv_ver in opencv_versions:
        if run_command(f"{pip_cmd} install {opencv_ver}", f"{opencv_ver} インストール"):
            opencv_installed = True
            break
    
    if not opencv_installed:
        print("⚠ OpenCVのインストールに失敗しました")
    
    # Step 3: MediaPipe（オプション）
    print("\n[Step 3] MediaPipe インストール（オプション）")
    choice = input("MediaPipeを再試行しますか？ (y/N): ").lower()
    if choice in ['y', 'yes']:
        mediapipe_versions = [
            "mediapipe",
            "mediapipe==0.10.7"
        ]
        
        for mp_ver in mediapipe_versions:
            if run_command(f"{pip_cmd} install {mp_ver}", f"{mp_ver} インストール"):
                break
    
    # Step 4: 動作確認
    print("\n[Step 4] 動作確認")
    test_packages()

def test_packages():
    """パッケージテスト"""
    print("\n=== 動作確認テスト ===")
    
    test_cases = [
        ("numpy", "import numpy; print(f'NumPy: {numpy.__version__}')"),
        ("opencv", "import cv2; print(f'OpenCV: {cv2.__version__}')"),
        ("requests", "import requests; print('Requests: OK')"),
        ("flask", "import flask; print('Flask: OK')"),
        ("pillow", "import PIL; print('Pillow: OK')"),
        ("pyttsx3", "import pyttsx3; print('pyttsx3: OK')"),
        ("mediapipe", "import mediapipe; print('MediaPipe: OK')")
    ]
    
    for name, test_code in test_cases:
        try:
            result = subprocess.run([
                "venv\\Scripts\\python", "-c", test_code
            ], capture_output=True, text=True, check=True)
            print(f"✓ {name}: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            if name == "mediapipe":
                print(f"- {name}: インストールされていません（オプション）")
            else:
                print(f"✗ {name}: エラー")

def create_requirements_fixed():
    """修正版requirements.txt作成"""
    requirements_content = """# 互換性修正版 requirements.txt
# NumPy 1.x (OpenCV互換)
numpy<2

# 基本パッケージ
requests
flask
pillow
pyttsx3

# OpenCV (NumPy 1.x互換)
opencv-python

# オプション（手動インストール推奨）
# mediapipe
"""
    
    with open("requirements_fixed.txt", 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print("✓ requirements_fixed.txt を作成しました")

def main():
    """メイン処理"""
    print("NumPy/OpenCV 互換性問題を修正します...")
    
    # 互換性修正
    fix_numpy_opencv_compatibility()
    
    # 修正版requirements.txt作成
    create_requirements_fixed()
    
    print("\n" + "=" * 60)
    print(" 修正完了")
    print("=" * 60)
    print("✓ NumPy/OpenCV互換性問題を修正しました")
    print()
    print("次のステップ:")
    print("1. システムテスト実行:")
    print("   python main.py test")
    print()
    print("2. Ollama準備:")
    print("   ollama pull gemma3:4b")
    print("   ollama serve")
    print()
    print("3. システム起動:")
    print("   start_system.bat")

if __name__ == "__main__":
    main()
