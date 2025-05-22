"""
Webインターフェース - Flask アプリケーション
"""
import cv2
import time
import threading
from flask import Flask, request, jsonify, Response
from datetime import datetime

import config
from main_system import SystemController

# Flask アプリケーション初期化
app = Flask(__name__)
app.secret_key = "geekcamp_visitor_recognition_2024"

# システムコントローラー
system_controller = SystemController()
stream_active = True

def generate_video_stream():
    """MJPEG ビデオストリーム生成"""
    global stream_active
    
    while stream_active:
        try:
            if system_controller.is_initialized:
                frame = system_controller.system.get_current_frame()
                
                if frame:
                    # JPEG エンコード
                    _, buffer = cv2.imencode('.jpg', frame.image, [
                        cv2.IMWRITE_JPEG_QUALITY, 80
                    ])
                    frame_bytes = buffer.tobytes()
                    
                    # MJPEG フォーマット
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # プレースホルダー画像
                    placeholder = create_placeholder_image("カメラフィードなし")
                    _, buffer = cv2.imencode('.jpg', placeholder)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # システム未初期化
                placeholder = create_placeholder_image("システム初期化中...")
                _, buffer = cv2.imencode('.jpg', placeholder)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # フレームレート調整
            time.sleep(1.0 / config.FRAME_RATE)
            
        except Exception as e:
            print(f"ビデオストリームエラー: {e}")
            time.sleep(0.5)

def create_placeholder_image(text: str):
    """プレースホルダー画像作成"""
    import numpy as np
    
    img = np.ones((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8) * 240
    cv2.putText(img, text, (50, config.CAMERA_HEIGHT // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
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
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/status')
def api_status():
    """システム状態API"""
    return jsonify(system_controller.get_status())

@app.route('/api/doorbell', methods=['POST'])
def api_doorbell():
    """呼び鈴API"""
    try:
        data = request.get_json() or {}
        time_offset = data.get('time_offset', 0.0)
        
        result = system_controller.doorbell_pressed(time_offset)
        return jsonify(result)
        
    except Exception as e:
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
        result = system_controller.save_current_frame()
        return jsonify(result)
        
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
    try:
        # システム初期化
        print("システムを初期化中...")
        if not system_controller.initialize():
            print("システムの初期化に失敗しました")
            return False
        
        print(f"Webサーバーを起動中... http://{config.WEB_HOST}:{config.WEB_PORT}")
        
        # Flask サーバー起動
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=config.DEBUG_MODE,
            threaded=True,
            use_reloader=False  # リローダーを無効化（重複初期化防止）
        )
        
    except KeyboardInterrupt:
        print("\nキーボード割り込みを検出")
    except Exception as e:
        print(f"Webアプリケーションエラー: {e}")
    finally:
        # クリーンアップ
        global stream_active
        stream_active = False
        system_controller.shutdown()
        print("システムを終了しました")

if __name__ == "__main__":
    run_web_app()