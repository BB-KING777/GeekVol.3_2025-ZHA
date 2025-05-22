#!/bin/bash

echo "=== YOLO統合玄関訪問者認識システム起動 ==="

# Ollamaサーバーをバックグラウンドで起動
echo "Ollamaサーバーを起動中..."
ollama serve &
OLLAMA_PID=$!

# Ollamaの起動を待機
echo "Ollamaサーバーの起動を待機中..."
sleep 10

# 必要なモデルをプル（存在しない場合）
echo "Ollamaモデルの確認..."
if ! ollama list | grep -q "gemma3:4b"; then
    echo "gemma3:4bモデルをダウンロード中..."
    ollama pull gemma3:4b
else
    echo "gemma3:4bモデルは既に存在します"
fi

# GPU使用設定
export OLLAMA_GPU_LAYERS=-1
export OLLAMA_GPU_MEMORY=8192

# CUDAパスの設定
export PATH="$PATH:/usr/local/cuda/bin"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/cuda/lib64"

# YOLOモデルディレクトリの確認
echo "YOLOモデルディレクトリの確認..."
if [ ! -d "/app/geek_cam/runs" ]; then
    echo "YOLOモデルディレクトリが見つかりません。サンプルディレクトリを作成します..."
    mkdir -p /app/geek_cam/runs/train_yolov11/face_identifier/weights
    echo "YOLOモデルを学習してください: python yolop1.py -> python yolop2.py"
fi

# Python環境のセットアップ
cd /app/geek/GeekVol.3_2025/GeekCam

# YOLOの基本モデルをダウンロード（存在しない場合）
if [ ! -f "model/yolo11n.pt" ]; then
    echo "YOLO基本モデルをダウンロード中..."
    mkdir -p model
    python3 -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); model.save('model/yolo11n.pt')"
fi

if [ ! -f "model/yolov11n-face.pt" ]; then
    echo "YOLO顔検出モデルをダウンロード中..."
    python3 -c "from ultralytics import YOLO; model = YOLO('yolov11n-face.pt'); model.save('model/yolov11n-face.pt')"
fi

echo "システム設定完了"
echo "=== 起動オプション ==="
echo "1. YOLO学習用データ作成: python yolop1.py"
echo "2. YOLO学習実行: python yolop2.py" 
echo "3. リアルタイム顔認識テスト: python yolop3.py"
echo "4. 統合システム起動: python app.py"
echo "========================"

# 統合システムを起動
echo "統合システムを起動中..."
python3 app.py

# 終了時の処理
echo "システムを終了中..."
if [ ! -z "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID
fi