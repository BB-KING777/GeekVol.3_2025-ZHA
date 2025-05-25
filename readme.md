# ZHA
Assist By LLM

<img src="https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat">  <img src="https://img.shields.io/badge/-Ubuntu-6F52B5.svg?logo=ubuntu&style=flat">  <img src="https://img.shields.io/badge/-Visual%20Studio%20Code-007ACC.svg?logo=visual-studio-code&style=flat">  <img src="https://img.shields.io/badge/技育CAMPハッカソン-ZHA-green.svg">　<img src="https://img.shields.io/badge/-Jetson%20Orin%20Nano-000000.svg?logo=nvidia&style=flat">　<img src="https://img.shields.io/badge/-Flask-000000.svg?logo=flask&style=flat">


# 玄関訪問者認識システム

視覚障害者および高齢者を対象とした、訪問者認識・説明支援システム。  
深層学習に基づく顔認識（ResNet50）と、画像理解を行う大規模言語モデル（Gemma3）を統合し、訪問者の識別・特徴把握・音声通知を自動化する。

## 問題定義
日本では、加齢に伴う視力の後天的低下が主な要因となり、視覚障害を抱える高齢者の数が年々増加している。
高齢化の進展が続く日本において、この傾向は今後さらに顕著になると見込まれている。
厚生労働省が公表した令和4年の統計によれば、視覚障害者全体のうち「70歳以上」の高齢者が占める割合は過半数に達しており、その人数は約16万人にのぼる。

こうした状況において、視覚障害者が日常生活の中で直面する困難のひとつが、「訪問者の識別」である。玄関先に現れた人物が誰であるかを把握することは、視覚障害者にとって容易ではなく、時に不安や危険を伴う。特に一人暮らしの高齢者にとって、訪問者の情報を瞬時に得る手段は限られている。　

ZHAは、このような課題に対処するために開発された、訪問者認識支援システムである。

## 主要機能

- **顔認識（既知識別）**: 事前に登録した人物を自動認識
- **人物特徴分析（未知識別）**: 未登録の訪問者に対して、年齢・服装・性別などを分析
- **音声案内**: 分析結果を音声で案内
- **リアルタイム映像**: Webブラウザでカメラ映像を確認
- **エッジ実装**: 全ての機微データをエッジで処理

## 環境構築

### 1. 必要要件
- Linux 環境（Ubuntu推奨）
- NVIDIA GPU
- Webカメラ
- スピーカ

### 2. セットアップ手順
- Gitクローン起動
- (option)ユーザーの顔データ収集とResNet学習によるユーザ登録
- アプリケーション起動

## 使用方法（利用者向け）

本システムはWebブラウザを通じて操作可能であり、以下の手順で利用する。

1. ブラウザで http://localhost:8080 にアクセスする。
2. 表示されるインターフェース上の **呼び鈴ボタン** を押すと、訪問者の認識処理が開始される。
3. 処理結果は **リアルタイム映像** と音声ガイドによって出力される。

### インターフェース構成

- **呼び鈴ボタン**  
  認識処理の開始トリガー。訪問者が来た際に押下する。

- **リアルタイム映像表示**  
  カメラから取得した映像を即時表示。

- **設定パネル**  
  閾値や使用モデル、カメラIDなどをGUIから変更可能。

---

## 動作フロー

1. **呼び鈴が押される**  
　ユーザーまたは訪問者がインターフェース上のボタンを押下する。

2. **顔認識処理を実行**  
　事前に登録された顔画像と照合し、訪問者が既知か未知かを判定する。

   - **既知の訪問者**  
     - 認識結果に基づき、「○○さんがいらっしゃいました」と音声出力。
     - 映像とともに識別結果がWeb UIに表示され、処理は終了する。

   - **未知の訪問者**  
     - 次のステップへ遷移。

3. **外見特徴分析処理を実行**  
　Gemma3を用いて、カメラ映像から以下のような特徴を抽出・要約する。

   - 性別・年齢推定
   - 服装の色や形状
   - 所持品や職業風の外観

