"""
Webインターフェース - Flask アプリケーション（完全修正版）
"""
import cv2
import time
import threading
import numpy as np
from flask import Flask, request, jsonify, Response
from datetime import datetime

import config
from main_system import SystemController

# Flask アプリケーション初期化
app = Flask(__name__)
app.secret_key = "geekcamp_visitor_recognition_2024"

# グローバル変数
system_controller = SystemController()
stream_active = True
current_frame = None
frame_lock = threading.Lock()

def frame_capture_thread():
    """動作する最終版フレームキャプチャ"""
    global current_frame
    
    print("フレームキャプチャスレッド開始")
    success_count = 0
    last_frame_time = 0
    
    while stream_active:
        try:
            current_time = time.time()
            
            if system_controller.is_initialized:
                # フレームレート制限を一時的に無効化して取得を試行
                original_last_time = system_controller.system.camera_manager.last_frame_time
                system_controller.system.camera_manager.last_frame_time = 0
                
                # フレーム取得
                frame = system_controller.system.camera_manager.get_frame()
                
                # フレームレート制限を復元
                system_controller.system.camera_manager.last_frame_time = original_last_time
                
                if frame and frame.image is not None:
                    with frame_lock:
                        current_frame = frame.image.copy()
                    success_count += 1
                    last_frame_time = current_time
                    
                    if success_count % 30 == 0:
                        print(f"✓ フレーム取得成功: {success_count}回")
                
                # フレーム取得失敗時のフォールバック
                elif current_time - last_frame_time > 2.0:  # 2秒間取得できない場合
                    try:
                        # 直接カメラから取得
                        camera_manager = system_controller.system.camera_manager
                        if config.USE_CAMERA and camera_manager.camera and camera_manager.camera.isOpened():
                            ret, direct_frame = camera_manager.camera.read()
                            if ret and direct_frame is not None:
                                # タイムスタンプ追加
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cv2.putText(direct_frame, timestamp, (10, direct_frame.shape[0] - 10), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                
                                with frame_lock:
                                    current_frame = direct_frame.copy()
                                success_count += 1
                                last_frame_time = current_time
                                print("フォールバック: 直接カメラから取得成功")
                        
                        elif not config.USE_CAMERA and camera_manager.test_images:
                            # テスト画像から取得
                            test_frame = camera_manager.test_images[camera_manager.current_test_index].copy()
                            camera_manager.current_test_index = (camera_manager.current_test_index + 1) % len(camera_manager.test_images)
                            
                            # タイムスタンプ追加
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cv2.putText(test_frame, timestamp, (10, test_frame.shape[0] - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
                            with frame_lock:
                                current_frame = test_frame.copy()
                            success_count += 1
                            last_frame_time = current_time
                            print("フォールバック: テスト画像から取得成功")
                    except Exception as e:
                        print(f"フォールバック取得エラー: {e}")
                        
        except Exception as e:
            print(f"フレームキャプチャエラー: {e}")
        
        # 適切な間隔で待機
        time.sleep(0.1)
    
    print("フレームキャプチャスレッド終了")

def generate_video_stream():
    """MJPEG ビデオストリーム生成（修正版）"""
    global stream_active, current_frame
    
    frame_count = 0
    last_frame_time = time.time()
    
    while stream_active:
        try:
            frame_to_send = None
            
            # 現在のフレームを安全に取得
            with frame_lock:
                if current_frame is not None:
                    frame_to_send = current_frame.copy()
            
            if frame_to_send is not None:
                # 正常なフレームの場合
                success, buffer = cv2.imencode('.jpg', frame_to_send, [
                    cv2.IMWRITE_JPEG_QUALITY, 75
                ])
                
                if success:
                    frame_bytes = buffer.tobytes()
                    frame_count += 1
                    
                    # FPS計算とデバッグ出力
                    current_time = time.time()
                    if current_time - last_frame_time >= 5.0:  # 5秒ごと
                        fps = frame_count / (current_time - last_frame_time)
                        print(f"ストリームFPS: {fps:.1f}, フレーム送信: {frame_count}")
                        frame_count = 0
                        last_frame_time = current_time
                else:
                    raise Exception("JPEG encode failed")
            else:
                # フレームがない場合のプレースホルダー
                placeholder = create_placeholder_image("カメラ接続中...")
                success, buffer = cv2.imencode('.jpg', placeholder, [
                    cv2.IMWRITE_JPEG_QUALITY, 75
                ])
                if success:
                    frame_bytes = buffer.tobytes()
                else:
                    raise Exception("Placeholder encode failed")
            
            # MJPEG フォーマット出力
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # フレームレート制御
            time.sleep(1.0 / config.FRAME_RATE)
            
        except Exception as e:
            print(f"ストリームエラー: {e}")
            try:
                # エラー時のフォールバック
                error_img = create_placeholder_image(f"エラー")
                _, buffer = cv2.imencode('.jpg', error_img)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except:
                pass
            time.sleep(0.5)

def create_placeholder_image(text: str):
    """プレースホルダー画像作成"""
    img = np.ones((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8) * 200
    
    # テキスト描画
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2
    
    # テキストサイズ計算
    try:
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 中央配置
        x = max(10, (config.CAMERA_WIDTH - text_width) // 2)
        y = max(30, (config.CAMERA_HEIGHT + text_height) // 2)
        
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0), thickness)
        
        # タイムスタンプ
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(img, timestamp, (10, 30), font, 0.6, (100, 100, 100), 2)
    except Exception as e:
        print(f"プレースホルダー作成エラー: {e}")
        # 最小限の画像
        cv2.putText(img, "Camera", (250, 240), font, 1, (0, 0, 0), 2)
    
    return img

# === Webルート ===

@app.route('/')
def index():
    """メインページ"""
    status = system_controller.get_status()
    
    # システム状態に基づいた表示設定
    system_status = status.get("system", {})
    face_recognition_status = status.get("face_recognition", {})
    api_status = status.get("api", {})
    
    is_running = system_status.get("is_running", False)
    is_processing = system_status.get("is_processing", False)
    face_enabled = face_recognition_status.get("enabled", False)
    api_accessible = api_status.get("api_accessible", False)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>訪問者認識システム</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        
        .container {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }}
        
        .video-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .control-section {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .status-card, .result-card, .controls-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .video-container {{
            position: relative;
            text-align: center;
        }}
        
        .video-stream {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .video-overlay {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .status-active {{ background-color: #4CAF50; }}
        .status-inactive {{ background-color: #f44336; }}
        .status-warning {{ background-color: #ff9800; }}
        
        .doorbell-button {{
            width: 100%;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .doorbell-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        }}
        
        .doorbell-button:disabled {{
            background: #cccccc;
            cursor: not-allowed;
            transform: none;
        }}
        
        .action-button {{
            padding: 12px 20px;
            margin: 5px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .action-button:hover {{
            background-color: #e9ecef;
        }}
        
        .result-text {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
            min-height: 60px;
            font-size: 1.1em;
            line-height: 1.5;
        }}
        
        .config-section {{
            margin-top: 20px;
        }}
        
        .config-row {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            gap: 10px;
        }}
        
        .config-label {{
            min-width: 120px;
            font-weight: 500;
        }}
        
        .slider {{
            flex: 1;
            margin: 0 10px;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 訪問者認識システム</h1>
        <p>AI powered visitor recognition for accessibility</p>
    </div>
    
    <div class="container">
        <div class="video-section">
            <h2>📹 ライブ映像</h2>
            <div class="video-container">
                <img id="videoStream" class="video-stream" src="/video_feed" alt="ライブ映像">
                <div class="video-overlay" id="fpsCounter">FPS: --</div>
            </div>
        </div>
        
        <div class="control-section">
            <div class="status-card">
                <h3>📊 システム状態</h3>
                <p>
                    <span class="status-indicator {'status-active' if is_running else 'status-inactive'}"></span>
                    システム: {'稼働中' if is_running else '停止中'}
                </p>
                <p>
                    <span class="status-indicator {'status-active' if api_accessible else 'status-inactive'}"></span>
                    AI分析: {'利用可能' if api_accessible else '利用不可'}
                </p>
                <p>
                    <span class="status-indicator {'status-active' if face_enabled else 'status-inactive'}"></span>
                    顔認識: {'有効' if face_enabled else '無効'}
                </p>
                <p id="statusText">{'処理中...' if is_processing else '待機中'}</p>
            </div>
            
            <div class="controls-card">
                <h3>🔔 操作</h3>
                <button id="doorbellButton" class="doorbell-button" {'disabled' if not is_running else ''}>
                    呼び鈴を押す
                </button>
                
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button id="speakButton" class="action-button">🔊 読み上げ</button>
                    <button id="captureButton" class="action-button">📷 保存</button>
                </div>
            </div>
            
            <div class="result-card">
                <h3>📝 分析結果</h3>
                <div id="resultText" class="result-text">
                    ここに分析結果が表示されます
                </div>
            </div>
            
            <div class="status-card config-section">
                <h3>⚙️ 設定</h3>
                <div class="config-row">
                    <span class="config-label">時間オフセット:</span>
                    <input type="range" id="timeOffset" class="slider" min="-5" max="5" value="0" step="1">
                    <span id="timeOffsetValue">0秒</span>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button id="restartButton" class="action-button">🔄 再起動</button>
                    <button id="shutdownButton" class="action-button">🛑 停止</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // DOM要素取得
        const doorbellButton = document.getElementById('doorbellButton');
        const speakButton = document.getElementById('speakButton');
        const captureButton = document.getElementById('captureButton');
        const restartButton = document.getElementById('restartButton');
        const shutdownButton = document.getElementById('shutdownButton');
        const statusText = document.getElementById('statusText');
        const resultText = document.getElementById('resultText');
        const timeOffset = document.getElementById('timeOffset');
        const timeOffsetValue = document.getElementById('timeOffsetValue');
        const fpsCounter = document.getElementById('fpsCounter');
        const videoStream = document.getElementById('videoStream');
        
        // 状態管理
        let isProcessing = false;
        let frameCount = 0;
        let lastFpsUpdate = Date.now();
        
        // FPS計測
        videoStream.onload = function() {{
            frameCount++;
            const now = Date.now();
            if (now - lastFpsUpdate > 1000) {{
                const fps = Math.round(frameCount * 1000 / (now - lastFpsUpdate));
                fpsCounter.textContent = `FPS: ${{fps}}`;
                frameCount = 0;
                lastFpsUpdate = now;
            }}
        }};
        
        // エラーハンドリング
        videoStream.onerror = function() {{
            console.error('ビデオストリーム読み込みエラー');
            fpsCounter.textContent = 'エラー';
        }};
        
        // 呼び鈴ボタン
        doorbellButton.addEventListener('click', function() {{
            if (isProcessing) return;
            
            const offset = parseFloat(timeOffset.value);
            
            fetch('/api/doorbell', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ time_offset: offset }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (!data.success) {{
                    alert('エラー: ' + data.message);
                }}
            }})
            .catch(error => {{
                console.error('通信エラー:', error);
                alert('通信エラーが発生しました');
            }});
        }});
        
        // 読み上げボタン
        speakButton.addEventListener('click', function() {{
            const text = resultText.textContent.trim();
            if (!text || text === 'ここに分析結果が表示されます') {{
                alert('読み上げる内容がありません');
                return;
            }}
            
            fetch('/api/speak', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ text: text }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (!data.success) {{
                    alert('音声出力エラー: ' + data.message);
                }}
            }});
        }});
        
        // 保存ボタン
        captureButton.addEventListener('click', function() {{
            fetch('/api/capture', {{ method: 'POST' }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    alert('画像を保存しました: ' + data.message);
                }} else {{
                    alert('保存エラー: ' + data.message);
                }}
            }});
        }});
        
        // 時間オフセット
        timeOffset.addEventListener('input', function() {{
            timeOffsetValue.textContent = this.value + '秒';
        }});
        
        // ステータス更新
        function updateStatus() {{
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {{
                const system = data.system || {{}};
                isProcessing = system.is_processing || false;
                
                statusText.textContent = isProcessing ? '処理中...' : '待機中';
                doorbellButton.disabled = isProcessing || !system.is_running;
                
                if (data.last_result && data.last_result.message) {{
                    resultText.textContent = data.last_result.message;
                }}
            }})
            .catch(error => console.error('ステータス更新エラー:', error));
        }}
        
        // キーボードショートカット
        document.addEventListener('keydown', function(e) {{
            if (e.code === 'Space' && !isProcessing) {{
                e.preventDefault();
                doorbellButton.click();
            }}
        }});
        
        // 定期更新
        setInterval(updateStatus, 1000);
        updateStatus();
        
        // デバッグ情報
        console.log('Web app initialized');
        console.log('Video stream URL:', '/video_feed');
    </script>
</body>
</html>
    """
    
    return Response(html_content, content_type='text/html; charset=utf-8')

@app.route('/video_feed')
def video_feed():
    """ビデオストリーム"""
    return Response(
        generate_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

@app.route('/api/status')
def api_status():
    """システム状態API"""
    return jsonify(system_controller.get_status())

@app.route('/api/doorbell', methods=['POST'])
def api_doorbell():
    """呼び鈴API（修正版）"""
    try:
        data = request.get_json() or {}
        time_offset = data.get('time_offset', 0.0)
        
        # 現在フレームの直接取得
        global current_frame
        analysis_frame = None
        
        with frame_lock:
            if current_frame is not None:
                analysis_frame = current_frame.copy()
                print(f"分析用フレーム取得成功: {analysis_frame.shape}")
        
        if analysis_frame is None:
            # フォールバック: システムから直接取得
            if system_controller.is_initialized:
                frame = system_controller.system.camera_manager.get_frame()
                if frame and frame.image is not None:
                    analysis_frame = frame.image.copy()
                    print(f"フォールバック分析用フレーム取得: {analysis_frame.shape}")
        
        if analysis_frame is None:
            print("分析用フレーム取得失敗")
            return jsonify({
                "success": False,
                "message": "分析用の画像を取得できませんでした"
            })
        
        # 通常の分析処理を実行（非同期）
        def run_analysis():
            try:
                result = system_controller.doorbell_pressed(time_offset)
                print(f"分析結果: {result}")
            except Exception as e:
                print(f"分析処理エラー: {e}")
        
        threading.Thread(target=run_analysis, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message": "訪問者分析を開始しました"
        })
        
    except Exception as e:
        print(f"呼び鈴API エラー: {e}")
        return jsonify({
            "success": False,
            "message": f"処理エラー: {str(e)}"
        }), 500

@app.route('/api/speak', methods=['POST'])
def api_speak():
    """音声出力API"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "message": "テキストが指定されていません"
            }), 400
        
        result = system_controller.speak_text(data['text'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"音声出力エラー: {str(e)}"
        }), 500

@app.route('/api/capture', methods=['POST'])
def api_capture():
    """画像保存API"""
    try:
        global current_frame
        
        # 現在フレームを取得
        with frame_lock:
            if current_frame is not None:
                save_frame = current_frame.copy()
            else:
                save_frame = None
        
        if save_frame is None:
            return jsonify({
                "success": False,
                "message": "保存する画像がありません"
            })
        
        # 画像保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_capture_{timestamp}.jpg"
        filepath = config.CAPTURES_DIR / filename
        
        cv2.imwrite(str(filepath), save_frame)
        
        return jsonify({
            "success": True,
            "message": filename
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"保存エラー: {str(e)}"
        }), 500

@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    """システム停止API"""
    try:
        result = system_controller.shutdown()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"停止エラー: {str(e)}"
        }), 500

