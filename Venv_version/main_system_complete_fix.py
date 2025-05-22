"""
メインシステム - 完全修正版（フレームバッファ問題解決）
"""
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path

import config
from models import SystemStatus, AnalysisResult
from camera_module import CameraManager, FrameBuffer
from face_recognition_module import FaceRecognitionManager
from audio_module import AudioManager
from api_client import OllamaClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / 'system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VisitorRecognitionSystem:
    """訪問者認識システムメインクラス（完全修正版）"""
    
    def __init__(self):
        # システム状態
        self.status = SystemStatus()
        self.last_analysis_result = None
        self.analysis_lock = threading.Lock()
        
        # コンポーネント初期化
        self.camera_manager = CameraManager()
        self.frame_buffer = FrameBuffer(max_frames=30)
        self.face_recognition = FaceRecognitionManager()
        self.audio_manager = AudioManager()
        self.api_client = OllamaClient()
        
        # フレームキャプチャスレッド
        self.capture_thread = None
        self.stop_capture = False
        
        logger.info("訪問者認識システムを初期化")
    
    def start(self) -> bool:
        """システム開始"""
        try:
            logger.info("システム開始処理を実行中...")
            
            # API接続テスト
            self.audio_manager.speak("システムの初期化を開始します", priority=1)
            
            if not self.api_client.test_connection():
                error_msg = "Ollama APIに接続できません。Ollamaが起動しているか確認してください。"
                logger.error(error_msg)
                self.audio_manager.speak_immediately(error_msg)
                return False
            
            # カメラ初期化
            if not self.camera_manager.start():
                error_msg = "カメラの初期化に失敗しました。"
                logger.error(error_msg)
                self.audio_manager.speak_immediately(error_msg)
                return False
            
            # フレームキャプチャスレッド開始
            self._start_frame_capture()
            
            # システム状態更新
            self.status.is_running = True
            self.status.camera_active = True
            
            # フレームキャプチャが正常に動作するまで少し待機
            time.sleep(2)
            
            # 開始メッセージ
            camera_mode = "カメラ" if config.USE_CAMERA else "テスト画像"
            face_methods = self.face_recognition.get_available_methods()
            
            success_msg = f"システムが正常に起動しました。{camera_mode}モードで動作中です。"
            if config.USE_FACE_RECOGNITION:
                success_msg += f" 顔認識: {face_methods[0] if face_methods else 'なし'}"
            
            logger.info(success_msg)
            self.audio_manager.speak(success_msg)
            
            return True
            
        except Exception as e:
            error_msg = f"システム開始エラー: {str(e)}"
            logger.error(error_msg)
            self.audio_manager.speak_immediately(error_msg)
            return False
    
    def _start_frame_capture(self):
        """フレームキャプチャスレッド開始"""
        self.stop_capture = False
        self.capture_thread = threading.Thread(target=self._frame_capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("フレームキャプチャスレッド開始")
    
    def _frame_capture_loop(self):
        """フレームキャプチャメインループ（修正版）"""
        logger.info("フレームキャプチャループ開始")
        frame_count = 0
        error_count = 0
        last_success_time = time.time()
        
        while not self.stop_capture and self.status.is_running:
            try:
                current_time = time.time()
                
                # フレーム取得（フレームレート制限を無視）
                original_last_time = self.camera_manager.last_frame_time
                self.camera_manager.last_frame_time = 0  # フレームレート制限を一時無効化
                
                frame = self.camera_manager.get_frame()
                
                self.camera_manager.last_frame_time = original_last_time  # 制限を復元
                
                if frame and frame.image is not None:
                    # フレームバッファに追加
                    self.frame_buffer.add_frame(frame)
                    self.status.frame_count += 1
                    frame_count += 1
                    last_success_time = current_time
                    error_count = 0  # エラーカウントリセット
                    
                    # 定期的な進捗表示
                    if frame_count % 30 == 0:
                        logger.info(f"フレームキャプチャ進行中: {frame_count}フレーム, バッファサイズ: {len(self.frame_buffer.frames)}")
                
                else:
                    error_count += 1
                    if error_count % 10 == 0:
                        logger.warning(f"フレーム取得失敗継続中: {error_count}回")
                
                # 短時間待機（フレームレート調整）
                time.sleep(0.1)  # 10FPS程度
                
            except Exception as e:
                error_count += 1
                if error_count % 20 == 0:
                    logger.error(f"フレームキャプチャエラー (第{error_count}回): {e}")
                time.sleep(0.5)
        
        logger.info(f"フレームキャプチャループ終了 (総フレーム数: {frame_count})")
    
    def analyze_visitor(self, time_offset: float = 0.0) -> AnalysisResult:
        """訪問者分析実行（修正版）"""
        start_time = time.time()
        
        with self.analysis_lock:
            if self.status.is_processing:
                logger.warning("分析処理が既に実行中です")
                return self.last_analysis_result
            
            self.status.is_processing = True
            self.status.last_analysis = datetime.now()
        
        try:
            logger.info("訪問者分析を開始")
            self.audio_manager.speak("訪問者を確認しています。しばらくお待ちください。", priority=1)
            
            # 分析用フレーム取得（複数の方法を試行）
            frame = None
            
            # 方法1: フレームバッファから取得
            if time_offset == 0.0:
                frame = self.frame_buffer.get_latest_frame()
                if frame:
                    logger.info("方法1: フレームバッファから取得成功")
                else:
                    logger.warning("方法1: フレームバッファから取得失敗")
            else:
                frame = self.frame_buffer.get_frame_by_offset(time_offset)
                if frame:
                    logger.info(f"方法1: オフセット{time_offset}秒でフレーム取得成功")
                else:
                    logger.warning(f"方法1: オフセット{time_offset}秒でフレーム取得失敗")
            
            # 方法2: カメラマネージャーから直接取得
            if not frame:
                logger.info("方法2: カメラマネージャーから直接取得を試行")
                # フレームレート制限を一時的に無効化
                original_last_time = self.camera_manager.last_frame_time
                self.camera_manager.last_frame_time = 0
                
                frame = self.camera_manager.get_frame()
                
                # フレームレート制限を復元
                self.camera_manager.last_frame_time = original_last_time
                
                if frame:
                    logger.info("方法2: カメラマネージャーから取得成功")
                else:
                    logger.warning("方法2: カメラマネージャーから取得失敗")
            
            # 方法3: 直接カメラAPIから取得
            if not frame:
                logger.info("方法3: 直接カメラAPIから取得を試行")
                try:
                    import cv2
                    from models import CameraFrame
                    
                    if config.USE_CAMERA and self.camera_manager.camera:
                        ret, direct_frame = self.camera_manager.camera.read()
                        if ret and direct_frame is not None:
                            # タイムスタンプ追加
                            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cv2.putText(direct_frame, timestamp_str, (10, direct_frame.shape[0] - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
                            frame = CameraFrame(
                                image=direct_frame,
                                timestamp=datetime.now(),
                                width=direct_frame.shape[1],
                                height=direct_frame.shape[0],
                                source="camera_direct"
                            )
                            logger.info("方法3: 直接カメラAPIから取得成功")
                        else:
                            logger.warning("方法3: 直接カメラAPIから取得失敗")
                    elif not config.USE_CAMERA and self.camera_manager.test_images:
                        test_frame = self.camera_manager.test_images[self.camera_manager.current_test_index].copy()
                        self.camera_manager.current_test_index = (self.camera_manager.current_test_index + 1) % len(self.camera_manager.test_images)
                        
                        # タイムスタンプ追加
                        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cv2.putText(test_frame, timestamp_str, (10, test_frame.shape[0] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        frame = CameraFrame(
                            image=test_frame,
                            timestamp=datetime.now(),
                            width=test_frame.shape[1],
                            height=test_frame.shape[0],
                            source="test_image_direct"
                        )
                        logger.info("方法3: テスト画像から取得成功")
                except Exception as e:
                    logger.error(f"方法3でエラー: {e}")
            
            if not frame:
                error_msg = "すべての方法で分析用の画像を取得できませんでした"
                logger.error(error_msg)
                logger.error(f"バッファ内フレーム数: {len(self.frame_buffer.frames)}")
                logger.error(f"カメラ状態: 稼働={self.camera_manager.is_running}, カメラ={self.camera_manager.camera is not None}")
                self.audio_manager.speak(error_msg)
                return None
            
            logger.info(f"分析用フレーム取得成功: {frame.width}x{frame.height} ({frame.source})")
            
            # Step 1: 顔認識
            person_recognition = self.face_recognition.recognize_person(frame)
            logger.info(f"顔認識結果: {person_recognition.method_used}, 顔数: {len(person_recognition.face_detections)}")
            
            # Step 2: 既知の人物チェック
            if person_recognition.is_known_person:
                # 既知の人物の場合
                message = f"{person_recognition.person_id}さんがいらっしゃいました"
                ai_description = ""
                
                self.audio_manager.speak(message)
                self.audio_manager.speak("いらっしゃいませ")
                
            else:
                # 未知の人物 → AI分析
                logger.info("未知の訪問者のためAI分析を実行")
                
                api_response = self.api_client.analyze_image(frame)
                
                if api_response.success:
                    ai_description = api_response.content
                    message = f"未知の訪問者です。{ai_description}"
                    
                    self.audio_manager.speak("未知の訪問者です")
                    time.sleep(0.5)
                    self.audio_manager.speak(ai_description)
                    
                else:
                    ai_description = api_response.error_message
                    message = f"分析エラーが発生しました: {ai_description}"
                    
                    self.audio_manager.speak(message)
            
            # 分析結果作成
            processing_time = time.time() - start_time
            analysis_result = AnalysisResult(
                timestamp=datetime.now(),
                frame=frame,
                person_recognition=person_recognition,
                ai_description=ai_description,
                processing_time=processing_time
            )
            
            # 画像保存（オプション）
            if config.AUTO_SAVE_CAPTURES:
                self._save_analysis_image(analysis_result)
            
            self.last_analysis_result = analysis_result
            logger.info(f"訪問者分析完了 ({processing_time:.2f}秒)")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"訪問者分析エラー: {str(e)}"
            logger.error(error_msg)
            self.audio_manager.speak("分析中にエラーが発生しました")
            return None
            
        finally:
            self.status.is_processing = False
    
    def _save_analysis_image(self, result: AnalysisResult):
        """分析画像保存"""
        try:
            import cv2
            
            # タイムスタンプファイル名
            timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
            
            # 基本画像保存
            basic_filename = config.CAPTURES_DIR / f"analysis_{timestamp}.jpg"
            cv2.imwrite(str(basic_filename), result.frame.image)
            
            # 顔検出結果付き画像保存（顔が検出された場合）
            if result.person_recognition.face_detections:
                annotated_image = self.face_recognition.draw_detections(
                    result.frame, 
                    result.person_recognition.face_detections
                )
                annotated_filename = config.CAPTURES_DIR / f"analysis_faces_{timestamp}.jpg"
                cv2.imwrite(str(annotated_filename), annotated_image)
            
            logger.info(f"分析画像保存: {basic_filename}")
            
        except Exception as e:
            logger.error(f"画像保存エラー: {e}")
    
    def get_current_frame(self):
        """現在のフレーム取得（修正版）"""
        # まずバッファから試行
        frame = self.frame_buffer.get_latest_frame()
        if frame:
            return frame
        
        # バッファにない場合は直接取得
        return self.camera_manager.get_current_frame()
    
    def get_system_status(self) -> dict:
        """システム状態取得"""
        audio_status = self.audio_manager.get_status()
        
        return {
            "system": {
                "is_running": self.status.is_running,
                "is_processing": self.status.is_processing,
                "camera_active": self.status.camera_active,
                "frame_count": self.status.frame_count,
                "buffer_size": len(self.frame_buffer.frames),  # バッファサイズも追加
                "last_analysis": self.status.last_analysis.isoformat() if self.status.last_analysis else None,
                "last_error": self.status.last_error
            },
            "audio": audio_status,
            "face_recognition": {
                "enabled": config.USE_FACE_RECOGNITION,
                "method": config.FACE_RECOGNITION_METHOD,
                "available_methods": self.face_recognition.get_available_methods()
            },
            "api": self.api_client.health_check(),
            "last_result": {
                "message": self.last_analysis_result.get_message() if self.last_analysis_result else None,
                "processing_time": self.last_analysis_result.processing_time if self.last_analysis_result else 0,
                "person_detected": bool(self.last_analysis_result.person_recognition.face_detections) if self.last_analysis_result else False
            } if self.last_analysis_result else None
        }
    
    def stop(self):
        """システム停止"""
        logger.info("システム停止処理を開始")
        
        try:
            # 音声通知
            self.audio_manager.speak_immediately("システムを停止します")
            
            # フラグ設定
            self.status.is_running = False
            self.stop_capture = True
            
            # コンポーネント停止
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2)
            
            self.camera_manager.stop()
            self.audio_manager.stop()
            
            logger.info("システム停止完了")
            
        except Exception as e:
            logger.error(f"システム停止エラー: {e}")

class SystemController:
    """システム制御クラス - 外部からの操作用（修正版）"""
    
    def __init__(self):
        self.system = VisitorRecognitionSystem()
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """システム初期化"""
        if self.is_initialized:
            return True
        
        success = self.system.start()
        if success:
            self.is_initialized = True
            logger.info("システムコントローラー初期化完了")
        
        return success
    
    def doorbell_pressed(self, time_offset: float = 0.0) -> dict:
        """呼び鈴押下処理"""
        if not self.is_initialized:
            return {
                "success": False,
                "message": "システムが初期化されていません"
            }
        
        if self.system.status.is_processing:
            return {
                "success": False,
                "message": "別の分析処理が実行中です"
            }
        
        try:
            # 非同期で分析実行
            threading.Thread(
                target=self.system.analyze_visitor,
                args=(time_offset,),
                daemon=True
            ).start()
            
            return {
                "success": True,
                "message": "訪問者分析を開始しました"
            }
            
        except Exception as e:
            logger.error(f"呼び鈴処理エラー: {e}")
            return {
                "success": False,
                "message": f"処理エラー: {str(e)}"
            }
    
    def speak_text(self, text: str, priority: int = 1) -> dict:
        """テキスト読み上げ"""
        try:
            self.system.audio_manager.speak(text, priority)
            return {
                "success": True,
                "message": "音声出力を開始しました"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"音声出力エラー: {str(e)}"
            }
    
    def save_current_frame(self) -> dict:
        """現在フレーム保存"""
        try:
            frame = self.system.get_current_frame()
            if not frame:
                return {
                    "success": False,
                    "message": "フレームが取得できません"
                }
            
            import cv2
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = config.CAPTURES_DIR / f"manual_{timestamp}.jpg"
            cv2.imwrite(str(filename), frame.image)
            
            return {
                "success": True,
                "message": f"画像を保存しました: {filename.name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"画像保存エラー: {str(e)}"
            }
    
    def get_status(self) -> dict:
        """システム状態取得"""
        if not self.is_initialized:
            return {
                "system": {"is_running": False},
                "message": "システムが初期化されていません"
            }
        
        return self.system.get_system_status()
    
    def shutdown(self) -> dict:
        """システム終了"""
        try:
            if self.is_initialized:
                self.system.stop()
                self.is_initialized = False
            
            return {
                "success": True,
                "message": "システムを停止しました"
            }
            
        except Exception as e:
            logger.error(f"システム終了エラー: {e}")
            return {
                "success": False,
                "message": f"終了エラー: {str(e)}"
            }
    
    def restart(self) -> dict:
        """システム再起動"""
        try:
            # 停止
            self.shutdown()
            time.sleep(1)
            
            # 再初期化
            success = self.initialize()
            
            return {
                "success": success,
                "message": "システムを再起動しました" if success else "再起動に失敗しました"
            }
            
        except Exception as e:
            logger.error(f"システム再起動エラー: {e}")
            return {
                "success": False,
                "message": f"再起動エラー: {str(e)}"
            }

# システムのグローバルインスタンス（シングルトン的な使用）
_system_controller = None

def get_system_controller() -> SystemController:
    """システムコントローラーのシングルトン取得"""
    global _system_controller
    if _system_controller is None:
        _system_controller = SystemController()
    return _system_controller

def cleanup_system():
    """システムクリーンアップ"""
    global _system_controller
    if _system_controller and _system_controller.is_initialized:
        _system_controller.shutdown()
        _system_controller = None
