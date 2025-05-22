# YOLO統合玄関訪問者認識システム用Dockerfile
FROM ollama-update:latest

# 基本パッケージのインストール
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-tk \
    libopencv-dev libasound2-dev libglib2.0-dev \
    espeak-ng libx11-dev libatlas-base-dev \
    build-essential cmake curl \
    # YOLO/GPU用追加パッケージ
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python依存パッケージのインストール
RUN pip3 install --upgrade pip 
RUN pip3 install numpy 
RUN pip3 install requests 
RUN pip3 install opencv-python
RUN pip3 install pyttsx3
RUN pip3 install flask

# YOLO関連パッケージ
RUN pip3 install ultralytics
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Ollama GPU設定用環境変数
ENV OLLAMA_GPU_LAYERS=-1
ENV OLLAMA_GPU_MEMORY=8192
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# 作業ディレクトリの設定
WORKDIR /app/geek_cam

# ポート開放
EXPOSE 8080
EXPOSE 11434

# 起動スクリプト
COPY start_system.sh /app/start_system.sh
RUN chmod +x /app/start_system.sh

# システム起動
CMD ["/app/start_system.sh"]