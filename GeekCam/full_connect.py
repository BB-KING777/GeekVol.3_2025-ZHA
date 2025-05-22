"""
視覚障害者向け玄関訪問者認識システム - リアルタイム映像対応版
"""
import os
import sys
import time
import cv2
import numpy as np
import base64
import json
import logging
import threading
import requests
import collections
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flaskアプリケーション初期化
app = Flask(__name__)

# グローバル変数
camera = None
is_processing = False
last_result = None
frame_buffer = collections.deque(maxlen=30)  # 最大30フレーム（約10秒間）のバッファ
current_frame = None
stream_active = True

# 設定
CONFIG = {
    "use_camera": True,           # カメラを使用するか（Falseの場合はテスト画像を使用）
    "camera_id": 0,                # カメラID
    "frame_rate": 3,               # フレームレート（fps）
    "api_url": "http://localhost:11434/api/chat",  # LLM API URL
    "api_key": "dummy-key",        # API Key
    "test_images_dir": "test_images",  # テスト画像ディレクトリ
    "time_offset": 0,              # 呼び鈴時のオフセット（秒）、正：未来、負：過去
    "stream_quality": 75,          # JPEG品質（1-100）
    "system_prompt": """
    あなたは視覚障害者や高齢者を支援するAIです。カメラに映っている人物の特徴を簡潔に説明してください。
    以下の情報を含めてください：
    1. 性別と推定年齢層
    2. 服装の特徴（色、スタイル）
    3. 持っているもの（荷物、書類など）
    4. 表情や姿勢
    5. 明らかな職業的特徴（制服など）
    6. 制服から予想できる職業

    怪しければ怪しいと教える必要があります。
    
    メガネをかけている、や持っているものの特徴、体形なども教えてください。

    簡潔で分かりやすい日本語で、50文字以内で説明してください。
    """
}

