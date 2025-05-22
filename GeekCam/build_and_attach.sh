#!/bin/bash
set -e

SERVICE_NAME="geek_cam_yolo"  # docker-compose.yaml の services: 名前
PROJECT_NAME="geekcam"  # docker-compose -p で指定するプロジェクト名
# composeの仕様
CONTAINER_NAME="${PROJECT_NAME}-${SERVICE_NAME}-1"

# 🔥 最初にsudo権限を取得しておく（パスワードを最初だけ聞く）
echo "🛡️ Requesting sudo permission..."
sudo -v

# 🖥 X11のローカルアクセスを許可
echo "🪟 Granting X11 access to local Docker container..."
echo "🚨Check what you are doing on the Jetson display!!!"
xhost +local:

# ⬇️ スクリプト終了時にコンテナを停止・削除するtrapをセット
trap 'echo "🛑 Cleaning up: Stopping and removing container..."; sudo docker stop "$CONTAINER_NAME"; sudo docker rm "$CONTAINER_NAME"' EXIT

# 🔵 Docker-compose up (プロジェクト名固定)
echo "🔵 Building and starting containers with docker-compose..."
sudo docker compose -p "$PROJECT_NAME" up --build -d

# 🔄 コンテナが起動するまで待機
echo "🔄 Waiting for container to be running..."
for i in {1..30}; do
    STATUS=$(sudo docker inspect -f "{{.State.Running}}" "$CONTAINER_NAME" 2>/dev/null || echo "false")
    if [ "$STATUS" = "true" ]; then
        echo "✅ Container is running!"
        break
    fi
    sleep 2
done

# 🟢 bashで接続
echo "🟢 Connecting to container: $CONTAINER_NAME"
if sudo docker exec -it "$CONTAINER_NAME" /bin/bash; then
    echo "📤 Exited container shell (you are now back on the host)."
fi 