"""
高精度顔認識システムセットアップスクリプト
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """ヘッダー表示"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

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
        print(f"エラー: {e}")
        return False

def check_system_requirements():
    """システム要件チェック"""
    print("システム要件を確認中...")
    
    # Python バージョンチェック
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"Python 3.8以上が必要です (現在: {version.major}.{version.minor})")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    # プラットフォーム確認
    system = platform.system()
    print(f"✓ OS: {system}")
    
    # メモリ確認
    try:
        import psutil
        memory = psutil.virtual_memory().total / (1024**3)  # GB
        print(f"✓ メモリ: {memory:.1f}GB")
        
        if memory < 4:
            print("⚠ 警告: 4GB以上のメモリを推奨します")
    except ImportError:
        print("- メモリ情報を取得できませんでした")
    
    return True

def install_face_recognition_dependencies():
    """face_recognition依存関係インストール"""
    print("face_recognition ライブラリの依存関係をインストール中...")
    
    system = platform.system()
    pip_cmd = "venv\\Scripts\\pip" if system == "Windows" else "venv/bin/pip"
    
    # 必要なパッケージリスト
    packages = [
        "cmake",  # dlib のビルドに必要
        "numpy",
        "pillow",
        "opencv-python"
    ]
    
    for package in packages:
        if not run_command(f"{pip_cmd} install {package}", f"{package} インストール"):
            print(f"警告: {package} のインストールに失敗しました")
    
    # システム固有の依存関係
    if system == "Windows":
        print("\nWindows用の追加設定...")
        # Windowsの場合、Visual Studio Build Toolsが必要
        print("注意: Visual Studio Build Tools が必要な場合があります")
        print("https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019")
        
    elif system == "Darwin":  # macOS
        print("\nmacOS用の追加設定...")
        print("Xcode Command Line Tools が必要です:")
        print("xcode-select --install")
        
    elif system == "Linux":
        print("\nLinux用の追加設定...")
        print("以下のパッケージが必要な場合があります:")
        print("Ubuntu/Debian: sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev")
        print("CentOS/RHEL: sudo yum install gcc gcc-c++ cmake")

def install_dlib():
    """dlib ライブラリインストール"""
    print("dlib ライブラリをインストール中...")
    
    system = platform.system()
    pip_cmd = "venv\\Scripts\\pip" if system == "Windows" else "venv/bin/pip"
    
    # dlib インストールの試行
    dlib_install_methods = [
        "dlib",
        "dlib --no-cache-dir",
        "dlib --verbose"
    ]
    
    for method in dlib_install_methods:
        print(f"試行中: {method}")
        if run_command(f"{pip_cmd} install {method}", f"dlib インストール ({method})"):
            print("✓ dlib インストール成功")
            return True
        print(f"失敗: {method}")
    
    print("dlib のインストールに失敗しました")
    print("手動インストールが必要な場合があります:")
    print("詳細: https://github.com/davisking/dlib")
    return False

def install_face_recognition():
    """face_recognition ライブラリインストール"""
    print("face_recognition ライブラリをインストール中...")
    
    system = platform.system()
    pip_cmd = "venv\\Scripts\\pip" if system == "Windows" else "venv/bin/pip"
    
    # face_recognition インストール
    if run_command(f"{pip_cmd} install face_recognition", "face_recognition インストール"):
        print("✓ face_recognition インストール成功")
        return True
    else:
        print("face_recognition のインストールに失敗しました")
        
        # 代替インストール方法
        print("代替方法を試行中...")
        alternative_methods = [
            "face_recognition --no-deps",
            "face_recognition --no-cache-dir"
        ]
        
        for method in alternative_methods:
            if run_command(f"{pip_cmd} install {method}", f"face_recognition インストール ({method})"):
                print("✓ face_recognition インストール成功（代替方法）")
                return True
        
        return False

