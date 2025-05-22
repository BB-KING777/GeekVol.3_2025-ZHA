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
        description="顔認識管理ツール（修正版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python face_manager.py register      # 新しい人物を登録
  python face_manager.py list         # 登録済み人物一覧
  python face_manager.py delete       # 人物を削除
  python face_manager.py test         # 認識システムテスト
  python face_manager.py stats        # 認識統計表示
  python face_manager.py export       # データベースエクスポート
  python face_manager.py sample_guide # サンプルデータ設定ガイド
"""
    )

    parser.add_argument(
        "command",
        choices=["register", "list", "delete", "test", "stats", "export", "sample_guide"],
        help="実行するコマンド"
    )

    args = parser.parse_args()

    if args.command == "register":
        register_person_interactive()
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