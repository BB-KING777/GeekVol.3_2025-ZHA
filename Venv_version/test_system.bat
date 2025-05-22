@echo off
chcp 65001 > nul
echo システムテスト実行中...
cd /d "%~dp0"
call venv\Scripts\activate
python main.py test
pause
