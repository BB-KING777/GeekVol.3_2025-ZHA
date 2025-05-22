# 訪問者認識システム

視覚障害者・高齢者向けの AI powered 玄関訪問者認識システムです。

## 機能

- **リアルタイム映像監視**: Webカメラまたはテスト画像での動作
- **AI画像分析**: Ollama を使用した訪問者の特徴分析
- **顔認識**: MediaPipe/OpenCV による顔検出
- **音声出力**: OS標準またはpyttsx3による読み上げ
- **Webインターフェース**: ブラウザから操作可能

## 必要環境

- Python 3.8以上
- Ollama (AI分析用)
- Webカメラ (オプション)

## セットアップ

1. セットアップスクリプト実行:
   ```bash
   python setup.py
   ```

2. Ollama インストール・起動:
   ```bash
   # Ollama公式サイトからダウンロード・インストール
   ollama pull gemma3:4b
   ollama serve
   ```

## 使用方法

### Windows
```cmd
start_system.bat
```

### macOS/Linux  
```bash
./start_system.sh
```

### 手動起動
```bash
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
python web_app.py
```

ブラウザで http://localhost:8080 にアクセス

## 設定

`config.py` ファイルで各種設定を変更可能:

- カメラ設定
- API設定
- 音声設定
- 顔認識設定

## トラブルシューティング

### カメラが認識されない
- `config.py` の `CAMERA_ID` を変更 (0, 1, 2...)
- テスト画像モードに切り替え: `USE_CAMERA = False`

### 音声が出力されない
- OS標準音声の確認
- `config.py` の音声設定確認

### Ollama接続エラー
- Ollamaサービス起動確認: `ollama serve`
- モデル確認: `ollama list`

## ライセンス

MIT License