# カメラクラス
class RealtimeCamera:
    def __init__(self, use_camera=False, camera_id=0, frame_rate=3):
        self.use_camera = use_camera
        self.camera_id = camera_id
        self.frame_rate = frame_rate
        self.camera = None
        self.test_images = []
        self.current_test_index = 0
        self.is_running = False
        self.last_frame_time = 0
        
        # テスト画像ディレクトリの確認
        self._ensure_test_images_dir()

    def _ensure_test_images_dir(self):
        """テスト画像ディレクトリの確認と作成"""
        test_dir = CONFIG["test_images_dir"]
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            logger.info(f"テスト画像ディレクトリを作成しました: {test_dir}")
            self._create_sample_images(test_dir)

    def _create_sample_images(self, test_dir):
        """サンプルテスト画像の作成"""
        logger.info("サンプルテスト画像を作成しています...")
        
        # サンプル1: 配達員
        delivery_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.rectangle(delivery_img, (200, 100), (440, 400), (0, 0, 200), -1)
        cv2.circle(delivery_img, (320, 150), 50, (200, 180, 140), -1)
        cv2.putText(delivery_img, "Delivery Person", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(os.path.join(test_dir, "sample1.jpg"), delivery_img)
        
        # サンプル2: ビジネスパーソン
        business_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        cv2.rectangle(business_img, (200, 100), (440, 400), (50, 50, 50), -1)
        cv2.circle(business_img, (320, 150), 50, (200, 180, 140), -1)
        cv2.putText(business_img, "Business Person", (220, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(os.path.join(test_dir, "sample2.jpg"), business_img)
        
        logger.info("サンプルテスト画像を作成しました")

    def start(self):
        """カメラまたはテスト画像の起動"""
        if self.use_camera:
            try:
                self.camera = cv2.VideoCapture(self.camera_id)
                if not self.camera.isOpened():
                    logger.error(f"カメラの起動に失敗しました: ID {self.camera_id}")
                    return False
                self.is_running = True
                logger.info("カメラの起動に成功しました")
                
                # カメラの設定
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                return True
            except Exception as e:
                logger.error(f"カメラの起動中にエラーが発生しました: {e}")
                return False
        else:
            # テスト画像の読み込み
            self._load_test_images()
            if not self.test_images:
                logger.error("テスト画像が読み込めませんでした")
                return False
            self.is_running = True
            logger.info(f"{len(self.test_images)}枚のテスト画像を読み込みました")
            return True

    def _load_test_images(self):
        """テスト画像のロード"""
        self.test_images = []
        test_dir = CONFIG["test_images_dir"]
        
        for file in os.listdir(test_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(test_dir, file)
                image = cv2.imread(image_path)
                if image is not None:
                    self.test_images.append(image)
                    logger.info(f"テスト画像を読み込みました: {file}")
        
        # テスト画像がなければサンプル作成
        if not self.test_images:
            self._create_sample_images(test_dir)
            # 再度読み込み
            for file in os.listdir(test_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(test_dir, file)
                    image = cv2.imread(image_path)
                    if image is not None:
                        self.test_images.append(image)

    def get_frame(self):
        """フレームの取得"""
        if not self.is_running:
            return None
            
        # フレームレート制限
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        if elapsed < 1.0 / self.frame_rate:
            return None
            
        self.last_frame_time = current_time
            
        if self.use_camera:
            ret, frame = self.camera.read()
            if not ret:
                logger.error("カメラからのフレーム取得に失敗しました")
                return None
            
            # フレームにタイムスタンプを追加
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            return frame
        else:
            if not self.test_images:
                return None
                
            # 次のテスト画像を取得（ローテーション）
            frame = self.test_images[self.current_test_index].copy()
            self.current_test_index = (self.current_test_index + 1) % len(self.test_images)
            
            # フレームにタイムスタンプを追加
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            return frame

    def stop(self):
        """カメラの停止"""
        if self.use_camera and self.camera:
            self.camera.release()
        self.is_running = False
        logger.info("カメラを停止しました")

# 画像分析機能
def analyze_image(image):
    """画像をAPIに送信して分析結果を取得"""
    if image is None:
        return "画像の取得に失敗しました"
    
    try:
        # 画像をBase64エンコード
        _, buffer = cv2.imencode('.jpg', image)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        # APIリクエスト準備
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "gemma3:4b",
            "messages": [
                {"role": "system", "content": CONFIG["system_prompt"]},
                {"role": "user","content": "この画像に映っている人物について説明してください。",
                "images":[base64_image]},
            ],
            "stream": False,
        }
        
        # APIリクエスト送信
        response = requests.post(CONFIG["api_url"], headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["message"]["content"]
            logger.info(f"分析結果: {content}")
            return content
        else:
            error_message = f"API通信エラー: ステータスコード {response.status_code}"
            logger.error(error_message)
            return error_message
            
    except Exception as e:
        error_message = f"画像分析中にエラーが発生しました: {str(e)}"
        logger.error(error_message)
        return error_message

# 音声出力機能
def speak_text(text):
    """テキストを音声に変換（OSごとに適切な方法で）"""
    if not text:
        return False
        
    logger.info(f"音声出力: {text}")
    
    try:
        success = False
        
        # OSごとの音声合成コマンド
        if sys.platform == 'darwin':  # macOS
            os.system(f'say "{text}"')
            success = True
        elif sys.platform == 'linux':  # Linux
            # espeak、Open JTalk、またはその他のTTSがインストールされている場合
            if os.system('which espeak > /dev/null 2>&1') == 0:
                os.system(f'espeak -v ja "{text}"')
                success = True
            elif os.system('which open_jtalk > /dev/null 2>&1') == 0:
                # 一時ファイルに保存して実行
                with open('/tmp/speech.txt', 'w') as f:
                    f.write(text)
                os.system('open_jtalk -x /usr/local/dic -m /usr/local/voice/mei/mei_normal.htsvoice -ow /tmp/speech.wav /tmp/speech.txt')
                os.system('aplay /tmp/speech.wav')
                success = True
        elif sys.platform == 'win32':  # Windows
            # PowerShellを使用
            os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"')
            success = True
            
        # Pythonライブラリを使用した音声合成（フォールバック）
        if not success:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                success = True
            except Exception as e:
                logger.error(f"pyttsx3での音声合成エラー: {e}")
                
        # テキストファイルへの出力（最終フォールバック）
        if not success:
            logger.warning(f"音声合成に失敗しました。テキストとして出力します: {text}")
            print(f"\n==== 音声出力 ====\n{text}\n==================\n")
            
        return success
    except Exception as e:
        logger.error(f"音声合成エラー: {e}")
        return False

# フレームキャプチャスレッド
def frame_capture_thread():
    """バックグラウンドでフレームをキャプチャし続ける"""
    global camera, frame_buffer, current_frame
    
    logger.info("フレームキャプチャスレッドを開始")
    
    while camera and camera.is_running:
        frame = camera.get_frame()
        if frame is not None:
            # 現在のフレームとバッファを更新
            current_frame = frame.copy()
            timestamp = datetime.now()
            frame_buffer.append((timestamp, frame.copy()))
            
            # 古いフレームをクリア
            while len(frame_buffer) > 0:
                oldest_time = frame_buffer[0][0]
                if (timestamp - oldest_time).total_seconds() > 10:  # 10秒以上前のフレームは削除
                    frame_buffer.popleft()
                else:
                    break
        
        # 少し待機
        time.sleep(0.1)
    
    logger.info("フレームキャプチャスレッドを終了")

# ビデオストリーム生成
def generate_frames():
    """MJPEG形式のビデオストリームを生成"""
    global current_frame, stream_active
    
    while stream_active:
        if current_frame is not None:
            # フレームをJPEG形式にエンコード
            frame = current_frame.copy()
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, CONFIG["stream_quality"]])
            frame_bytes = buffer.tobytes()
            
            # MJPEGストリームのパート
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # フレームがない場合はプレースホルダー画像を送信
            placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 240
            cv2.putText(placeholder, "No Camera Feed", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            _, buffer = cv2.imencode('.jpg', placeholder)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
        # フレームレートの調整
        time.sleep(1.0 / CONFIG["frame_rate"])

# 呼び鈴処理関数
def process_doorbell():
    """呼び鈴が押されたときの処理（非同期実行用）"""
    global is_processing, last_result, frame_buffer
    
    is_processing = True
    logger.info("呼び鈴処理を開始します")
    
    try:
        # 音声通知
        speak_text("画像分析を開始します。少々お待ちください。")
        
        # オフセットを考慮してフレームを選択
        target_time = datetime.now() + timedelta(seconds=CONFIG["time_offset"])
        selected_frame = None
        
        if CONFIG["time_offset"] <= 0:
            # 過去のフレームを探索
            best_diff = float('inf')
            for timestamp, frame in frame_buffer:
                time_diff = abs((target_time - timestamp).total_seconds())
                if time_diff < best_diff:
                    best_diff = time_diff
                    selected_frame = frame.copy()
        else:
            # 未来のフレームを待つ
            wait_time = CONFIG["time_offset"]
            logger.info(f"{wait_time}秒後のフレームを待機中...")
            time.sleep(wait_time)
            if current_frame is not None:
                selected_frame = current_frame.copy()
        
        # フレームが選択できなかった場合は現在のフレームを使用
        if selected_frame is None:
            if current_frame is not None:
                selected_frame = current_frame.copy()
            else:
                speak_text("画像の取得に失敗しました。")
                is_processing = False
                return "画像の取得に失敗しました"
        
        # 保存用にタイムスタンプを付与
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_frame = selected_frame.copy()
        
        # 分析中であることを表示
        cv2.putText(analysis_frame, "分析中...", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # 画像分析
        result = analyze_image(selected_frame)
        last_result = result
        
        # 画像保存
        if not os.path.exists("captures"):
            os.makedirs("captures")
        cv2.imwrite(f"captures/analysis_{timestamp}.jpg", selected_frame)
        
        # 音声出力
        speak_text("分析結果: " + result)
        time.sleep(1)  # 少し間をあける
        speak_text(result)  # 重要なので2回読み上げ
        
        logger.info("呼び鈴処理が完了しました")
        is_processing = False
        return result
        
    except Exception as e:
        error_message = f"呼び鈴処理中にエラーが発生しました: {str(e)}"
        logger.error(error_message)
        speak_text("処理中にエラーが発生しました。")
        is_processing = False
        return error_message

# HTMLをインメモリで提供
@app.route('/')
def index():
    """メインページ"""
    html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>視覚障害者向け玄関訪問者認識システム</title>
    <style>
        body {
            font-family: sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .camera-view {
            width: 100%;
            text-align: center;
            margin-bottom: 20px;
            position: relative;
        }
        #cameraStream {
            max-width: 100%;
            border: 1px solid #ddd;
        }
        .controls {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .doorbell-button {
            padding: 15px 30px;
            font-size: 18px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .doorbell-button:disabled {
            background-color: #cccccc;
        }
        .result-box {
            border: 1px solid #ddd;
            padding: 15px;
            min-height: 100px;
            margin-bottom: 20px;
        }
        .status {
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .button-row {
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        .action-button {
            padding: 10px 20px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        }
        .config-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 10px;
            align-items: center;
        }
        .config-label {
            min-width: 180px;
        }
        .overlay {
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>視覚障害者向け玄関訪問者認識システム</h1>
    
    <div class="container">
        <div class="status" id="statusText">システム準備完了</div>
        
        <div class="camera-view">
            <img id="cameraStream" src="/video_feed" alt="カメラ映像">
            <div class="overlay" id="fpsInfo">FPS: 0</div>
        </div>
        
        <div class="controls">
            <button id="doorbellButton" class="doorbell-button">呼び鈴を押す</button>
        </div>
        
        <div>
            <h2>分析結果</h2>
            <div id="resultBox" class="result-box">
                ここに分析結果が表示されます
            </div>
            <div class="button-row">
                <button id="speakButton" class="action-button">結果を読み上げる</button>
                <button id="captureButton" class="action-button">現在の画像を保存</button>
            </div>
        </div>
        
        <div>
            <h2>設定</h2>
            <div class="config-row">
                <span class="config-label">時間オフセット:</span>
                <input type="range" id="timeOffsetSlider" min="-5" max="5" value="0" step="1">
                <span id="timeOffsetValue">0秒</span>
                <span>(負：過去、正：未来)</span>
            </div>
            <div class="config-row">
                <span class="config-label">ストリーム品質:</span>
                <input type="range" id="qualitySlider" min="30" max="100" value="75" step="5">
                <span id="qualityValue">75%</span>
            </div>
            <div class="config-row">
                <span class="config-label">フレームレート:</span>
                <input type="range" id="frameRateSlider" min="1" max="10" value="3" step="1">
                <span id="frameRateValue">3 FPS</span>
            </div>
        </div>
        
        <div class="button-row">
            <button id="restartButton" class="action-button">システム再起動</button>
            <button id="shutdownButton" class="action-button">システム停止</button>
        </div>
    </div>

    <script>
        // DOM要素
        const statusText = document.getElementById('statusText');
        const cameraStream = document.getElementById('cameraStream');
        const doorbellButton = document.getElementById('doorbellButton');
        const resultBox = document.getElementById('resultBox');
        const speakButton = document.getElementById('speakButton');
        const captureButton = document.getElementById('captureButton');
        const restartButton = document.getElementById('restartButton');
        const shutdownButton = document.getElementById('shutdownButton');
        const timeOffsetSlider = document.getElementById('timeOffsetSlider');
        const timeOffsetValue = document.getElementById('timeOffsetValue');
        const qualitySlider = document.getElementById('qualitySlider');
        const qualityValue = document.getElementById('qualityValue');
        const frameRateSlider = document.getElementById('frameRateSlider');
        const frameRateValue = document.getElementById('frameRateValue');
        const fpsInfo = document.getElementById('fpsInfo');
        
        // 状態変数
        let isProcessing = false;
        let frameCount = 0;
        let lastFpsUpdate = Date.now();
        
        // FPS計測
        function updateFps() {
            const now = Date.now();
            const elapsed = (now - lastFpsUpdate) / 1000;
            
            if (elapsed > 1) {  // 1秒ごとに更新
                const fps = Math.round(frameCount / elapsed);
                fpsInfo.textContent = `FPS: ${fps}`;
                frameCount = 0;
                lastFpsUpdate = now;
            }
        }
        
        // ストリーム画像読み込み時のイベント
        cameraStream.onload = function() {
            frameCount++;
            updateFps();
        };
        
        // 呼び鈴ボタン
        doorbellButton.addEventListener('click', function() {
            if (isProcessing) return;
            
            isProcessing = true;
            statusText.textContent = '分析中...';
            doorbellButton.disabled = true;
            
            fetch('/api/doorbell', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'エラーが発生しました');
                }
            })
            .catch(error => {
                console.error('通信エラー:', error);
                alert('通信エラーが発生しました');
                isProcessing = false;
                doorbellButton.disabled = false;
                statusText.textContent = 'エラー';
            });
        });
        
        // 結果読み上げボタン
        speakButton.addEventListener('click', function() {
            const text = resultBox.textContent;
            if (text && text !== 'ここに分析結果が表示されます') {
                fetch('/api/speak', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text })
                })
                .catch(error => console.error('読み上げエラー:', error));
            }
        });
        
        // 画像保存ボタン
        captureButton.addEventListener('click', function() {
            fetch('/api/capture', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('画像を保存しました: ' + data.filename);
                } else {
                    alert('画像の保存に失敗しました: ' + data.error);
                }
            })
            .catch(error => console.error('保存エラー:', error));
        });
        
        // 再起動ボタン
        restartButton.addEventListener('click', function() {
            if (confirm('システムを再起動しますか？')) {
                fetch('/api/restart', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'システムを再起動しています...');
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                })
                .catch(error => console.error('再起動エラー:', error));
            }
        });
        
        // 停止ボタン
        shutdownButton.addEventListener('click', function() {
            if (confirm('システムを停止しますか？')) {
                fetch('/api/shutdown', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'システムを停止しました');
                    statusText.textContent = '停止中';
                    doorbellButton.disabled = true;
                })
                .catch(error => console.error('停止エラー:', error));
            }
        });
        
        // 時間オフセットスライダー
        timeOffsetSlider.addEventListener('input', function() {
            const value = this.value;
            timeOffsetValue.textContent = `${value}秒`;
            
            // 設定をサーバーに送信
            updateConfig('time_offset', parseInt(value));
        });
        
        // 画質スライダー
        qualitySlider.addEventListener('input', function() {
            const value = this.value;
            qualityValue.textContent = `${value}%`;
            
            // 設定をサーバーに送信
            updateConfig('stream_quality', parseInt(value));
        });
        
        // フレームレートスライダー
        frameRateSlider.addEventListener('input', function() {
            const value = this.value;
            frameRateValue.textContent = `${value} FPS`;
            
            // 設定をサーバーに送信
            updateConfig('frame_rate', parseInt(value));
        });
        
        // 設定更新関数
        function updateConfig(key, value) {
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: key,
                    value: value
                })
            })
            .catch(error => console.error('設定更新エラー:', error));
        }
        
        // ステータス更新
        function updateStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // ステータス更新
                statusText.textContent = data.status;
                isProcessing = data.processing;
                doorbellButton.disabled = isProcessing;
                
                // 結果更新
                if (data.result) {
                    resultBox.textContent = data.result;
                }
            })
            .catch(error => {
                console.error('ステータス取得エラー:', error);
            });
        }
        
        // キーボードショートカット
        document.addEventListener('keydown', function(e) {
            // スペースキーで呼び鈴
            if (e.code === 'Space' && !isProcessing) {
                doorbellButton.click();
                e.preventDefault();
            }
        });
        
        // 設定値の初期表示
        fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            timeOffsetSlider.value = data.time_offset;
            timeOffsetValue.textContent = `${data.time_offset}秒`;
            
            qualitySlider.value = data.stream_quality;
            qualityValue.textContent = `${data.stream_quality}%`;
            
            frameRateSlider.value = data.frame_rate;
            frameRateValue.textContent = `${data.frame_rate} FPS`;
        })
        .catch(error => console.error('設定取得エラー:', error));
        
        // 定期的な状態更新
        updateStatus();
        setInterval(updateStatus, 1000);
    </script>
