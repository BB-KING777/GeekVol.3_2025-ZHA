"""
API通信モジュール: LMStudio APIとの通信を管理
"""
import requests
import json
import base64
import config
from openai import OpenAI

class ApiClient:
    def __init__(self):
        """APIクライアントの初期化"""
        self.client = OpenAI(
            api_key=config.API_KEY,
            base_url=config.API_BASE_URL
        )
        print(f"APIクライアントを初期化しました: {config.API_BASE_URL}")

    def analyze_image(self, base64_image):
        """画像を分析してテキスト説明を取得"""
        if not base64_image:
            print("画像データがありません")
            return "画像の取得に失敗しました。"

        try:
            response = self.client.chat.completions.create(
                model="gemma-3-vision",  # LMStudioでのモデル名
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "この画像に映っている人物について説明してください。"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )
            
            result = response.choices[0].message.content
            if config.DEBUG_MODE:
                print(f"API応答: {result}")
            return result
        except Exception as e:
            print(f"API通信中にエラーが発生しました: {e}")
            return "画像の分析中にエラーが発生しました。"

    def test_connection(self):
        """API接続テスト"""
        try:
            # モデル一覧を取得して接続テスト
            response = requests.get(f"{config.API_BASE_URL}/models")
            if response.status_code == 200:
                print("API接続テスト成功")
                return True
            else:
                print(f"API接続テスト失敗: ステータスコード {response.status_code}")
                return False
        except Exception as e:
            print(f"API接続テスト中にエラーが発生しました: {e}")
            return False