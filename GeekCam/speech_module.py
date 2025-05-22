"""
音声出力モジュール: テキストを音声に変換（Tkinter対応版）
"""
import pyttsx3
import time
import threading
import queue
import config

class SpeechModule:
    def __init__(self):
        """音声モジュールの初期化"""
        self.engine = pyttsx3.init()
        self.configure_voice()
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.stop_requested = False
        
        # スピーチスレッドの開始
        self.speech_thread = threading.Thread(target=self._process_speech_queue)
        self.speech_thread.daemon = True
        self.speech_thread.start()
        
        print("音声モジュールを初期化しました")

    def configure_voice(self):
        """音声設定の構成"""
        # 利用可能な声を確認
        voices = self.engine.getProperty('voices')
        japanese_voice = None
        
        # 日本語の声を探す
        for voice in voices:
            if "japanese" in voice.name.lower() or "ja" in voice.id.lower():
                japanese_voice = voice.id
                break
        
        # 日本語の声が見つかった場合は設定
        if japanese_voice:
            self.engine.setProperty('voice', japanese_voice)
            print(f"日本語の音声を設定しました: {japanese_voice}")
        
        # 音声の速度と音量を設定
        self.engine.setProperty('rate', config.VOICE_RATE)
        self.engine.setProperty('volume', config.VOICE_VOLUME)

    def speak(self, text):
        """テキストを音声に変換（非同期）"""
        if not text:
            return
            
        if config.DEBUG_MODE:
            print(f"音声キューに追加: {text}")
        
        try:
            self.speech_queue.put(text)
        except Exception as e:
            print(f"音声キューへの追加中にエラーが発生しました: {e}")

    def speak_sync(self, text):
        """テキストを音声に変換（同期）- Tkinterと衝突するため注意"""
        if not text:
            return
            
        if config.DEBUG_MODE:
            print(f"音声出力: {text}")
         
        # GUIスレッドでは音声出力の代わりにキューに追加
        if threading.current_thread() != self.speech_thread:
            self.speak(text)
            return
            
        # 専用スレッドでのみ実行
        try:    
            self.engine.say(text)
            self.engine.runAndWait()
        except RuntimeError as e:
            print(f"音声出力中にエラーが発生しました（無視して継続）: {e}")
            # フォールバックとして結果を表示
            print("\n" + "=" * 60)
            print("【音声出力】" + text)
            print("=" * 60 + "\n")

    def _process_speech_queue(self):
        """音声キューを処理するスレッド"""
        while not self.stop_requested:
            try:
                # キューからテキストを取得（タイムアウト付き）
                try:
                    text_to_speak = self.speech_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                # 音声出力
                self.is_speaking = True
                
                try:
                    # エンジンを再初期化して問題を回避
                    engine = pyttsx3.init()
                    voices = engine.getProperty('voices')
                    japanese_voice = None
                    for voice in voices:
                        if "japanese" in voice.name.lower() or "ja" in voice.id.lower():
                            japanese_voice = voice.id
                            break
                    if japanese_voice:
                        engine.setProperty('voice', japanese_voice)
                    engine.setProperty('rate', config.VOICE_RATE)
                    engine.setProperty('volume', config.VOICE_VOLUME)
                    
                    # 音声出力
                    engine.say(text_to_speak)
                    engine.runAndWait()
                except Exception as e:
                    print(f"音声出力中にエラーが発生しました: {e}")
                    # テキスト出力にフォールバック
                    print("\n" + "=" * 60)
                    print("【音声出力】" + text_to_speak)
                    print("=" * 60 + "\n")
                
                self.is_speaking = False
                self.speech_queue.task_done()
                
            except Exception as e:
                print(f"音声スレッドでエラーが発生しました: {e}")
                time.sleep(0.5)  # エラー時の短い遅延

    def is_busy(self):
        """音声出力中かどうかを確認"""
        return self.is_speaking or not self.speech_queue.empty()

    def clear_queue(self):
        """音声キューをクリア"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break