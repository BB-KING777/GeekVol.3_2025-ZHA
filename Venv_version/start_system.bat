@echo off
chcp 65001 > nul
echo 訪問者認識システム起動中...
cd /d "%~dp0"

echo 仮想環境をアクティベート中...
call venv\Scripts\activate

echo システム開始...
python main.py web

echo.
echo システムが終了しました。何かキーを押してください...
pause > nul
