"""
顔認識管理ツール - 修正版（Windows対応）
"""
import argparse
import sys
from pathlib import Path
import json
import cv2
import time
import threading
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

import config


def calculate_blur_score(image: np.ndarray) -> float:
    """画像のブレ（ぼかし）スコアを計算（ラプラシアン分散）"""
    try:
        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # ラプラシアンフィルタでエッジ検出
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # 分散を計算（高いほど鮮明）
        blur_score = laplacian.var()
        
        return blur_score
    except Exception as e:
        print(f"ブレスコア計算エラー: {e}")
        return 0.0

def calculate_brightness_score(image: np.ndarray) -> float:
    """画像の明るさスコアを計算"""
    try:
        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 平均明度を計算
        brightness = np.mean(gray)
        
        return brightness
    except Exception as e:
        print(f"明るさスコア計算エラー: {e}")
        return 0.0

def detect_face_quality(image: np.ndarray) -> Tuple[bool, float, tuple]:
    """顔の品質を評価（顔検出 + サイズチェック）"""
    try:
        # OpenCVの顔検出器を使用
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 顔検出
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)  # 最小顔サイズ
        )
        
        if len(faces) == 1:
            # 1つの顔が検出された場合
            x, y, w, h = faces[0]
            face_area = w * h
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area
            
            return True, face_ratio, (x, y, w, h)
        elif len(faces) > 1:
            # 複数の顔が検出された場合
            return False, 0.0, None
        else:
            # 顔が検出されない場合
            return False, 0.0, None
            
    except Exception as e:
        print(f"顔品質検出エラー: {e}")
        return False, 0.0, None