4. **結果を音声で通知**  
　「未知の訪問者です。30代の男性、黒いスーツを着用、ブリーフケースを所持しています」といった形式で、リアルタイム音声通知を行う。

## ディレクトリ構造
   ```text
GeekCam/
├── Venv_version/                    # 仮想環境版（メインシステム）
│   ├── 設定・セットアップファイル
│   ├── config.py                    # システム設定（Linux用）
│   ├── config_emergency.py         # 緊急用設定（カメラ問題対応版）
│   ├── setup.py                    # 基本セットアップスクリプト
│   ├── windows_setup.py            # Windows専用セットアップ
│   ├── advanced_face_setup.py      # 高精度顔認識セットアップ
│   ├── linux_setup_fix.sh          # Linux環境修正スクリプト
│   │
│   ├── コアシステムファイル
│   ├── main.py                      # メインランチャー
│   ├── main_system.py               # メインシステム（高精度顔認識統合版）
│   ├── main_system_complete_fix.py  # 完全修正版メインシステム
│   ├── web_app.py                   # Webインターフェース（Flask）
│   │
│   ├── コアモジュール
│   ├── models.py                    # データモデル
│   ├── camera_module.py             # カメラ管理モジュール
│   ├── audio_module.py              # 音声出力モジュール
│   ├── api_client.py                # API通信モジュール（Ollama）
│   │
│   ├── 顔認識システム
│   ├── face_recognition_module_updated.py  # 顔認識モジュール（統合版）
│   ├── face_recognition_advanced.py        # 高精度顔認識システム
│   ├── face_manager.py              # 顔認識管理ツール
│   │
│   ├── ユーティリティ・修正ツール
│   ├── fix_compatibility.py        # NumPy/OpenCV 互換性修正
│   ├── debug_camera_fix.py         # カメラ問題診断・修正
│   ├── debug_analize.py            # フレーム取得問題診断
│   ├── apply_fixes.py              # 修正版ファイル適用スクリプト
│   │
│   ├── 依存関係管理
│   ├── requirements.txt            # 基本依存関係
│   ├── requirements_fixed.txt      # 互換性修正版
│   ├── requirements_advanced_face.txt  # 高精度顔認識用
│   │
│   ├── 起動スクリプト
│   ├── start_system.bat           # Windows用起動スクリプト
│   ├── start_system.sh            # Linux用起動スクリプト
│   ├── test_system.bat            # Windows用テストスクリプト
│   ├── test_system.sh             # Linux用テストスクリプト
│   │
│   ├── ドキュメント
│   ├── README.md                   # 具体的な使用方法
│   ├── QUICK_START_ADVANCED_FACE.md  # 高精度顔認識ガイド
│   │
│   ├── データディレクトリ（自動生成）
│   ├── data/
│   │   ├── captures/               # 分析結果画像保存
│   │   ├── test_images/            # テスト用画像
│   │   ├── logs/                   # システムログファイル
│   │   ├── registration_photos/    # 登録用写真
│   │   │   └── [person_id]/        # 人物別フォルダ
│   │   ├── registration_videos/    # 登録用動画
│   │   │   └── [person_id]/        # 人物別フォルダ
│   │   ├── face_database.db        # SQLite顔認識データベース
│   │   ├── face_encodings.pkl      # 顔エンコーディングファイル
│   │   └── known_faces.json        # 既知の顔データ（下位互換）
│   │
│   ├── 仮想環境（自動生成）
│   ├── venv/                       # Python仮想環境
│   │   ├── Scripts/                # Windows用実行ファイル
│   │   │   ├── python.exe
│   │   │   ├── pip.exe
│   │   │   └── activate.bat
│   │   ├── bin/                    # Linux/macOS用実行ファイル
│   │   │   ├── python
│   │   │   ├── pip
│   │   │   └── activate
│   │   └── Lib/                    # インストールされたライブラリ
│   │
│   └── バックアップ（自動生成）
│       └── backup_[timestamp]/     # ファイル修正時のバックアップ
│
├── プロジェクトルートファイル
└── readme.md                       # 全体像
   ```

## プライバシー

- すべての処理はローカルで実行
- 顔データは暗号化されてローカル保存
- 外部への通信は行わない
