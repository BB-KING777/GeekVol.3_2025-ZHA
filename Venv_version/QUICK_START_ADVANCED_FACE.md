# 高精度顔認識システム クイックスタートガイド

## 1. システムの起動

```bash
# システムテスト
python main.py test

# Webインターフェースで起動
python main.py web
```

## 2. 人物の登録

```bash
# 新しい人物を登録
python face_manager.py register

# 登録済み人物一覧表示
python face_manager.py list
```

## 3. 登録の手順

### 家族の登録例
1. `python face_manager.py register`
2. 人物ID: `family_dad`
3. 名前: `お父さん`
4. 関係性: `家族`
5. 備考: `お疲れ様です`
6. カメラで3枚の写真を撮影

### 配達員の登録例
1. `python face_manager.py register`
2. 人物ID: `delivery_yamato`
3. 名前: `ヤマト配達員`
4. 関係性: `配達員`
5. 備考: `いつものヤマト運輸の方`

## 4. 認識テスト

```bash
# リアルタイム認識テスト
python face_manager.py test
```

## 5. システムの利点

- **即座の認識**: 既知の人物は1-2秒で認識
- **Ollama不要**: 既知の人物にはAI分析を使わない
- **個別メッセージ**: 関係性に応じたカスタムメッセージ
- **認識履歴**: 誰がいつ来たかの記録

## 6. トラブルシューティング

### 顔認識精度が低い場合
- 明るい場所で正面を向いて登録
- 複数枚の写真で登録（推奨3-5枚）
- メガネ、帽子の有無を考慮

### 認識されない場合
- `python face_manager.py test` で確認
- 信頼度の閾値を調整
- 追加の写真で再登録

## 7. データ管理

```bash
# 認識統計表示
python face_manager.py stats

# データベースエクスポート
python face_manager.py export

# 人物削除
python face_manager.py delete
```
