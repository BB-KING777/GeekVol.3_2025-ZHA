"""
API通信モジュール - Ollama専用、依存性最小化
"""
import requests
import base64
import json
import time
import logging
import cv2
from typing import Optional

import config
from models import CameraFrame, APIResponse

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama API クライアント"""
    
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model_name = config.MODEL_NAME
        self.timeout = config.REQUEST_TIMEOUT
        self.session = requests.Session()
        
        # セッション設定
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "GeekCam-VisitorRecognition/1.0"
        })
        
        logger.info(f"Ollama APIクライアント初期化: {self.base_url}")
    
    def test_connection(self) -> bool:
        """API接続テスト"""
        try:
            # Ollamaのタグエンドポイントをテスト
            tags_url = self.base_url.replace("/api/chat", "/api/tags")
            response = self.session.get(tags_url, timeout=5)
            
            if response.status_code == 200:
                logger.info("Ollama API接続テスト成功")
                return True
            else:
                logger.error(f"Ollama API接続テスト失敗: ステータス {response.status_code}")
                return False
                
        except requests.exceptions.ConnectError:
            logger.error("Ollama APIサーバーに接続できません。Ollamaが起動しているか確認してください。")
            return False
        except Exception as e:
            logger.error(f"Ollama API接続テストエラー: {e}")
            return False
    
    def get_available_models(self) -> list:
        """利用可能なモデル一覧を取得"""
        try:
            tags_url = self.base_url.replace("/api/chat", "/api/tags")
            response = self.session.get(tags_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                logger.info(f"利用可能なモデル: {models}")
                return models
            else:
                logger.error(f"モデル一覧取得失敗: ステータス {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"モデル一覧取得エラー: {e}")
            return []
    
    def analyze_image(self, frame: CameraFrame) -> APIResponse:
        """画像分析リクエスト"""
        start_time = time.time()
        
        try:
            # 画像をBase64エンコード
            base64_image = self._encode_image(frame.image)
            if not base64_image:
                return APIResponse(
                    success=False,
                    error_message="画像のエンコードに失敗しました"
                )
            
            # APIリクエスト構築
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": config.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": "この画像に映っている人物について説明してください。",
                        "images": [base64_image]
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 150
                }
            }
            
            # APIリクエスト送信
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                
                if not content:
                    return APIResponse(
                        success=False,
                        error_message="APIからの応答が空です",
                        response_time=response_time
                    )
                
                logger.info(f"API分析成功 ({response_time:.2f}s): {content[:100]}...")
                
                return APIResponse(
                    success=True,
                    content=content,
                    response_time=response_time,
                    model_used=self.model_name
                )
                
            else:
                error_msg = f"API通信エラー: ステータス {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text[:200]}"
                
                logger.error(error_msg)
                
                return APIResponse(
                    success=False,
                    error_message=error_msg,
                    response_time=response_time
                )
                
        except requests.exceptions.Timeout:
            error_msg = f"API要求がタイムアウトしました ({self.timeout}秒)"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
            
        except requests.exceptions.ConnectError:
            error_msg = "Ollamaサーバーに接続できません"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"API通信中に予期しないエラー: {str(e)}"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
    
    def _encode_image(self, image) -> Optional[str]:
        """画像をBase64エンコード"""
        try:
            # OpenCV画像をJPEGとしてエンコード
            success, buffer = cv2.imencode('.jpg', image, [
                cv2.IMWRITE_JPEG_QUALITY, 85
            ])
            
            if not success:
                logger.error("画像のJPEGエンコードに失敗")
                return None
            
            # Base64エンコード
            base64_image = base64.b64encode(buffer).decode('utf-8')
            
            logger.debug(f"画像をBase64エンコード完了 ({len(base64_image)} 文字)")
            return base64_image
            
        except Exception as e:
            logger.error(f"画像エンコードエラー: {e}")
            return None
    
    def health_check(self) -> dict:
        """ヘルスチェック"""
        result = {
            "api_accessible": False,
            "model_available": False,
            "response_time": 0.0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # 基本的な接続テスト
            if self.test_connection():
                result["api_accessible"] = True
                
                # モデル利用可能性チェック
                models = self.get_available_models()
                if self.model_name in models:
                    result["model_available"] = True
                else:
                    result["error"] = f"モデル '{self.model_name}' が利用不可"
            else:
                result["error"] = "API接続失敗"
                
        except Exception as e:
            result["error"] = str(e)
        
        result["response_time"] = time.time() - start_time
        
        return result
    
    def switch_model(self, model_name: str) -> bool:
        """使用モデル切り替え"""
        try:
            # モデルが利用可能かチェック
            available_models = self.get_available_models()
            if model_name not in available_models:
                logger.error(f"モデル '{model_name}' は利用できません")
                return False
            
            self.model_name = model_name
            logger.info(f"使用モデルを切り替え: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"モデル切り替えエラー: {e}")
            return False