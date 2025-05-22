# sudo docker buildx build -t zha_ollama:latest .
# YOLO統合玄関訪問者認識システム用Dockerfile
FROM dustynv/ollama:r36.2.0

# 基本パッケージのインストール
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-tk \
    libopencv-dev libasound2-dev libglib2.0-dev \
    espeak-ng libx11-dev libatlas-base-dev \
    build-essential cmake curl \
    # YOLO/GPU用追加パッケージ
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# sudo with no password
RUN apt-get update && apt-get install -y \
    openssh-server sudo curl libssl-dev libglfw3-dev    
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers


# Python依存パッケージのインストール
RUN pip3 install --upgrade pip 
RUN pip3 install numpy 
RUN pip3 install requests 
RUN pip3 install opencv-python
RUN pip3 install pyttsx3
# error回避
RUN pip3 install --ignore-installed flask

# YOLO関連パッケージ
RUN pip3 install ultralytics
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Ollama GPU設定用環境変数
ENV OLLAMA_GPU_LAYERS=-1
ENV OLLAMA_GPU_MEMORY=8192
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# cudaパスを事前に通す
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# 作業ディレクトリの設定
WORKDIR /app/

# ポート開放
EXPOSE 8080
EXPOSE 11434

# 起動スクリプト
COPY start_system.sh /app/start_system.sh
RUN chmod +x /app/start_system.sh

# システム起動
CMD ["/app/start_system.sh"]