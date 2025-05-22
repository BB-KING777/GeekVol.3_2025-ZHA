# ZHA
Assist By LLM
# YOLO統合玄関訪問者認識システム

視覚障害者や高齢者向けの玄関訪問者認識システムです。YOLOによる顔認識とOllamaによる詳細分析を組み合わせています。

## 🚀 主な機能

- **YOLO顔認識**: 事前に登録した人物を自動認識
- **Ollama詳細分析**: 未知の訪問者の特徴を詳細に説明（GPU加速）
- **音声案内**: 分析結果を音声で案内
- **リアルタイム映像**: Webブラウザでカメラ映像を確認
- **自動判定**: 知っている人→即座に案内、知らない人→詳細分析

## 📋 システム要件

- Docker + Docker Compose
- NVIDIA GPU (GPU加速用)
- Webカメラ
- Linux環境推奨

## 🔧 セットアップ

### 1. リポジトリクローン
```bash
git clone <このリポジトリ>
cd GeekCam
```

### 2. Docker環境構築
```bash
# Docker Composeでシステム起動
docker-compose up -d

# コンテナに入る
docker exec -it geek_cam_yolo_system bash
```

### 3. YOLOモデル学習（初回のみ）

#### 3-1. ユーザーデータ収集
```bash
# 顔データを収集（10秒間録画）
python yolo_training.py record --user_id user_001 --duration 10

# 複数ユーザーの場合
python yolo_training.py record --user_id user_002 --duration 10
```

#### 3-2. モデル学習
```bash
# YOLO学習実行（30エポック）
python yolo_training.py train --epochs 30

# より高精度にしたい場合
python yolo_training.py train --epochs 100
```

#### 3-3. テスト
```bash
# リアルタイム顔認識テスト
python yolo_training.py test
```

### 4. システム起動
```bash
# 統合システム起動
python app.py
```

## 🎯 使用方法

### Webインターフェース
ブラウザで `http://localhost:8080` にアクセス

- **呼び鈴ボタン**: 訪問者の確認を開始
- **リアルタイム映像**: カメラの現在の状況を確認
- **設定パネル**: システムパラメータの調整

### 動作フロー
1. 呼び鈴ボタンを押す
2. **YOLO判定**: 登録済みユーザーかチェック
   - **既知の人**: 「○○さんがいらっしゃいました」→終了
   - **未知の人**: 次のステップへ
3. **Ollama分析**: 詳細な人物分析を実行
   - 性別・年齢・服装・職業などを分析
   - 「未知の訪問者です。30代男性、黒いスーツ、ブリーフケース所持...」

## ⚙️ 設定

### config.py
```python
# YOLO設定
YOLO_MODEL_PATH = "runs/train_yolov11/face_identifier/weights/best.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.7
USE_FACE_DETECTION = True

# Ollama設定
API_BASE_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"
OLLAMA_GPU_LAYERS = -1  # GPU使用

# カメラ設定
USE_CAMERA = True
CAMERA_ID = "/dev/video0"
```

## 📂 ディレクトリ構造

```
GeekCam/
├── app.py                 # メインアプリケーション
├── face_detector.py       # YOLO顔認識モジュール
├── config.py             # システム設定
├── yolo_training.py      # YOLO学習統合スクリプト
├── model/               # 基本モデル
│   ├── yolo11n.pt
│   └── yolov11n-face.pt
├── runs/                # 学習済みモデル
│   └── face_identifier/
├── dataset/             # 学習用データセット
├── faces/              # 抽出した顔画像
└── captures/           # キャプチャ画像
```

## 🔍 トラブルシューティング

### YOLOモデルが見つからない
```bash
# モデル学習を実行
python yolo_training.py record --user_id your_name
python yolo_training.py train
```

### カメラが認識されない
```bash
# カメラデバイス確認
ls /dev/video*
# config.pyのCAMERA_IDを調整
```

### GPU使用できない
```bash
# NVIDIA Docker確認
nvidia-smi
docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Ollamaモデルエラー
```bash
# モデル再ダウンロード
ollama pull gemma3:4b
```

## 🎛️ APIエンドポイント

- `GET /` - Web UI
- `GET /video_feed` - カメラストリーム
- `POST /api/doorbell` - 呼び鈴処理
- `GET /api/status` - システム状態
- `POST /api/speak` - 音声出力
- `POST/GET /api/config` - 設定変更

## 🔄 システム更新

### 新しいユーザー追加
```bash
# 新ユーザーのデータ収集
python yolo_training.py record --user_id new_user --duration 15

# data.yamlに手動でユーザー追加後、再学習
python yolo_training.py train --epochs 50
```

### モデル精度向上
- より長時間の録画（`--duration 20`）
- より多くのエポック（`--epochs 100`）
- 異なる照明条件でのデータ収集

## 📊 パフォーマンス

- **YOLO認識**: ~50ms（GPU使用時）
- **Ollama分析**: ~3-5秒（GPU使用時）
- **総処理時間**: 既知ユーザー1秒未満、未知ユーザー5秒程度

## 🔒 プライバシー

- すべての処理はローカルで実行
- 顔データは暗号化されてローカル保存
- 外部への通信は行わない

## 🆘 サポート

問題が発生した場合：
1. ログの確認: `docker logs geek_cam_yolo_system`
2. システム再起動: `docker-compose restart`
3. 完全リセット: `docker-compose down && docker-compose up -d`