def test_face_recognition():
    """face_recognition ライブラリテスト"""
    print("face_recognition ライブラリをテスト中...")
    
    system = platform.system()
    python_cmd = "venv\\Scripts\\python" if system == "Windows" else "venv/bin/python"
    
    test_code = '''
try:
    import face_recognition
    import numpy as np
    print("✓ face_recognition インポート成功")
    
    # 簡単なテスト
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    face_locations = face_recognition.face_locations(test_image)
    print("✓ 顔検出機能テスト成功")
    
    face_encodings = face_recognition.face_encodings(test_image)
    print("✓ 顔エンコーディング機能テスト成功")
    
    print("face_recognition ライブラリは正常に動作しています")
    
except ImportError as e:
    print(f"インポートエラー: {e}")
    exit(1)
except Exception as e:
    print(f"テストエラー: {e}")
    exit(1)
'''
    
    try:
        result = subprocess.run([python_cmd, "-c", test_code], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"テスト失敗: {e}")
        print(f"標準出力: {e.stdout}")
        print(f"標準エラー: {e.stderr}")
        return False

def create_advanced_face_files():
    """高精度顔認識ファイルを作成"""
    print("高精度顔認識システムファイルを作成中...")
    
    # 既に作成済みのファイルをコピー（実際の実装では手動でコピーする必要がある）
    files_to_create = [
        "face_recognition_advanced.py",
        "face_recognition_module_updated.py", 
        "main_system_with_advanced_face.py",
        "face_manager.py"
    ]
    
    for filename in files_to_create:
        if Path(filename).exists():
            print(f"✓ {filename} が存在します")
        else:
            print(f"⚠ {filename} が見つかりません")
            print(f"  このファイルを手動で作成してください")