def record_video_for_registration(person_id: str, name: str, duration: int = 10) -> str:
    """登録用動画を撮影"""
    print(f"\n{name}さんの動画を{duration}秒間撮影します。")
    print("撮影中は以下を心がけてください：")
    print("1. カメラを正面に向けて座る")
    print("2. ゆっくりと左右に顔を向ける")
    print("3. 上下にも少し顔を動かす")
    print("4. 途中で笑顔も作ってください")
    print("\n操作方法:")
    print("- Enterキー: 撮影開始")
    print("- Escキー: キャンセル")
    
    videos_dir = config.DATA_DIR / "registration_videos" / person_id
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # カメラ初期化（Windows対応）
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not camera.isOpened():
        print("❌ カメラを開けませんでした")
        return None
    
    # カメラ設定
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    
    # 動画ファイルパス
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = videos_dir / f"{person_id}_{timestamp}.avi"
    
    # 動画書き込み設定
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
    
    print(f"\n📹 カメラを起動しました。Enterキーで撮影開始...")
    
    # 撮影準備画面
    recording = False
    start_time = None
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                print("❌ フレームの取得に失敗しました")
                break
            
            # フレームを左右反転（鏡像表示）
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            
            # 撮影状態に応じた表示
            if not recording:
                # 撮影前
                cv2.putText(display_frame, f"Person: {name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(display_frame, "Press ENTER to start recording", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, "ESC: Cancel", 
                           (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            else:
                # 撮影中
                elapsed = time.time() - start_time
                remaining = max(0, duration - elapsed)
                
                # 録画中表示
                cv2.circle(display_frame, (30, 30), 15, (0, 0, 255), -1)  # 赤い録画インジケータ
                cv2.putText(display_frame, "RECORDING", 
                           (60, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # 残り時間表示
                cv2.putText(display_frame, f"Time: {remaining:.1f}s", 
                           (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # プログレスバー
                progress_width = int((elapsed / duration) * 620)
                cv2.rectangle(display_frame, (10, 100), (630, 120), (100, 100, 100), 2)
                cv2.rectangle(display_frame, (10, 100), (10 + progress_width, 120), (0, 255, 0), -1)
                
                # 撮影ガイド
                phase = int(elapsed) % 6
                guides = [
                    "Look straight ahead",
                    "Turn slightly left", 
                    "Turn slightly right",
                    "Look up a little",
                    "Look down a little",
                    "Smile!"
                ]
                cv2.putText(display_frame, guides[phase], 
                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                # 動画に書き込み（反転しない元のフレーム）
                original_frame = cv2.flip(frame, 1)  # 2回反転で元に戻す
                out.write(original_frame)
                
                # 時間終了チェック
                if elapsed >= duration:
                    print(f"✅ {duration}秒間の撮影が完了しました")
                    break
            
            # 中央に撮影エリアを表示
            h, w = display_frame.shape[:2]
            cv2.rectangle(display_frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
            
            cv2.imshow(f'Video Registration - {name}', display_frame)
            
            # キー入力処理
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13:  # Enterキー
                if not recording:
                    recording = True
                    start_time = time.time()
                    print(f"📹 撮影開始: {duration}秒間")
                
            elif key == 27:  # Escapeキー
                print("❌ 撮影をキャンセルしました")
                video_path = None
                break
    
    except KeyboardInterrupt:
        print("❌ 撮影が中断されました")
        video_path = None
    
    finally:
        camera.release()
        out.release()
        cv2.destroyAllWindows()
        print("📷 カメラを停止しました")
    
    return str(video_path) if video_path and video_path.exists() else None

def extract_best_frames_from_video(video_path: str, person_id: str, target_count: int = 5) -> List[str]:
    """動画から最適なフレームを抽出"""
    print(f"\n📊 動画から最適なフレームを抽出中...")
    print("評価基準: ブレ、明るさ、顔サイズ、顔の向き")
    
    # 出力ディレクトリ
    frames_dir = config.DATA_DIR / "registration_photos" / person_id
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 動画ファイルを開けませんでした: {video_path}")
        return []
    
    # 動画情報取得
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"動画情報: {total_frames}フレーム, {fps:.1f}FPS, {duration:.1f}秒")
    
    # フレーム評価結果を保存
    frame_evaluations = []
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 5フレームに1回評価（処理速度向上）
        if frame_count % 5 == 0:
            # 各種品質スコアを計算
            blur_score = calculate_blur_score(frame)
            brightness_score = calculate_brightness_score(frame)
            has_face, face_ratio, face_bbox = detect_face_quality(frame)
            
            # 品質評価
            quality_score = 0.0
            
            if has_face:
                # ブレスコア（高いほど良い）- 正規化
                blur_normalized = min(blur_score / 500.0, 1.0)  # 500以上で満点
                
                # 明るさスコア（70-180が最適）
                brightness_normalized = 1.0 - abs(brightness_score - 125) / 125.0
                brightness_normalized = max(0.0, brightness_normalized)
                
                # 顔サイズスコア（0.1-0.4が最適）
                face_size_normalized = 1.0
                if face_ratio < 0.05:  # 顔が小さすぎる
                    face_size_normalized = face_ratio / 0.05
                elif face_ratio > 0.5:  # 顔が大きすぎる
                    face_size_normalized = max(0.0, 1.0 - (face_ratio - 0.5) / 0.5)
                
                # 総合品質スコア計算
                quality_score = (
                    blur_normalized * 0.4 +      # ブレが最重要
                    brightness_normalized * 0.3 + # 明るさ重要
                    face_size_normalized * 0.3    # 顔サイズ重要
                )
                
                # デバッグ情報（詳細版は一部のフレームのみ表示）
                if frame_count % 50 == 0:
                    print(f"フレーム {frame_count}: ブレ={blur_score:.1f}, 明るさ={brightness_score:.1f}, "
                          f"顔比率={face_ratio:.3f}, 品質={quality_score:.3f}")
            
            # 評価結果を保存
            frame_evaluations.append({
                'frame_number': frame_count,
                'timestamp': frame_count / fps if fps > 0 else 0,
                'quality_score': quality_score,
                'blur_score': blur_score,
                'brightness_score': brightness_score,
                'has_face': has_face,
                'face_ratio': face_ratio,
                'face_bbox': face_bbox,
                'frame': frame.copy()  # フレーム画像も保存
            })
        
        frame_count += 1
        
        # 進捗表示
        if frame_count % 100 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"処理進捗: {progress:.1f}% ({frame_count}/{total_frames})")
    
    cap.release()
    
    print(f"✅ {len(frame_evaluations)}フレームを評価しました")
    
    # 品質スコアでソート（高い順）
    frame_evaluations.sort(key=lambda x: x['quality_score'], reverse=True)
    
    # 上位フレームを選択（時間的に分散させる）
    selected_frames = []
    selected_timestamps = []
    min_time_gap = duration / (target_count * 2)  # 最小時間間隔
    
    for eval_data in frame_evaluations:
        if len(selected_frames) >= target_count:
            break
        
        timestamp = eval_data['timestamp']
        
        # 既選択フレームと時間的に十分離れているかチェック
        too_close = False
        for selected_time in selected_timestamps:
            if abs(timestamp - selected_time) < min_time_gap:
                too_close = True
                break
        
        if not too_close and eval_data['quality_score'] > 0.3:  # 最低品質閾値
            selected_frames.append(eval_data)
            selected_timestamps.append(timestamp)
    
    # フレームを画像ファイルとして保存
    saved_paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i, eval_data in enumerate(selected_frames):
        filename = f"{person_id}_{timestamp}_frame_{i+1}_q{eval_data['quality_score']:.2f}.jpg"
        filepath = frames_dir / filename
        
        cv2.imwrite(str(filepath), eval_data['frame'])
        saved_paths.append(str(filepath))
        
        print(f"✅ 保存: {filename} (品質: {eval_data['quality_score']:.3f}, "
              f"時刻: {eval_data['timestamp']:.1f}s)")
    
    # 評価統計を表示
    if frame_evaluations:
        all_scores = [e['quality_score'] for e in frame_evaluations]
        selected_scores = [e['quality_score'] for e in selected_frames]
        
        print(f"\n📈 評価統計:")
        print(f"全フレーム品質: 最大={max(all_scores):.3f}, 平均={np.mean(all_scores):.3f}, 最小={min(all_scores):.3f}")
        if selected_scores:
            print(f"選択フレーム品質: 最大={max(selected_scores):.3f}, 平均={np.mean(selected_scores):.3f}, 最小={min(selected_scores):.3f}")
        print(f"選択フレーム数: {len(selected_frames)}/{target_count}")
    
    return saved_paths

def register_person_with_video():
    """動画撮影による人物登録"""
    print("\n" + "="*60)
    print(" 動画撮影による人物登録")
    print("="*60)
    
    # 基本情報入力
    person_id = input("人物ID（英数字、例：family_dad）: ").strip()
    if not person_id:
        print("❌ 人物IDは必須です")
        return
    
    if not person_id.replace('_', '').isalnum():
        print("❌ 人物IDは英数字とアンダースコア(_)のみ使用可能です")
        return
    
    name = input("名前: ").strip()
    if not name:
        print("❌ 名前は必須です")
        return
    
    relationship = input("関係性（例：家族、友人、配達員）: ").strip()
    notes = input("備考（例：いつもの郵便屋さん）: ").strip()
    
    print(f"\n登録情報:")
    print(f"ID: {person_id}")
    print(f"名前: {name}")
    print(f"関係性: {relationship}")
    print(f"備考: {notes}")
    
    confirm = input("\nこの情報で登録しますか？ (y/N): ").lower()
    if confirm not in ['y', 'yes']:
        print("❌ 登録をキャンセルしました")
        return
    
    # 撮影設定
    print("\n📹 動画撮影設定:")
    duration_input = input("撮影時間（秒、デフォルト10秒）: ").strip()
    try:
        duration = int(duration_input) if duration_input else 10
        duration = max(5, min(60, duration))  # 5-60秒の範囲
    except ValueError:
        duration = 10
    
    frame_count_input = input("抽出フレーム数（デフォルト5枚）: ").strip()
    try:
        frame_count = int(frame_count_input) if frame_count_input else 5
        frame_count = max(3, min(20, frame_count))  # 3-20枚の範囲
    except ValueError:
        frame_count = 5
    
    print(f"\n設定: {duration}秒撮影, {frame_count}枚抽出")
    
    # 動画撮影
    print("\n📸 動画撮影を開始します...")
    print("注意: 他のアプリケーションでカメラを使用している場合は先に終了してください")
    
    ready = input("準備ができたらEnterキーを押してください...")
    
    video_path = record_video_for_registration(person_id, name, duration)
    
    if not video_path:
        print("❌ 動画撮影に失敗しました")
        return
    
    print(f"✅ 動画撮影完了: {Path(video_path).name}")
    
    # フレーム抽出
    photo_paths = extract_best_frames_from_video(video_path, person_id, frame_count)
    
    if not photo_paths:
        print("❌ フレーム抽出に失敗しました")
        return
    
    print(f"✅ {len(photo_paths)}枚のフレームを抽出しました")
    
    # 顔認識システムで登録
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            print("インストール: pip install face-recognition")
            return
        
        print(f"\n📊 {len(photo_paths)}枚の画像から顔エンコーディングを抽出中...")
        
        success = recognizer.register_person(
            person_id=person_id,
            name=name,
            image_paths=photo_paths,
            relationship=relationship,
            notes=notes
        )
        
        if success:
            print(f"🎉 {name}さんの登録が完了しました！")
            print(f"人物ID: {person_id}")
            print(f"登録画像数: {len(photo_paths)}枚")
            print(f"関係性: {relationship}")
            print(f"動画ファイル: {Path(video_path).name}")
            
            # 動画ファイルを削除するかユーザーに確認
            delete_video = input("\n元の動画ファイルを削除しますか？ (Y/n): ").lower()
            if delete_video in ['', 'y', 'yes']:
                try:
                    Path(video_path).unlink()
                    print("✅ 動画ファイルを削除しました")
                except Exception as e:
                    print(f"⚠ 動画ファイル削除エラー: {e}")
            
            # 登録テスト
            test_choice = input("\n登録した人物の認識テストを実行しますか？ (y/N): ").lower()
            if test_choice in ['y', 'yes']:
                test_recognition_for_person(person_id, name)
                
        else:
            print("❌ 登録に失敗しました")
            print("抽出したフレームに顔が明確に写っているか確認してください")
            
    except ImportError:
        print("❌ face_recognition ライブラリがインストールされていません")
        print("インストール方法:")
        print("1. pip install face-recognition")
        print("2. または: python advanced_face_setup.py")
        
    except Exception as e:
        print(f"❌ 登録中にエラーが発生しました: {e}")


def take_photo_for_registration(person_id: str, name: str, count: int = 3) -> list:
    """登録用の写真を撮影（修正版）"""
    print(f"\n{name}さんの写真を{count}枚撮影します。")
    print("カメラの前に座って、以下のポーズをとってください：")
    print("1. 正面を向いて")
    print("2. 少し左を向いて")
    print("3. 少し右を向いて")
    print("\n操作方法:")
    print("- スペースキー: 撮影")
    print("- Escキー: キャンセル")
    print("- qキー: 終了")
    
    photos_dir = config.DATA_DIR / "registration_photos" / person_id
    photos_dir.mkdir(parents=True, exist_ok=True)
    
    # カメラ初期化（Windows対応）
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow使用
    
    if not camera.isOpened():
        print("❌ カメラを開けませんでした")
        print("他のアプリケーションがカメラを使用していないか確認してください")
        return []
    
    # カメラ設定
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    
    photo_paths = []
    current_photo = 0
    
    print(f"\n📸 カメラを起動しました。写真 {current_photo + 1}/{count} の準備をしてください...")
    
    # 少し待機してカメラを安定化
    time.sleep(2)
    
    try:
        while current_photo < count:
            ret, frame = camera.read()
            if not ret:
                print("❌ フレームの取得に失敗しました")
                break
            
            # フレームを左右反転（鏡像表示）
            frame = cv2.flip(frame, 1)
            
            # 撮影ガイド表示
            cv2.putText(frame, f"Photo {current_photo + 1}/{count}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Person: {name}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # 操作説明
            cv2.putText(frame, "SPACE: Take Photo, ESC: Cancel, Q: Quit", 
                       (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # 撮影ポーズのガイド
            pose_guides = ["Face forward", "Turn slightly left", "Turn slightly right"]
            if current_photo < len(pose_guides):
                cv2.putText(frame, pose_guides[current_photo], 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 中央に撮影枠を表示
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
            cv2.putText(frame, "Face area", (w//4, h//4 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow(f'Registration - {name}', frame)
            
            # キー入力処理（修正版）
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # スペースキー
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                photo_path = photos_dir / f"{person_id}_{timestamp}_{current_photo + 1}.jpg"
                
                # 撮影時は反転しない元のフレームを保存
                original_frame = cv2.flip(frame, 1)  # 2回反転で元に戻す
                cv2.imwrite(str(photo_path), original_frame)
                photo_paths.append(str(photo_path))
                
                print(f"✅ 撮影完了 {current_photo + 1}/{count}: {photo_path.name}")
                current_photo += 1
                
                if current_photo < count:
                    print(f"📸 次の写真 {current_photo + 1}/{count} の準備をしてください...")
                
                # 撮影後少し待機
                time.sleep(1)
                
            elif key == 27:  # Escapeキー
                print("❌ 撮影をキャンセルしました")
                break
                
            elif key == ord('q') or key == ord('Q'):  # qキー
                print("❌ 撮影を終了しました")
                break
    
    except KeyboardInterrupt:
        print("❌ 撮影が中断されました")
    
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print(f"📷 カメラを停止しました")
    
    if current_photo == count:
        print(f"🎉 {count}枚の写真撮影が完了しました！")
    else:
        print(f"⚠ {current_photo}枚の写真のみ撮影されました")
    
    return photo_paths

def register_person_interactive():
    """対話式で人物を登録（修正版）"""
    print("\n" + "="*60)
    print(" 新しい人物の登録")
    print("="*60)
    
    # 基本情報入力
    person_id = input("人物ID（英数字、例：family_dad）: ").strip()
    if not person_id:
        print("❌ 人物IDは必須です")
        return
    
    # 英数字とアンダースコアのみ許可
    if not person_id.replace('_', '').isalnum():
        print("❌ 人物IDは英数字とアンダースコア(_)のみ使用可能です")
        return
    
    name = input("名前: ").strip()
    if not name:
        print("❌ 名前は必須です")
        return
    
    relationship = input("関係性（例：家族、友人、配達員）: ").strip()
    notes = input("備考（例：いつもの郵便屋さん）: ").strip()
    
    print(f"\n登録情報:")
    print(f"ID: {person_id}")
    print(f"名前: {name}")
    print(f"関係性: {relationship}")
    print(f"備考: {notes}")
    
    confirm = input("\nこの情報で登録しますか？ (y/N): ").lower()
    if confirm not in ['y', 'yes']:
        print("❌ 登録をキャンセルしました")
        return
    
    # 写真撮影方法選択
    print("\n写真の追加方法を選択してください：")
    print("1. カメラで撮影")
    print("2. 既存の画像ファイルを指定")
    print("3. スキップ（後で追加）")
    
    choice = input("選択 (1/2/3): ").strip()
    
    photo_paths = []
    
    if choice == "1":
        # カメラで撮影
        print("\n📸 カメラでの撮影を開始します...")
        print("注意: 他のアプリケーションでカメラを使用している場合は先に終了してください")
        
        ready = input("準備ができたらEnterキーを押してください...")
        photo_paths = take_photo_for_registration(person_id, name, 3)
        
    elif choice == "2":
        # 既存ファイルを指定
        print("画像ファイルのパスを入力してください（複数可、空行で終了）:")
        while True:
            path = input("画像パス: ").strip()
            if not path:
                break
            if Path(path).exists():
                photo_paths.append(path)
                print(f"✅ 追加: {path}")
            else:
                print(f"❌ ファイルが見つかりません: {path}")
                
    elif choice == "3":
        print("⚠ 写真なしで登録します（後で追加してください）")
        
    else:
        print("❌ 無効な選択です")
        return
    
    # 顔認識システムで登録（写真がある場合のみ）
    if photo_paths:
        try:
            # face_recognitionライブラリのテスト
            import face_recognition
            print("✅ face_recognition ライブラリが利用可能です")
            
            from face_recognition_advanced import AdvancedFaceRecognizer
            recognizer = AdvancedFaceRecognizer()
            
            if not recognizer.is_available():
                print("❌ face_recognition ライブラリが利用できません")
                print("インストール: pip install face-recognition")
                return
            
            print(f"\n📊 {len(photo_paths)}枚の画像から顔エンコーディングを抽出中...")
            
            success = recognizer.register_person(
                person_id=person_id,
                name=name,
                image_paths=photo_paths,
                relationship=relationship,
                notes=notes
            )
            
            if success:
                print(f"🎉 {name}さんの登録が完了しました！")
                print(f"人物ID: {person_id}")
                print(f"登録画像数: {len(photo_paths)}枚")
                print(f"関係性: {relationship}")
                
                # 登録テスト
                test_choice = input("\n登録した人物の認識テストを実行しますか？ (y/N): ").lower()
                if test_choice in ['y', 'yes']:
                    test_recognition_for_person(person_id, name)
                
            else:
                print("❌ 登録に失敗しました")
                print("写真に顔が明確に写っているか確認してください")
                
        except ImportError:
            print("❌ face_recognition ライブラリがインストールされていません")
            print("インストール方法:")
            print("1. pip install face-recognition")
            print("2. または: python setup_advanced_face.py")
            
        except Exception as e:
            print(f"❌ 登録中にエラーが発生しました: {e}")
    else:
        print("⚠ 写真が登録されていないため、顔認識機能は使用できません")
        print("後で写真を追加してください: python face_manager.py register")

def test_recognition_for_person(person_id: str, name: str):
    """特定の人物の認識テスト"""
    print(f"\n🔍 {name}さんの認識テストを開始します...")
    print("カメラの前に座ってください（Escキーで終了）")
    
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        from models import CameraFrame
        
        recognizer = AdvancedFaceRecognizer()
        
        # カメラ初期化
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            print("❌ カメラを開けませんでした")
            return
        
        print("✅ 認識テスト開始 - Escキーで終了")
        
        while True:
            ret, frame = camera.read()
            if not ret:
                continue
            
            # フレームを左右反転
            frame = cv2.flip(frame, 1)
            
            # CameraFrameオブジェクトに変換
            camera_frame = CameraFrame(
                image=frame,
                timestamp=datetime.now(),
                width=frame.shape[1],
                height=frame.shape[0],
                source="test_camera"
            )
            
            # 顔認識実行
            result = recognizer.recognize_person(camera_frame)
            
            # 結果を画像に描画
            if result.face_detections:
                annotated_frame = recognizer.draw_detections(camera_frame, result.face_detections)
            else:
                annotated_frame = frame
            
            # 結果表示
            if result.is_known_person and result.person_id == person_id:
                cv2.putText(annotated_frame, f"RECOGNIZED: {name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Confidence: {result.confidence:.2f}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(annotated_frame, "SUCCESS!", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            elif result.is_known_person:
                other_info = recognizer.get_person_info(result.person_id)
                other_name = other_info['name'] if other_info else result.person_id
                cv2.putText(annotated_frame, f"WRONG PERSON: {other_name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                cv2.putText(annotated_frame, "NOT RECOGNIZED", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if result.face_detections:
                    cv2.putText(annotated_frame, "Face detected but unknown", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                else:
                    cv2.putText(annotated_frame, "No face detected", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            cv2.putText(annotated_frame, "Press ESC to exit", 
                       (10, annotated_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow(f'Recognition Test - {name}', annotated_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # Escapeキー
                break
        
        camera.release()
        cv2.destroyAllWindows()
        print("✅ 認識テスト終了")
        
    except ImportError:
        print("❌ 必要なライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ 認識テストエラー: {e}")

def list_registered_persons():
    """登録済み人物一覧表示"""
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            return
        
        persons = recognizer.get_all_persons()
        
        if not persons:
            print("📝 登録された人物はいません")
            return
        
        print("\n" + "="*80)
        print(" 登録済み人物一覧")
        print("="*80)
        print(f"{'ID':<15} {'名前':<15} {'関係性':<10} {'認識回数':<8} {'最終確認':<12}")
        print("-"*80)
        
        for person in persons:
            last_seen = person['last_seen']
            if last_seen:
                last_seen = datetime.fromisoformat(last_seen).strftime('%m/%d %H:%M')
            else:
                last_seen = "未認識"
            
            print(f"{person['person_id']:<15} {person['name']:<15} {person['relationship']:<10} "
                  f"{person['recognition_count']:<8} {last_seen:<12}")
        
        print(f"\n合計: {len(persons)}人が登録されています")
        
    except ImportError:
        print("❌ face_recognition ライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ エラー: {e}")

def delete_person_interactive():
    """対話式で人物を削除"""
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            return
        
        # 登録済み人物一覧表示
        list_registered_persons()
        
        print("\n削除したい人物のIDを入力してください:")
        person_id = input("人物ID: ").strip()
        
        if not person_id:
            print("❌ IDが入力されませんでした")
            return
        
        # 人物情報確認
        person_info = recognizer.get_person_info(person_id)
        if not person_info:
            print(f"❌ 人物ID '{person_id}' は見つかりませんでした")
            return
        
        print(f"\n削除対象:")
        print(f"ID: {person_info['person_id']}")
        print(f"名前: {person_info['name']}")
        print(f"関係性: {person_info['relationship']}")
        print(f"認識回数: {person_info['recognition_count']}")
        
        confirm = input(f"\n'{person_info['name']}'さんを削除しますか？ (y/N): ").lower()
        if confirm not in ['y', 'yes']:
            print("❌ 削除をキャンセルしました")
            return
        
        if recognizer.delete_person(person_id):
            print(f"✅ {person_info['name']}さんを削除しました")
        else:
            print("❌ 削除に失敗しました")
            
    except ImportError:
        print("❌ face_recognition ライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ エラー: {e}")

def show_recognition_stats():
    """認識統計表示"""
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            return
        
        stats = recognizer.get_recognition_stats()
        
        print("\n" + "="*60)
        print(" 認識統計")
        print("="*60)
        print(f"登録人数: {stats.get('total_persons', 0)}人")
        print(f"総認識回数: {stats.get('total_recognitions', 0)}回")
        print(f"今日の認識回数: {stats.get('today_recognitions', 0)}回")
        print(f"エンコーディング数: {stats.get('encodings_count', 0)}個")
        print(f"データベース: {stats.get('database_path', 'N/A')}")
        
    except ImportError:
        print("❌ face_recognition ライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ エラー: {e}")

def test_recognition_system():
    """認識システムテスト（修正版）"""
    print("\n" + "="*60)
    print(" 認識システムテスト")
    print("="*60)
    
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            print("インストール: pip install face-recognition")
            return
        
        print("📸 カメラで認識テストを開始します")
        print("操作方法: Escキー=終了, Qキー=終了")
        
        # カメラ初期化
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            print("❌ カメラを開けませんでした")
            return
        
        # カメラ設定
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("✅ カメラ開始 - 顔認識テスト中...")
        
        from models import CameraFrame
        
        while True:
            ret, frame = camera.read()
            if not ret:
                continue
            
            # フレームを左右反転
            frame = cv2.flip(frame, 1)
            
            # CameraFrameオブジェクトに変換
            camera_frame = CameraFrame(
                image=frame,
                timestamp=datetime.now(),
                width=frame.shape[1],
                height=frame.shape[0],
                source="test_camera"
            )
            
            # 顔認識実行
            result = recognizer.recognize_person(camera_frame)
            
            # 結果を画像に描画
            if result.face_detections:
                annotated_frame = recognizer.draw_detections(camera_frame, result.face_detections)
            else:
                annotated_frame = frame
            
            # 結果表示
            if result.is_known_person:
                person_info = recognizer.get_person_info(result.person_id)
                name = person_info['name'] if person_info else result.person_id
                relationship = person_info.get('relationship', '') if person_info else ''
                
                cv2.putText(annotated_frame, f"Recognized: {name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Relationship: {relationship}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Confidence: {result.confidence:.2f}", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                if result.face_detections:
                    cv2.putText(annotated_frame, "Unknown Person", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(annotated_frame, f"Faces detected: {len(result.face_detections)}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.putText(annotated_frame, "No Face Detected", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            cv2.putText(annotated_frame, "Press ESC or Q to exit", 
                       (10, annotated_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Face Recognition Test', annotated_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q') or key == ord('Q'):  # Escape or Q
                break
        
        camera.release()
        cv2.destroyAllWindows()
        print("✅ 認識テスト終了")
        
    except ImportError:
        print("❌ 必要なライブラリがインストールされていません")
        print("インストール: python setup_advanced_face.py")
    except Exception as e:
        print(f"❌ 認識テストエラー: {e}")

def export_database():
    """データベースをJSONでエクスポート"""
    try:
        from face_recognition_advanced import AdvancedFaceRecognizer
        recognizer = AdvancedFaceRecognizer()
        
        if not recognizer.is_available():
            print("❌ face_recognition ライブラリが利用できません")
            return
        
        persons = recognizer.get_all_persons()
        stats = recognizer.get_recognition_stats()
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'statistics': stats,
            'persons': persons
        }
        
        export_file = config.DATA_DIR / f"face_database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ データベースをエクスポートしました: {export_file}")
        
    except ImportError:
        print("❌ face_recognition ライブラリがインストールされていません")
    except Exception as e:
        print(f"❌ エラー: {e}")

def setup_sample_persons():
    """サンプル人物データの説明"""
    print("\n" + "="*60)
    print(" サンプル人物データ設定ガイド")
    print("="*60)
    
    sample_persons = [
        {
            'person_id': 'family_dad',
            'name': 'お父さん',
            'relationship': '家族',
            'notes': 'お疲れ様です'
        },
        {
            'person_id': 'family_mom',
            'name': 'お母さん',
            'relationship': '家族',
            'notes': 'おかえりなさい'
        },
        {
            'person_id': 'delivery_yamato',
            'name': 'ヤマト配達員',
            'relationship': '配達員',
            'notes': 'いつものヤマト運輸の方'
        },
        {
            'person_id': 'postman_regular',
            'name': '郵便配達員',
            'relationship': '郵便局員',
            'notes': '毎日来る郵便屋さん'
        }
    ]
    
    print("推奨する人物登録例:")
    for i, person in enumerate(sample_persons, 1):
        print(f"\n{i}. {person['name']}")
        print(f"   ID: {person['person_id']}")
        print(f"   関係性: {person['relationship']}")
        print(f"   備考: {person['notes']}")
    
    print(f"\n登録方法:")
    print("python face_manager.py register")
    print("\n各人物の写真を3枚ずつ撮影することを推奨します。")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="顔認識管理ツール（動画撮影対応版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python face_manager.py register         # 静止画撮影で登録
  python face_manager.py register_video   # 動画撮影で登録（推奨）
  python face_manager.py list            # 登録済み人物一覧
  python face_manager.py delete          # 人物を削除
  python face_manager.py test            # 認識システムテスト
  python face_manager.py stats           # 認識統計表示
  python face_manager.py export          # データベースエクスポート
  python face_manager.py sample_guide    # サンプルデータ設定ガイド
"""
    )

    parser.add_argument(
        "command",
        choices=["register", "register_video", "list", "delete", "test", "stats", "export", "sample_guide"],
        help="実行するコマンド"
    )

    args = parser.parse_args()

    if args.command == "register":
        # 従来の静止画撮影
        from face_manager import register_person_interactive
        register_person_interactive()
    elif args.command == "register_video":
        # 新しい動画撮影
        register_person_with_video()
    elif args.command == "list":
        list_registered_persons()
    elif args.command == "delete":
        delete_person_interactive()
    elif args.command == "test":
        test_recognition_system()
    elif args.command == "stats":
        show_recognition_stats()
    elif args.command == "export":
        export_database()
    elif args.command == "sample_guide":
        setup_sample_persons()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()