</body>
</html>
    """
    
    # 直接HTML文字列を返す
    return Response(html_content, content_type='text/html; charset=utf-8')

# ビデオフィード
@app.route('/video_feed')
def video_feed():
    """ビデオストリームのエンドポイント"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/doorbell', methods=['POST'])
def doorbell():
    """呼び鈴API"""
    global is_processing
    
    if is_processing:
        return jsonify({
            'success': False,
            'message': '別の処理が実行中です'
        })
    
    # 非同期で処理
    threading.Thread(target=process_doorbell, daemon=True).start()
    
    return jsonify({
        'success': True,
        'message': '分析を開始しました'
    })

@app.route('/api/status', methods=['GET'])
def status():
    """ステータスAPI"""
    global is_processing, last_result
    
    return jsonify({
        'status': '分析中...' if is_processing else '準備完了',
        'processing': is_processing,
        'result': last_result if last_result else None
    })

@app.route('/api/speak', methods=['POST'])
def speak():
    """テキスト読み上げAPI"""
    if not request.json or 'text' not in request.json:
        return jsonify({'success': False, 'error': 'テキストが指定されていません'}), 400
    
    text = request.json['text']
    success = speak_text(text)
    
    return jsonify({
        'success': success,
        'message': '音声出力を実行しました' if success else '音声出力に失敗しました'
    })