def setup_database():
    """データベースディレクトリセットアップ"""
    print("データベースディレクトリをセットアップ中...")
    
    # 必要なディレクトリを作成
    directories = [
        "data",
        "data/registration_photos",
        "data/captures",
        "data/test_images",
        "data/logs"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✓ ディレクトリ作成: {dir_name}")
        else:
            print(f"- ディレクトリ存在: {dir_name}")

def create_quick_start_guide():
    """クイックスタートガイド作成"""
    guide_content = """# 高精度顔認識システム クイックスタートガイド

## 1. システムの起動

```bash
# システムテスト
python main.py test

# Webインターフェースで起動
python main.py web
```

## 2. 人物の登録

```bash
# 新しい人物を登録
python face_manager.py register

# 登録済み人物一覧表示
python face_manager.py list
```

## 3. 登録の手順

### 家族の登録例
1. `python face_manager.py register`
2. 人物ID: `family_dad`
3. 名前: `お父さん`
4. 関係性: `家族`
5. 備考: `お疲れ様です`
6. カメラで3枚の写真を撮影

### 配達員の登録例
1. `python face_manager.py register`
2. 人物ID: `delivery_yamato`
3. 名前: `ヤマト配達員`
4. 関係性: `配達員`
5. 備考: `いつものヤマト運輸の方`

## 4. 認識テスト

```bash
# リアルタイム認識テスト
python face_manager.py test
```

## 5. システムの利点

- **即座の認識**: 既知の人物は1-2秒で認識
- **Ollama不要**: 既知の人物にはAI分析を使わない
- **個別メッセージ**: 関係性に応じたカスタムメッセージ
- **認識履歴**: 誰がいつ来たかの記録

## 6. トラブルシューティング

### 顔認識精度が低い場合
- 明るい場所で正面を向いて登録
- 複数枚の写真で登録（推奨3-5枚）
- メガネ、帽子の有無を考慮

### 認識されない場合
- `python face_manager.py test` で確認
- 信頼度の閾値を調整
- 追加の写真で再登録

## 7. データ管理

```bash
# 認識統計表示
python face_manager.py stats

# データベースエクスポート
python face_manager.py export

# 人物削除
python face_manager.py delete
```
"""
    
    with open("QUICK_START_ADVANCED_FACE.md", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✓ クイックスタートガイドを作成: QUICK_START_ADVANCED_FACE.md")

def create_requirements_advanced():
    """高精度顔認識用requirements.txt作成"""
    requirements_content = """# 高精度顔認識システム用requirements.txt

# 基本パッケージ
numpy>=1.21.0
opencv-python>=4.5.0
pillow>=8.0.0
requests>=2.25.0
flask>=2.0.0
pyttsx3>=2.90

# 高精度顔認識用
dlib>=19.22.0
face-recognition>=1.3.0

# データベース・ユーティリティ
sqlite3  # Python標準ライブラリ
psutil  # システム情報取得用

# オプション（既存機能）
# mediapipe>=0.8.0
"""
    
    with open("requirements_advanced_face.txt", 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print("✓ 高精度顔認識用requirements.txt作成")

def main():
    """メインセットアップ処理"""
    print_header("高精度顔認識システム セットアップ")
    
    # Step 1: システム要件チェック
    print_step(1, "システム要件チェック")
    if not check_system_requirements():
        print("システム要件を満たしていません")
        sys.exit(1)
    
    # Step 2: 基本依存関係インストール
    print_step(2, "基本依存関係インストール")
    install_face_recognition_dependencies()
    
    # Step 3: dlib インストール
    print_step(3, "dlib ライブラリインストール")
    dlib_success = install_dlib()
    
    # Step 4: face_recognition インストール
    print_step(4, "face_recognition ライブラリインストール")
    if dlib_success:
        face_rec_success = install_face_recognition()
    else:
        print("dlib が利用できないため face_recognition をスキップ")
        face_rec_success = False
    
    # Step 5: テスト実行
    if face_rec_success:
        print_step(5, "face_recognition ライブラリテスト")
        test_success = test_face_recognition()
    else:
        test_success = False
    
    # Step 6: ファイルとディレクトリセットアップ
    print_step(6, "システムファイルセットアップ")
    create_advanced_face_files()
    setup_database()
    
    # Step 7: ドキュメント作成
    print_step(7, "ドキュメント作成")
    create_quick_start_guide()
    create_requirements_advanced()
    
    # 完了メッセージ
    print_header("セットアップ完了")
    
    if test_success:
        print("高精度顔認識システムのセットアップが完了しました！")
        print()
        print("成功した機能:")
        print("  - dlib ライブラリ")
        print("  - face_recognition ライブラリ")
        print("  - 顔認識機能テスト")
        print()
        print("次のステップ:")
        print("1. システムテスト: python main.py test")
        print("2. 人物登録: python face_manager.py register")
        print("3. 認識テスト: python face_manager.py test")
        print("4. システム起動: python main.py web")
        print()
        print("詳細な使用方法:")
        print("QUICK_START_ADVANCED_FACE.md をご覧ください")
        
    else:
        print("セットアップが部分的に完了しました")
        print()
        print(" 失敗した機能:")
        if not dlib_success:
            print("  - dlib ライブラリ")
        if not face_rec_success:
            print("  - face_recognition ライブラリ")
        
        print()
        print("トラブルシューティング:")
        print("1. システム要件を確認してください")
        print("   - Python 3.8以上")
        print("   - 4GB以上のメモリ")
        print("   - ビルドツール（cmake, gcc等）")
        print()
        print("2. 手動インストールを試してください:")
        print("   pip install cmake")
        print("   pip install dlib")
        print("   pip install face_recognition")
        print()
        print("3. プリコンパイル済みパッケージを使用:")
        print("   conda install -c conda-forge dlib")
        print("   conda install -c conda-forge face_recognition")
        print()
        print("4. システムは基本機能（MediaPipe/OpenCV）で動作可能です")
    
    print()
    print("ヒント:")
    print("- 登録時は明るい場所で正面から撮影")
    print("- 家族、配達員、友人など関係性を設定")
    print("- 複数枚の写真で登録すると認識精度向上")
    print("- 認識統計で使用状況を確認可能")

if __name__ == "__main__":
    main()