"""
YOLO顔認識学習統合スクリプト
使用方法:
1. python yolo_training.py record --user_id user_001 --duration 10
2. python yolo_training.py train --epochs 50
3. python yolo_training.py test
"""

import os
import cv2
import time
import glob
import shutil
import argparse
from ultralytics import YOLO

class YOLOFaceTrainer:
    def __init__(self):
        self.base_dir = "."
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.frames_dir = os.path.join(self.base_dir, "frames")
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.faces_dir = os.path.join(self.base_dir, "faces")
        self.model_dir = os.path.join(self.base_dir, "model")
        self.runs_dir = os.path.join(self.base_dir, "runs")
        
        # ディレクトリ作成
        for dir_path in [self.temp_dir, self.frames_dir, self.dataset_dir, 
                        self.faces_dir, self.model_dir, self.runs_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def record_video(self, user_id: str, duration: int = 10, width: int = 640, 
                    height: int = 480, fps: int = 30):
        """動画録画"""
        print(f"[INFO] {user_id}の動画録画を開始します（{duration}秒間）")
        
        output_path = os.path.join(self.temp_dir, f"{user_id}_video.mp4")
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        if not cap.isOpened():
            raise RuntimeError("カメラにアクセスできません")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        print("エンターキーを押して録画を開始してください...")
        input()
        
        print(f"録画開始！{duration}秒間カメラを見てください")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 残り時間を表示
            remaining = int(duration - (time.time() - start_time))
            cv2.putText(frame, f"Recording... {remaining}s", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            out.write(frame)
            cv2.imshow('Recording', frame)
            cv2.waitKey(1)

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        print(f"[INFO] 録画完了: {output_path}")
        return output_path
    
    def extract_frames(self, video_path: str, user_id: str, interval: int = 5):
        """フレーム抽出"""
        print(f"[INFO] フレーム抽出中: {video_path}")
        
        user_frames_dir = os.path.join(self.frames_dir, user_id)
        os.makedirs(user_frames_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        frame_id, saved_count = 0, 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_id % interval == 0:
                filename = os.path.join(user_frames_dir, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(filename, frame)
                saved_count += 1
            
            frame_id += 1
        
        cap.release()
        print(f"[INFO] {saved_count}フレームを抽出: {user_frames_dir}")
        return user_frames_dir
    
    def detect_faces(self, image_path, model, conf_threshold=0.5):
        """顔検出"""
        results = model(image_path, verbose=False)[0]
        faces = []
        
        for box, conf in zip(results.boxes.xyxy, results.boxes.conf):
            if conf < conf_threshold:
                continue
            x1, y1, x2, y2 = map(int, box.tolist())
            faces.append({"bbox": [x1, y1, x2, y2], "confidence": float(conf)})
        
        # 信頼度でソートして最も良い顔を返す
        faces.sort(key=lambda x: x["confidence"], reverse=True)
        return faces[:1]  # 最も信頼度の高い顔のみ
    
    def save_cropped_face(self, image, bbox, save_path, confidence=None):
        """顔画像の保存"""
        x1, y1, x2, y2 = bbox
        face = image[y1:y2, x1:x2].copy()
        
        if confidence:
            label = f"conf: {confidence:.3f}"
            cv2.putText(face, label, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imwrite(save_path, face)
    
    def save_yolo_annotation(self, bbox, image_size, class_id, save_path):
        """YOLO形式のアノテーション保存"""
        x1, y1, x2, y2 = bbox
        h, w = image_size
        
        x_center = ((x1 + x2) / 2) / w
        y_center = ((y1 + y2) / 2) / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        
        with open(save_path, "w") as f:
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}\n")
    
    def process_user_data(self, user_id: str, class_id: int):
        """ユーザーデータの処理"""
        print(f"[INFO] {user_id}のデータ処理を開始")
        
        # 顔検出モデルの読み込み
        face_model_path = os.path.join(self.model_dir, "yolov11n-face.pt")
        if not os.path.exists(face_model_path):
            print("顔検出モデルをダウンロード中...")
            face_model = YOLO("yolov11n-face.pt")
            face_model.save(face_model_path)
        else:
            face_model = YOLO(face_model_path)
        
        # ディレクトリ設定
        user_frames_dir = os.path.join(self.frames_dir, user_id)
        img_out_dir = os.path.join(self.dataset_dir, "images", "train")
        lbl_out_dir = os.path.join(self.dataset_dir, "labels", "train")
        cropped_dir = os.path.join(self.faces_dir, user_id)
        
        for dir_path in [img_out_dir, lbl_out_dir, cropped_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # フレーム処理
        processed_count = 0
        for idx, path in enumerate(sorted(glob.glob(os.path.join(user_frames_dir, '*.jpg')))):
            img = cv2.imread(path)
            h, w = img.shape[:2]
            
            faces = self.detect_faces(path, face_model)
            if not faces:
                continue
            
            bbox = faces[0]["bbox"]
            conf = faces[0]["confidence"]
            base = f"{user_id}_{idx:04d}_face0"
            
            # 保存パス
            face_path = os.path.join(img_out_dir, f"{base}.jpg")
            anno_path = os.path.join(lbl_out_dir, f"{base}.txt")
            cropped_path = os.path.join(cropped_dir, f"{base}.jpg")
            
            # 保存実行
            self.save_cropped_face(img, bbox, cropped_path, confidence=conf)
            shutil.copy(path, face_path)
            self.save_yolo_annotation(bbox, (h, w), class_id, anno_path)
            
            processed_count += 1
        
        print(f"[INFO] {processed_count}枚の顔画像を処理しました")
        return processed_count
    
    def write_data_yaml(self, usernames):
        """data.yaml作成"""
        yaml_path = os.path.join(self.dataset_dir, "data.yaml")
        
        with open(yaml_path, "w") as f:
            f.write("path: dataset\n")
            f.write("train: images/train\n")
            f.write("val: images/train\n\n")
            f.write("names:\n")
            for i, name in enumerate(usernames):
                f.write(f"  {i}: {name}\n")
        
        print(f"[INFO] data.yaml作成完了: {yaml_path}")
        return yaml_path
    
    def train_model(self, epochs=30, batch_size=8):
        """モデル学習"""
        print(f"[INFO] YOLO学習開始 (epochs={epochs})")
        
        # 基本モデルの準備
        base_model_path = os.path.join(self.model_dir, "yolo11n.pt")
        if not os.path.exists(base_model_path):
            print("基本モデルをダウンロード中...")
            model = YOLO("yolo11n.pt")
            model.save(base_model_path)
        else:
            model = YOLO(base_model_path)
        
        # 学習実行
        results = model.train(
            data=os.path.join(self.dataset_dir, "data.yaml"),
            epochs=epochs,
            imgsz=640,
            batch=batch_size,
            name="face_identifier",
            project=self.runs_dir
        )
        
        print("[INFO] 学習完了")
        return results
    
    def test_realtime(self, conf_threshold=0.7):
        """リアルタイムテスト"""
        # 学習済みモデルを探す
        model_path = os.path.join(self.runs_dir, "face_identifier", "weights", "best.pt")
        if not os.path.exists(model_path):
            # 最新の学習結果を探す
            train_dirs = glob.glob(os.path.join(self.runs_dir, "face_identifier*"))
            if train_dirs:
                latest_dir = max(train_dirs, key=os.path.getmtime)
                model_path = os.path.join(latest_dir, "weights", "best.pt")
        
        if not os.path.exists(model_path):
            print("学習済みモデルが見つかりません。先に学習を実行してください。")
            return
        
        print(f"[INFO] モデル読み込み: {model_path}")
        model = YOLO(model_path)
        class_names = model.names
        
        print("[INFO] リアルタイム顔認識開始 (qキーで終了)")
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 推論実行
            results = model(frame, verbose=False)[0]
            
            # 結果描画
            for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
                if conf < conf_threshold:
                    continue
                
                x1, y1, x2, y2 = map(int, box.tolist())
                class_id = int(cls.item())
                label = class_names.get(class_id, f"class_{class_id}")
                text = f"{label} ({conf:.2f})"
                
                # 描画
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, text, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow("YOLO Face Recognition Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="YOLO顔認識学習システム")
    parser.add_argument("command", choices=["record", "train", "test"], 
                       help="実行するコマンド")
    parser.add_argument("--user_id", default="user_001", help="ユーザーID")
    parser.add_argument("--duration", type=int, default=10, help="録画時間（秒）")
    parser.add_argument("--epochs", type=int, default=30, help="学習エポック数")
    parser.add_argument("--batch_size", type=int, default=8, help="バッチサイズ")
    
    args = parser.parse_args()
    trainer = YOLOFaceTrainer()
    
    if args.command == "record":
        print(f"=== {args.user_id}のデータ収集 ===")
        
        # 動画録画
        video_path = trainer.record_video(args.user_id, args.duration)
        
        # フレーム抽出
        frames_dir = trainer.extract_frames(video_path, args.user_id)
        
        # データ処理
        trainer.process_user_data(args.user_id, class_id=0)
        
        # data.yaml更新
        trainer.write_data_yaml([args.user_id])
        
        print("データ収集完了！次に学習を実行してください: python yolo_training.py train")
    
    elif args.command == "train":
        print("=== YOLO学習実行 ===")
        trainer.train_model(epochs=args.epochs, batch_size=args.batch_size)
        print("学習完了！テストを実行してください: python yolo_training.py test")
    
    elif args.command == "test":
        print("=== リアルタイムテスト ===")
        trainer.test_realtime()

if __name__ == "__main__":
    main()