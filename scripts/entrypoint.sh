#!/bin/bash

set -e  # 如果腳本中的任何命令失敗，則退出腳本

echo "Starting entrypoint script..."

# 安裝 Poetry（如果尚未安裝）
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Installing Poetry..."
    pip install poetry
fi

# 配置 Poetry 虛擬環境位於項目內
echo "Configuring Poetry to use in-project virtual environments..."
poetry config virtualenvs.in-project true


# 安裝依賴
echo "Installing dependencies with Poetry..."
poetry install

# 啟動 Gunicorn 服務
echo "Starting Gunicorn server..."
exec poetry run gunicorn -w 3 -b 0.0.0.0:5000 app:app