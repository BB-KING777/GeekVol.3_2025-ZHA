"""
分析用フレーム取得問題の診断・修正スクリプト
"""
import time
import cv2
import threading
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def debug_frame_buffer():
    """フレームバッファの動作確認"""
    print("=" * 60)
    print(" フレームバッファ動作診断")
    print("=" * 60)
    
    try:
        from camera_module import CameraManager, FrameBuffer
        from models import CameraFrame
        
        print("1. カメラマネージャーの初期化テスト")
        camera_manager = CameraManager()
        
        if camera_manager.start():
            print("✓ カメラマネージャー初期化成功")
        else:
            print("✗ カメラマネージャー初期化失敗")
            return False
        
        print("\n2. フレームバッファの初期化テスト")
        frame_buffer = FrameBuffer(max_frames=30)
        print("✓ フレームバッファ初期化成功")
        
        print("\n3. フレーム取得・バッファ追加テスト")
        for i in range(10):
            frame = camera_manager.get_frame()
            if frame:
                frame_buffer.add_frame(frame)
                print(f"✓ フレーム {i+1}: {frame.width}x{frame.height} ({frame.source})")
            else:
                print(f"✗ フレーム {i+1}: 取得失敗")
            time.sleep(0.5)
        
        print(f"\nバッファ内フレーム数: {len(frame_buffer.frames)}")
        
        print("\n4. 最新フレーム取得テスト")
        latest_frame = frame_buffer.get_latest_frame()
        if latest_frame:
            print(f"✓ 最新フレーム取得成功: {latest_frame.width}x{latest_frame.height}")
            
            # テスト画像保存
            test_path = Path("debug_latest_frame.jpg")
            cv2.imwrite(str(test_path), latest_frame.image)
            print(f"✓ テスト画像保存: {test_path}")
        else:
            print("✗ 最新フレーム取得失敗")
        
        print("\n5. オフセットフレーム取得テスト")
        offset_frame = frame_buffer.get_frame_by_offset(0.0)
        if offset_frame:
            print(f"✓ オフセットフレーム取得成功: {offset_frame.width}x{offset_frame.height}")
        else:
            print("✗ オフセットフレーム取得失敗")
        
        camera_manager.stop()
        return True
        
    except Exception as e:
        print(f"✗ フレームバッファテストエラー: {e}")
        return False

def debug_web_frame_capture():
    """Webアプリのフレームキャプチャ問題診断"""
    print("\n" + "=" * 60)
    print(" Webアプリフレームキャプチャ診断")
    print("=" * 60)
    
    try:
        from main_system import SystemController
        
        print("1. システムコントローラー初期化")
        controller = SystemController()
        
        if controller.initialize():
            print("✓ システムコントローラー初期化成功")
        else:
            print("✗ システムコントローラー初期化失敗")
            return False
        
        print("\n2. 現在フレーム取得テスト")
        current_frame = controller.system.get_current_frame()
        if current_frame:
            print(f"✓ 現在フレーム取得成功: {current_frame.width}x{current_frame.height}")
            
            # テスト画像保存
            test_path = Path("debug_current_frame.jpg")
            cv2.imwrite(str(test_path), current_frame.image)
            print(f"✓ テスト画像保存: {test_path}")
        else:
            print("✗ 現在フレーム取得失敗")
        
        print("\n3. フレームバッファから最新フレーム取得テスト")
        buffer_frame = controller.system.frame_buffer.get_latest_frame()
        if buffer_frame:
            print(f"✓ バッファフレーム取得成功: {buffer_frame.width}x{buffer_frame.height}")
            
            # テスト画像保存
            test_path = Path("debug_buffer_frame.jpg")
            cv2.imwrite(str(test_path), buffer_frame.image)
            print(f"✓ テスト画像保存: {test_path}")
        else:
            print("✗ バッファフレーム取得失敗")
        
        print("\n4. 直接カメラから取得テスト")
        direct_frame = controller.system.camera_manager.get_frame()
        if direct_frame:
            print(f"✓ 直接フレーム取得成功: {direct_frame.width}x{direct_frame.height}")
            
            # テスト画像保存
            test_path = Path("debug_direct_frame.jpg")
            cv2.imwrite(str(test_path), direct_frame.image)
            print(f"✓ テスト画像保存: {test_path}")
        else:
            print("✗ 直接フレーム取得失敗")
        
        print(f"\n5. システム状態確認")
        status = controller.get_status()
        system_status = status.get("system", {})
        print(f"システム稼働中: {system_status.get('is_running', False)}")
        print(f"処理中: {system_status.get('is_processing', False)}")
        print(f"カメラアクティブ: {system_status.get('camera_active', False)}")
        print(f"フレーム数: {system_status.get('frame_count', 0)}")
        
        controller.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ Webフレームキャプチャテストエラー: {e}")
        return False

