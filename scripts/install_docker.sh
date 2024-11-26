#!/bin/bash

# 更新系統並安裝必要依賴
sudo apt-get update
sudo apt-get install -y ca-certificates curl

# 添加 Docker 官方 GPG 密鑰
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 添加 Docker 軟件源到 APT
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新 APT 緩存
sudo apt-get update

# 安裝最新版本的 Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 檢查 Docker 安裝狀態
sudo docker --version
sudo docker compose version

echo "Docker installation is complete!"

sudo systemctl enable docker.service

cd $(dirname $(dirname $(realpath $0)))
chmod +x ./scripts/entrypoint.sh

echo "Building Docker image..."
sudo docker build -t science-video-ocr-api .

# 停止並刪除可能已運行的舊容器
echo "Stopping and removing any existing containers..."
sudo docker stop science-video-ocr-api || true
sudo docker rm science-video-ocr-api || true

# 運行 Docker 容器
echo "Running Docker container..."
sudo docker run -d \
  --name science-video-ocr-api \
  -p 5000:5000 \
  -v $(pwd):/app \
  science-video-ocr-api --bind 0.0.0.0

echo "Docker container is running at http://localhost:5000"

sudo docker update --restart=always science-video-ocr-api