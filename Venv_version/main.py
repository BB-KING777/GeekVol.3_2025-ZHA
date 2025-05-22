"""
メインランチャー - システム起動エントリーポイント
"""
import sys
import os
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """依存関係チェック"""
    missing_modules = []
    
    required_modules = [
        'cv2',
        'requests', 
        'flask',
        'numpy',
        'PIL'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("エラー: 以下のモジュールがインストールされていません:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nセットアップを実行してください: python setup.py")
        return False
    
    return True

def check_config():
    """設定ファイルチェック"""
    config_path = Path("config.py")
    if not config_path.exists():
        print("エラー: config.py が見つかりません")
        print("セットアップを実行してください: python setup.py")
        return False
    return True

def run_web_interface():
    """Webインターフェース起動"""
    try:
        from web_app import run_web_app
        run_web_app()
    except ImportError as e:
        print(f"エラー: Webアプリケーションのインポートに失敗: {e}")
        return False
    except Exception as e:
        print(f"エラー: Webアプリケーション実行中にエラー: {e}")
        return False

def run_console_interface():
    """コンソールインターフェース起動"""
    try:
        from main_system import SystemController
        
        print("="*60)
        print(" 訪問者認識システム - コンソールモード")
        print("="*60)
        
        controller = SystemController()
        
        if not controller.initialize():
            print("システムの初期化に失敗しました")
            return False
        
        print("\nシステムが起動しました。")
        print("操作方法:")
        print("  Enter: 呼び鈴を押す")
        print("  q: 終了")
        print("  s: システム状態表示")
        print("  h: ヘルプ")
        
        while True:
            try:
                command = input("\n> ").lower().strip()
                
                if command == "" or command == "enter":
                    # 呼び鈴処理
                    result = controller.doorbell_pressed()
                    if result["success"]:
                        print("訪問者分析を開始しました...")
                    else:
                        print(f"エラー: {result['message']}")
                
                elif command == "q" or command == "quit":
                    break
                
                elif command == "s" or command == "status":
                    # ステータス表示
                    status = controller.get_status()
                    print("\n=== システム状態 ===")
                    system_status = status.get("system", {})
                    print(f"稼働状態: {'稼働中' if system_status.get('is_running') else '停止中'}")
                    print(f"処理状態: {'処理中' if system_status.get('is_processing') else '待機中'}")
                    print(f"フレーム数: {system_status.get('frame_count', 0)}")
                    
                    api_status = status.get("api", {})
                    print(f"API状態: {'接続中' if api_status.get('api_accessible') else '未接続'}")
                    
                elif command == "h" or command == "help":
                    print("\n=== ヘルプ ===")
                    print("Enter: 呼び鈴を押す（訪問者分析実行）")
                    print("s: システム状態表示")
                    print("q: システム終了")
                    print("h: このヘルプを表示")
                
                else:
                    print("不明なコマンドです。'h' でヘルプを表示")
            
            except KeyboardInterrupt:
                print("\nキーボード割り込みを検出")
                break
            except Exception as e:
                print(f"コマンド処理エラー: {e}")
        
        # 終了処理
        print("\nシステムを終了しています...")
        controller.shutdown()
        print("システムを終了しました")
        return True
        
    except ImportError as e:
        print(f"エラー: モジュールのインポートに失敗: {e}")
        return False
    except Exception as e:
        print(f"エラー: コンソールアプリケーション実行中にエラー: {e}")
        return False

def run_setup():
    """セットアップ実行"""
    try:
        import setup
        setup.main()
    except ImportError:
        print("エラー: setup.py が見つかりません")
        return False
    except Exception as e:
        print(f"セットアップエラー: {e}")
        return False

def run_test():
    """システムテスト実行"""
    print("="*60)
    print(" システムテスト")
    print("="*60)
    
    # 依存関係テスト
    print("1. 依存関係チェック...")
    if not check_dependencies():
        return False
    print("✓ 依存関係OK")
    
    # 設定ファイルテスト
    print("2. 設定ファイルチェック...")
    if not check_config():
        return False
    print("✓ 設定ファイルOK")
    
    # インポートテスト
    print("3. モジュールインポートテスト...")
    try:
        import config
        from camera_module import CameraManager
        from face_recognition_module import FaceRecognitionManager
        from audio_module import AudioManager
        from api_client import OllamaClient
        print("✓ モジュールインポートOK")
    except Exception as e:
        print(f"✗ モジュールインポートエラー: {e}")
        return False
    
    # API接続テスト
    print("4. API接続テスト...")
    try:
        from api_client import OllamaClient
        client = OllamaClient()
        if client.test_connection():
            print("✓ Ollama API接続OK")
        else:
            print("⚠ Ollama API接続失敗（Ollamaが起動していない可能性があります）")
    except Exception as e:
        print(f"⚠ API接続テストエラー: {e}")
    
    # カメラテスト
    print("5. カメラテスト...")
    try:
        from camera_module import CameraManager
        camera = CameraManager()
        if camera.start():
            frame = camera.get_frame()
            camera.stop()
            if frame:
                print("✓ カメラ動作OK")
            else:
                print("⚠ カメラフレーム取得失敗")
        else:
            print("⚠ カメラ初期化失敗（テスト画像モードを使用してください）")
    except Exception as e:
        print(f"⚠ カメラテストエラー: {e}")
    
    # 音声テスト
    print("6. 音声システムテスト...")
    try:
        from audio_module import AudioManager
        audio = AudioManager()
        audio.speak_immediately("テスト音声です", method="print")
        audio.stop()
        print("✓ 音声システムOK")
    except Exception as e:
        print(f"⚠ 音声システムテストエラー: {e}")
    
    print("\n" + "="*60)
    print("テスト完了")
    print("⚠ マークの項目は動作に支障がない場合があります")
    print("="*60)
    
    return True

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="訪問者認識システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py web          # Webインターフェースで起動 (推奨)
  python main.py console      # コンソールインターフェースで起動  
  python main.py setup        # セットアップ実行
  python main.py test         # システムテスト実行
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['web', 'console', 'setup', 'test'],
        default='web',
        nargs='?',
        help='起動モード (デフォルト: web)'
    )
    
    args = parser.parse_args()
    
    # モード別実行
    if args.mode == 'setup':
        print("セットアップを実行します...")
        return run_setup()
    
    elif args.mode == 'test':
        print("システムテストを実行します...")
        return run_test()
    
    elif args.mode == 'console':
        # 事前チェック
        if not check_dependencies() or not check_config():
            return False
        
        print("コンソールモードで起動します...")
        return run_console_interface()
    
    else:  # web mode (default)
        # 事前チェック
        if not check_dependencies() or not check_config():
            print("\n自動セットアップを実行しますか? (y/N): ", end="")
            choice = input().lower()
            if choice in ['y', 'yes']:
                if not run_setup():
                    return False
            else:
                print("セットアップを実行してください: python main.py setup")
                return False
        
        print("Webインターフェースで起動します...")
        return run_web_interface()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n終了しました")
        sys.exit(0)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)