@app.route('/api/capture', methods=['POST'])
def capture():
    """現在の画像を保存"""
    global current_frame
    
    if current_frame is None:
        return jsonify({
            'success': False,
            'error': '画像がありません'
        })
    
    try:
        # 保存用ディレクトリ
        if not os.path.exists("captures"):
            os.makedirs("captures")
            
        # タイムスタンプ付きのファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captures/manual_{timestamp}.jpg"
        
        # 画像保存
        cv2.imwrite(filename, current_frame)
        
        return jsonify({
            'success': True,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """設定取得・更新API"""
    if request.method == 'GET':
        # 設定取得
        return jsonify({
            'time_offset': CONFIG["time_offset"],
            'stream_quality': CONFIG["stream_quality"],
            'frame_rate': CONFIG["frame_rate"]
        })
    else:
        # 設定更新
        if not request.json or 'key' not in request.json or 'value' not in request.json:
            return jsonify({'success': False, 'error': '設定キーと値が必要です'}), 400
            
        key = request.json['key']
        value = request.json['value']
        
        if key in ['time_offset', 'stream_quality', 'frame_rate']:
            CONFIG[key] = value
            
            # カメラのフレームレートを更新
            if key == 'frame_rate' and camera:
                camera.frame_rate = value
                
            logger.info(f"設定を更新しました: {key} = {value}")
            return jsonify({
                'success': True,
                'message': f"設定を更新しました: {key} = {value}"
            })
        else:
            return jsonify({
                'success': False,
                'error': f"不明な設定キー: {key}"
            }), 400

@app.route('/api/restart', methods=['POST'])
def restart():
    """システム再起動API"""
    global camera, stream_active
    
    try:
        # カメラとストリームを停止
        stream_active = False
        if camera and camera.is_running:
            camera.stop()
        
        # 再起動処理（非同期）
        def restart_process():
            time.sleep(1)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        
        threading.Thread(target=restart_process, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'システムを再起動しています...'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'再起動エラー: {str(e)}'
        }), 500

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """システム停止API"""
    global camera, stream_active
    
    try:
        # ストリームを停止
        stream_active = False
        
        # カメラを停止
        if camera and camera.is_running:
            camera.stop()
        
        # 停止メッセージ
        speak_text("システムを停止します。")
        
        return jsonify({
            'success': True,
            'message': 'システムを停止しました'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'停止エラー: {str(e)}'
        }), 500

# メイン処理
def main():
    """メイン関数"""
    global camera
    
    try:
        # カメラの初期化
        camera = RealtimeCamera(
            use_camera=CONFIG["use_camera"], 
            camera_id=CONFIG["camera_id"],
            frame_rate=CONFIG["frame_rate"]
        )
        
        if not camera.start():
            logger.error("カメラの初期化に失敗しました")
            return
        
        # フレームキャプチャスレッドの開始
        capture_thread = threading.Thread(target=frame_capture_thread, daemon=True)
        capture_thread.start()
        
        # 起動メッセージ
        logger.info("システムが起動しました")
        speak_text("玄関訪問者認識システムが起動しました。リアルタイム映像表示を開始します。")
        
        # Flaskサーバー起動
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("キーボード割り込みによりシステムを終了します")
    except Exception as e:
        logger.error(f"システム起動エラー: {e}")
    finally:
        # 終了処理
        global stream_active
        stream_active = False
        
        if camera and camera.is_running:
            camera.stop()
        logger.info("システムを終了しました")

if __name__ == "__main__":
    main()