def run_web_app():
    """Webアプリケーション起動"""
    global current_frame, stream_active
    
    try:
        # システム初期化
        print("システムを初期化中...")
        if not system_controller.initialize():
            print("システムの初期化に失敗しました")
            return False
        
        # フレームキャプチャスレッド開始
        print("フレームキャプチャスレッドを開始...")
        capture_thread = threading.Thread(target=frame_capture_thread, daemon=True)
        capture_thread.start()
        
        # 初期フレーム取得確認
        print("初期フレーム取得テスト...")
        test_count = 0
        while test_count < 10 and current_frame is None:
            time.sleep(0.5)
            test_count += 1
            print(f"フレーム待機中... ({test_count}/10)")
        
        if current_frame is not None:
            print(f"✓ フレーム取得成功: {current_frame.shape}")
        else:
            print("⚠ 初期フレーム取得失敗（ストリームは継続）")
        
        print(f"Webサーバーを起動中... http://{config.WEB_HOST}:{config.WEB_PORT}")
        
        # Flask サーバー起動
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=config.DEBUG_MODE,
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\nキーボード割り込みを検出")
    except Exception as e:
        print(f"Webアプリケーションエラー: {e}")
    finally:
        # クリーンアップ
        stream_active = False
        system_controller.shutdown()
        print("システムを終了しました")

if __name__ == "__main__":
    run_web_app()