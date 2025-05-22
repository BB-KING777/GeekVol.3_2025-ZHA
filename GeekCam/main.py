"""
メインアプリケーション: システム全体の統合と制御（Tkinterボタン付き、修正版）
"""
import time
import signal
import sys
import cv2
import threading
import os
import numpy as np
import tkinter as tk
from tkinter import ttk
from camera_handler import CameraHandler
from api_client import ApiClient
from speech_module import SpeechModule
import config

class GemmaVisionSystem:
    def __init__(self):
        """システムの初期化"""
        self.camera = CameraHandler()
        self.api = ApiClient()
        self.speech = SpeechModule()
        self.running = False
        self.last_analysis_time = 0
        self.analysis_interval = 1  # 連続押下防止のための最小分析間隔（秒）
        self.analysis_count = 0
        self.last_result = ""
        # 現在のフレームを保持する変数
        self.current_frame = None
        self._ensure_test_image_dir()
        
        # Tkinter GUIの初期化
        self.root = None
        self.gui_thread = None
        
    def _ensure_test_image_dir(self):
        """テスト画像ディレクトリの確保"""
        if not config.USE_CAMERA:
            if not os.path.exists(config.TEST_IMAGES_DIR):
                os.makedirs(config.TEST_IMAGES_DIR)
                print(f"テスト画像ディレクトリを作成しました: {config.TEST_IMAGES_DIR}")
                
                # サンプルテスト画像を作成（実際のテスト画像がない場合用）
                if not os.listdir(config.TEST_IMAGES_DIR):
                    print("テスト画像ディレクトリが空のため、サンプル画像を作成します")
                    self._create_sample_images()
    
    def _create_sample_images(self):
        """サンプルテスト画像の作成"""
        # サンプル1: 制服を着た男性配達員
        delivery_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.rectangle(delivery_img, (200, 100), (440, 400), (0, 0, 200), -1)  # 青い制服
        cv2.circle(delivery_img, (320, 150), 50, (200, 180, 140), -1)  # 顔
        cv2.rectangle(delivery_img, (250, 250), (390, 300), (200, 200, 200), -1)  # 荷物
        cv2.putText(delivery_img, "Delivery Person", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(os.path.join(config.TEST_IMAGES_DIR, "delivery.jpg"), delivery_img)
        
        # サンプル2: スーツを着たビジネスパーソン
        business_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.rectangle(business_img, (200, 100), (440, 400), (50, 50, 50), -1)  # 黒いスーツ
        cv2.circle(business_img, (320, 150), 50, (200, 180, 140), -1)  # 顔
        cv2.rectangle(business_img, (250, 250), (390, 300), (0, 0, 100), -1)  # ブリーフケース
        cv2.putText(business_img, "Business Person", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(os.path.join(config.TEST_IMAGES_DIR, "business.jpg"), business_img)
        
        # サンプル3: 郵便配達員
        postman_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.rectangle(postman_img, (200, 100), (440, 400), (0, 120, 255), -1)  # オレンジ色の制服
        cv2.circle(postman_img, (320, 150), 50, (200, 180, 140), -1)  # 顔
        cv2.rectangle(postman_img, (250, 250), (390, 300), (200, 200, 200), -1)  # 郵便物
        cv2.putText(postman_img, "Postal Worker", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(os.path.join(config.TEST_IMAGES_DIR, "postman.jpg"), postman_img)
        
        print("3つのサンプルテスト画像を作成しました")
        
    def _setup_gui(self):
        """Tkinter GUIのセットアップ"""
        self.root = tk.Tk()
        self.root.title("玄関訪問者認識システム")
        self.root.geometry("400x300")
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame, 
            text="視覚障害者向け玄関訪問者認識システム", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # 状態表示ラベル
        self.status_var = tk.StringVar(value="システム稼働中")
        status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            font=("Arial", 10)
        )
        status_label.pack(pady=5)
        
        # 分析結果表示エリア
        result_frame = ttk.LabelFrame(main_frame, text="分析結果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_var = tk.StringVar(value="ここに分析結果が表示されます")
        result_label = ttk.Label(
            result_frame, 
            textvariable=self.result_var,
            wraplength=350,
            justify=tk.LEFT
        )
        result_label.pack(fill=tk.BOTH, expand=True)
        
        # 呼び鈴ボタン
        doorbell_button = ttk.Button(
            main_frame, 
            text="呼び鈴を押す",
            command=self._doorbell_pressed,
            style="Accent.TButton",
            width=20
        )
        doorbell_button.pack(pady=10)
        
        # 終了ボタン
        exit_button = ttk.Button(
            main_frame, 
            text="システム終了",
            command=self._exit_app,
            width=20
        )
        exit_button.pack(pady=5)
        
        # スタイルの設定
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 12, "bold"))
        
        # ウィンドウを閉じたときの処理
        self.root.protocol("WM_DELETE_WINDOW", self._exit_app)
        
        # 定期的な画像更新タイマー
        self.root.after(100, self._update_frame)
    
    def _doorbell_pressed(self):
        """呼び鈴ボタン押下時の処理"""
        current_time = time.time()
        # 連続分析を防止するための時間チェック
        if (current_time - self.last_analysis_time) >= self.analysis_interval:
            self.status_var.set("分析中...")
            self.root.update_idletasks()  # GUIを即時更新
            print("呼び鈴が押されました。訪問者の分析を行います...")
            self.speech.speak("分析中です。")
            
            # 非同期で分析を実行（GUIがフリーズしないように）
            threading.Thread(target=self._process_frame_and_update_gui, daemon=True).start()
            self.last_analysis_time = current_time
        else:
            print(f"連続分析防止のため、{self.analysis_interval}秒間隔を空けてください")
    
    def _process_frame_and_update_gui(self):
        """フレーム処理と結果のGUI表示（スレッド用）"""
        result = self._process_frame()
        if result:
            # GUIの更新（スレッドセーフな方法で）
            self.root.after(0, lambda: self._update_result_gui(result))
    
    def _update_result_gui(self, result):
        """分析結果をGUIに表示"""
        self.result_var.set(result)
        self.status_var.set("分析完了")
    
    def _exit_app(self):
        """アプリケーションの終了処理"""
        print("システムを終了します...")
        self.running = False
        if self.root:
            self.root.destroy()
    
    def _update_frame(self):
        """定期的にフレームを取得して表示（OpenCVウィンドウ用）"""
        if self.running:
            # フレームを取得して保存
            frame = self.camera.capture_frame()
            if frame is not None:
                self.current_frame = frame
                if config.DEBUG_MODE:
                    cv2.imshow('Vision System', frame)
                    cv2.waitKey(1)
            
            # 定期的に呼び出し
            if self.root:
                self.root.after(100, self._update_frame)
    
    def start(self):
        """システムの起動"""
        print("視覚障害者向け玄関訪問者認識システムを起動しています...")
        
        # カメラまたはテスト画像の初期化
        if not self.camera.start():
            mode = "カメラ" if config.USE_CAMERA else "テスト画像"
            self.speech.speak_sync(f"{mode}の初期化に失敗しました。システムを終了します。")
            return False
        
        # API接続テスト
        if not self.api.test_connection():
            self.speech.speak_sync("APIサーバーへの接続に失敗しました。LMStudioが起動しているか確認してください。")
            self.camera.stop()
            return False
            
        self.running = True
        mode_msg = "カメラ" if config.USE_CAMERA else "テスト画像"
        self.speech.speak(f"システムの起動が完了しました。{mode_msg}を監視しています。")
        
        # ユーザーへの案内
        self.speech.speak("呼び鈴ボタンを押して訪問者を確認してください。")
        return True
        
    def stop(self):
        """システムの停止"""
        self.running = False
        self.camera.stop()
        self.speech.clear_queue()
        self.speech.speak_sync("システムを停止します。")
        
        # OpenCVウィンドウを閉じる
        cv2.destroyAllWindows()
        
        print("システムを停止しました。")
        
    def run(self):
        """メインループ"""
        try:
            if not self.start():
                return
                
            print("システムを起動します。呼び鈴ボタンで訪問者分析を実行できます。")
            
            # デバッグ用ウィンドウ表示（常時表示）
            if config.DEBUG_MODE:
                window_name = 'Vision System'
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, 800, 600)
            
            # Tkinter GUIを別スレッドで起動
            self._setup_gui()
            
            # Tkinterメインループ
            self.root.mainloop()
                
        except KeyboardInterrupt:
            print("\nキーボード割り込みを検出しました。")
        finally:
            self.stop()
            
    def _process_frame(self):
        """フレームの処理と分析"""
        # 保存されたフレームを使用
        if self.current_frame is None:
            # フレームが保存されていない場合は新たに取得を試みる
            frame = self.camera.capture_frame()
            if frame is None:
                print("フレームの取得に失敗しました。")
                self.speech.speak("画像の取得に失敗しました。")
                return None
        else:
            # 既に保存されているフレームを使用
            frame = self.current_frame.copy()
            
        # デバッグモードで画像表示を更新
        if config.DEBUG_MODE:
            cv2.imshow('Vision System', frame)
            cv2.waitKey(1)
            
        # 画像をBase64エンコード
        base64_image = self.camera.get_base64_image(frame)
        
        # 画像分析
        self.analysis_count += 1
        print(f"画像分析 #{self.analysis_count} を実行中...")
        
        result = self.api.analyze_image(base64_image)
        
        # 結果を保存
        self.last_result = result
        
        # 結果を音声出力
        self.speech.speak(result)
        
        # デバッグモードで結果を画像に表示
        if config.DEBUG_MODE:
            result_frame = frame.copy()
            # 結果テキストを画像に追加
            y_pos = 30
            for line in result.split('\n'):
                cv2.putText(result_frame, line, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos += 30
            
            cv2.imshow('Analysis Result', result_frame)
            cv2.waitKey(1)
            
        print("分析完了。結果を音声で出力しています。")
        return result

def signal_handler(sig, frame):
    """シグナルハンドラ"""
    print("\nシステムを終了しています...")
    sys.exit(0)

def main():
    """メイン関数"""
    # シグナルハンドラの設定
    signal.signal(signal.SIGINT, signal_handler)
    
    # システムのインスタンス化と実行
    print("=" * 50)
    print(" 視覚障害者向け玄関訪問者認識システム ")
    print("=" * 50)
    print(f"動作モード: {'カメラ' if config.USE_CAMERA else 'テスト画像'}")
    print(f"API URL: {config.API_BASE_URL}")
    print(f"操作: Tkinterウィンドウの「呼び鈴を押す」ボタンをクリック")
    print("=" * 50)
    
    system = GemmaVisionSystem()
    system.run()

if __name__ == "__main__":
    main()