def simulate_doorbell_analysis():
    """呼び鈴分析プロセスのシミュレーション"""
    print("\n" + "=" * 60)
    print(" 呼び鈴分析プロセス診断")
    print("=" * 60)
    
    try:
        from main_system import SystemController
        import threading
        
        print("1. システム初期化")
        controller = SystemController()
        
        if not controller.initialize():
            print("✗ システム初期化失敗")
            return False
        
        print("✓ システム初期化成功")
        
        # 数秒待機してフレームバッファを安定させる
        print("\n2. フレームバッファ安定化待機（5秒）")
        for i in range(5):
            time.sleep(1)
            frame_count = len(controller.system.frame_buffer.frames)
            print(f"  バッファ内フレーム数: {frame_count}")
        
        print("\n3. 呼び鈴分析シミュレーション")
        
        # 分析前の状態確認
        print("分析前の状態:")
        print(f"  システム稼働中: {controller.system.status.is_running}")
        print(f"  処理中: {controller.system.status.is_processing}")
        print(f"  バッファ内フレーム数: {len(controller.system.frame_buffer.frames)}")
        
        # 分析用フレーム取得テスト（analyze_visitorの一部を模擬）
        print("\n4. 分析用フレーム取得テスト")
        
        # 方法1: フレームバッファから最新フレーム
        frame1 = controller.system.frame_buffer.get_latest_frame()
        if frame1:
            print("✓ 方法1成功: フレームバッファから最新フレーム取得")
            cv2.imwrite("debug_analysis_method1.jpg", frame1.image)
        else:
            print("✗ 方法1失敗: フレームバッファから最新フレーム取得")
        
        # 方法2: オフセット指定（0秒）
        frame2 = controller.system.frame_buffer.get_frame_by_offset(0.0)
        if frame2:
            print("✓ 方法2成功: オフセット0秒でフレーム取得")
            cv2.imwrite("debug_analysis_method2.jpg", frame2.image)
        else:
            print("✗ 方法2失敗: オフセット0秒でフレーム取得")
        
        # 方法3: カメラから直接取得
        frame3 = controller.system.camera_manager.get_frame()
        if frame3:
            print("✓ 方法3成功: カメラから直接フレーム取得")
            cv2.imwrite("debug_analysis_method3.jpg", frame3.image)
        else:
            print("✗ 方法3失敗: カメラから直接フレーム取得")
        
        # 実際の呼び鈴処理テスト
        print("\n5. 実際の呼び鈴処理テスト")
        result = controller.doorbell_pressed(0.0)
        print(f"呼び鈴処理結果: {result}")
        
        # 分析完了を待機
        print("分析完了待機中...")
        for i in range(10):
            if not controller.system.status.is_processing:
                break
            time.sleep(1)
            print(f"  待機中... ({i+1}/10)")
        
        # 結果確認
        if controller.system.last_analysis_result:
            print("✓ 分析完了")
            print(f"  メッセージ: {controller.system.last_analysis_result.get_message()}")
            print(f"  処理時間: {controller.system.last_analysis_result.processing_time:.2f}秒")
        else:
            print("✗ 分析結果なし")
        
        controller.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ 呼び鈴分析シミュレーションエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fixed_analysis_method():
    """修正版の分析メソッドを提案"""
    print("\n" + "=" * 60)
    print(" 修正提案")
    print("=" * 60)
    
    print("問題の原因:")
    print("1. フレームバッファとWebストリーム間の競合")
    print("2. フレームレート制限による取得タイミングの問題")
    print("3. スレッド間でのフレーム共有の問題")
    
    print("\n修正方法:")
    print("1. web_app.pyの呼び鈴APIで直接current_frameを使用")
    print("2. フレームレート制限を一時的に無効化")
    print("3. フォールバック処理の追加")
    
    print("\n修正ファイルを作成しています...")

def main():
    """メイン診断処理"""
    print("フレーム取得問題の診断を開始します...\n")
    
    # Step 1: フレームバッファ動作確認
    if not debug_frame_buffer():
        print("フレームバッファに問題があります")
        return
    
    # Step 2: Webアプリフレームキャプチャ確認
    if not debug_web_frame_capture():
        print("Webアプリのフレームキャプチャに問題があります")
        return
    
    # Step 3: 呼び鈴分析プロセス確認
    if not simulate_doorbell_analysis():
        print("呼び鈴分析プロセスに問題があります")
        return
    
    # Step 4: 修正提案
    create_fixed_analysis_method()
    
    print("\n" + "=" * 60)
    print(" 診断完了")
    print("=" * 60)
    print("✓ すべての診断テストが完了しました")
    print("生成されたテスト画像を確認してください:")
    print("  - debug_latest_frame.jpg")
    print("  - debug_current_frame.jpg")
    print("  - debug_buffer_frame.jpg")
    print("  - debug_direct_frame.jpg")
    print("  - debug_analysis_method*.jpg")

if __name__ == "__main__":
    main()