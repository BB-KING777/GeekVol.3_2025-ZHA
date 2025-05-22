"""
メインシステム - 全モジュール統合
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
    """訪問者認識システムメインクラス"""
    
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
        """フレームキャプチャメインループ"""
        while not self.stop_capture and self.status.is_running:
            try:
                # フレーム取得
                frame = self.camera_manager.get_frame()
                if frame:
                    # バッファに追加
                    self.frame_buffer.add_frame(frame)
                    self.status.frame_count += 1
                
                # 短時間待機
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"フレームキャプチャエラー: {e}")
                time.sleep(0.5)
        
        logger.info("フレームキャプチャスレッド終了")
    
    def analyze_visitor(self, time_offset: float = 0.0) -> AnalysisResult:
        """訪問者分析実行"""
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
            
            # 分析用フレーム取得
            if time_offset == 0.0:
                frame = self.frame_buffer.get_latest_frame()
            else:
                frame = self.frame_buffer.get_frame_by_offset(time_offset)
            
            if not frame:
                error_msg = "分析用の画像を取得できませんでした"
                logger.error(error_msg)
                self.audio_manager.speak(error_msg)
                return None
            
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
        """現在のフレーム取得"""
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
    """システム制御クラス - 外部からの操作用"""
    
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
    
    def update_config(self, key: str, value) -> dict:
        """設定更新"""
        try:
            if hasattr(config, key):
                setattr(config, key, value)
                logger.info(f"設定更新: {key} = {value}")
                
                # 特定の設定変更時の処理
                if key == "USE_CAMERA" and self.is_initialized:
                    # カメラ設定変更時は再起動が必要
                    return self.restart()
                
                return {
                    "success": True,
                    "message": f"設定を更新しました: {key} = {value}"
                }
            else:
                return {
                    "success": False,
                    "message": f"不明な設定項目: {key}"
                }
                
        except Exception as e:
            logger.error(f"設定更新エラー: {e}")
            return {
                "success": False,
                "message": f"設定更新エラー: {str(e)}"
            }
    
    def get_config(self) -> dict:
        """現在の設定取得"""
        try:
            return {
                "success": True,
                "config": {
                    "USE_CAMERA": config.USE_CAMERA,
                    "CAMERA_ID": config.CAMERA_ID,
                    "FRAME_RATE": config.FRAME_RATE,
                    "USE_FACE_RECOGNITION": config.USE_FACE_RECOGNITION,
                    "FACE_RECOGNITION_METHOD": config.FACE_RECOGNITION_METHOD,
                    "MODEL_NAME": config.MODEL_NAME,
                    "DEBUG_MODE": config.DEBUG_MODE,
                    "AUTO_SAVE_CAPTURES": config.AUTO_SAVE_CAPTURES
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"設定取得エラー: {str(e)}"
            }
        
    # main_system.py の SystemController クラスに追加

def get_direct_frame(self):
    """フレームレート制限を無視して直接フレーム取得"""
    if not self.is_initialized:
        return None
    
    try:
        camera_manager = self.system.camera_manager
        
        if config.USE_CAMERA:
            # カメラから直接
            if camera_manager.camera and camera_manager.camera.isOpened():
                ret, frame = camera_manager.camera.read()
                if ret and frame is not None:
                    from models import CameraFrame
                    return CameraFrame(
                        image=frame,
                        timestamp=datetime.now(),
                        width=frame.shape[1],
                        height=frame.shape[0],
                        source="camera_direct"
                    )
        else:
            # テスト画像から
            if camera_manager.test_images:
                frame = camera_manager.test_images[camera_manager.current_test_index].copy()
                from models import CameraFrame
                return CameraFrame(
                    image=frame,
                    timestamp=datetime.now(),
                    width=frame.shape[1],
                    height=frame.shape[0],
                    source="test_image_direct"
                )
        
        return None
    except Exception as e:
        logger.error(f"直接フレーム取得エラー: {e}")
        return None

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