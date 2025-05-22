"""
音声出力モジュール - プラットフォーム対応
"""
import os
import subprocess
import queue
import threading
import time
import logging
from typing import Optional

import config
from models import AudioRequest

logger = logging.getLogger(__name__)

class AudioManager:
    """音声出力管理"""
    
    def __init__(self):
        self.audio_queue = queue.PriorityQueue()
        self.is_speaking = False
        self.stop_requested = False
        self.pyttsx3_engine = None
        
        # 音声処理スレッド開始
        self.audio_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.audio_thread.start()
        
        # 利用可能な音声合成方法をチェック
        self._check_available_methods()
        
        logger.info("音声管理システムを初期化")
    
    def _check_available_methods(self):
        """利用可能な音声合成方法をチェック"""
        self.available_methods = []
        
        # OS標準コマンドをチェック
        for cmd_template in config.CURRENT_TTS_COMMANDS:
            test_cmd = cmd_template.format(text="test")
            if self._test_command(test_cmd):
                self.available_methods.append("system")
                break
        
        # pyttsx3をチェック
        try:
            import pyttsx3
            engine = pyttsx3.init()
            self.pyttsx3_engine = engine
            self.available_methods.append("pyttsx3")
            logger.info("pyttsx3 音声エンジンが利用可能")
        except Exception as e:
            logger.warning(f"pyttsx3 初期化失敗: {e}")
        
        if not self.available_methods:
            self.available_methods.append("print")  # フォールバック
            logger.warning("音声出力がコンソール出力にフォールバック")
        
        logger.info(f"利用可能な音声方法: {self.available_methods}")
    
    def _test_command(self, command: str) -> bool:
        """コマンドの実行可能性をテスト"""
        try:
            # Windowsの場合
            if config.IS_WINDOWS:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    timeout=5
                )
                return result.returncode == 0
            # Unix系の場合
            else:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    timeout=5,
                    text=True
                )
                return result.returncode == 0
        except Exception:
            return False
    
    def speak(self, text: str, priority: int = 1, method: Optional[str] = None):
        """音声出力をキューに追加"""
        if not text.strip():
            return
        
        # デフォルト方法を決定
        if method is None:
            if config.USE_SYSTEM_TTS and "system" in self.available_methods:
                method = "system"
            elif "pyttsx3" in self.available_methods:
                method = "pyttsx3"
            else:
                method = "print"
        
        audio_request = AudioRequest(text=text, priority=priority, method=method)
        
        try:
            # 優先度付きキューに追加（数値が小さいほど高優先）
            self.audio_queue.put((priority, time.time(), audio_request))
            logger.debug(f"音声キューに追加: {text[:50]}...")
        except Exception as e:
            logger.error(f"音声キューへの追加エラー: {e}")
    
    def speak_immediately(self, text: str, method: Optional[str] = None):
        """即座に音声出力（キューをバイパス）"""
        if not text.strip():
            return
        
        if method is None:
            method = self.available_methods[0] if self.available_methods else "print"
        
        try:
            self._execute_speech(text, method)
        except Exception as e:
            logger.error(f"即座音声出力エラー: {e}")
            self._fallback_output(text)
    
    def _process_audio_queue(self):
        """音声キューを処理するスレッド"""
        while not self.stop_requested:
            try:
                # キューからリクエストを取得（タイムアウト付き）
                try:
                    priority, timestamp, audio_request = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                self.is_speaking = True
                
                # 音声出力実行
                self._execute_speech(audio_request.text, audio_request.method)
                
                self.is_speaking = False
                self.audio_queue.task_done()
                
            except Exception as e:
                logger.error(f"音声処理スレッドエラー: {e}")
                self.is_speaking = False
                time.sleep(0.1)
    
    def _execute_speech(self, text: str, method: str):
        """音声出力実行"""
        try:
            if method == "system":
                self._system_speech(text)
            elif method == "pyttsx3":
                self._pyttsx3_speech(text)
            else:
                self._fallback_output(text)
                
        except Exception as e:
            logger.error(f"音声出力実行エラー: {e}")
            self._fallback_output(text)
    
    def _system_speech(self, text: str):
        """OS標準の音声合成"""
        if not config.CURRENT_TTS_COMMANDS:
            raise Exception("OS標準音声コマンドが設定されていません")
        
        # テキストのエスケープ処理
        escaped_text = text.replace('"', '\\"').replace("'", "\\'")
        
        for cmd_template in config.CURRENT_TTS_COMMANDS:
            try:
                command = cmd_template.format(text=escaped_text)
                
                if config.IS_WINDOWS:
                    # Windowsの場合
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        timeout=30
                    )
                else:
                    # Unix系の場合
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        timeout=30,
                        text=True
                    )
                
                if result.returncode == 0:
                    logger.debug(f"システム音声出力成功: {command}")
                    return
                else:
                    logger.warning(f"システム音声コマンド失敗: {command}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"システム音声コマンドタイムアウト: {command}")
            except Exception as e:
                logger.error(f"システム音声コマンドエラー: {e}")
        
        # 全てのコマンドが失敗した場合
        raise Exception("全てのシステム音声コマンドが失敗")
    
    def _pyttsx3_speech(self, text: str):
        """pyttsx3による音声出力"""
        if not self.pyttsx3_engine:
            raise Exception("pyttsx3エンジンが初期化されていません")
        
        try:
            # エンジン設定
            self.pyttsx3_engine.setProperty('rate', config.VOICE_RATE)
            self.pyttsx3_engine.setProperty('volume', config.VOICE_VOLUME)
            
            # 音声出力
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            
            logger.debug("pyttsx3音声出力成功")
            
        except Exception as e:
            logger.error(f"pyttsx3音声出力エラー: {e}")
            raise
    
    def _fallback_output(self, text: str):
        """フォールバック出力（コンソール）"""
        separator = "=" * 60
        print(f"\n{separator}")
        print(f"【音声出力】 {text}")
        print(f"{separator}\n")
        logger.info(f"フォールバック音声出力: {text}")
    
    def clear_queue(self):
        """音声キューをクリア"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
        logger.info("音声キューをクリア")
    
    def is_busy(self) -> bool:
        """音声出力中かどうか"""
        return self.is_speaking or not self.audio_queue.empty()
    
    def stop(self):
        """音声管理システム停止"""
        self.stop_requested = True
        self.clear_queue()
        
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.stop()
            except:
                pass
        
        logger.info("音声管理システム停止")
    
    def get_status(self) -> dict:
        """音声システム状態取得"""
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.audio_queue.qsize(),
            "available_methods": self.available_methods,
            "stop_requested": self.stop_requested
        }