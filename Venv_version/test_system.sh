#!/bin/bash
echo "システムテスト実行中（Linux版）..."
cd "$(dirname "$0")"
source venv/bin/activate
python main.py test
echo "テスト完了。Enterキーを押してください..."
read
