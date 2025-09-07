import threading
import queue
import time
from typing import Optional, Callable


class VoiceService:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        self.microphone_available = False
        self.tts_available = False
        
        # Try to initialize speech recognition
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.microphone_available = True
            self._calibrate_microphone()
        except Exception as e:
            pass
            
        # Try to initialize TTS
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_available = True
            self._configure_tts()
        except Exception as e:
            pass
            
    def _configure_tts(self):
        """Configure text-to-speech settings"""
        if not self.tts_available:
            return
        
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'english' in voice.name.lower() and 'female' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            pass
        
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        if not self.microphone_available:
            return
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
        except Exception as e:
            pass
        
    def speak(self, text: str, callback: Optional[Callable] = None):
        """Convert text to speech"""
        if not self.tts_available:
            if callback:
                callback()
            return
        
        if self.is_speaking:
            return
        
        self.is_speaking = True
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            if callback:
                callback()
        except Exception as e:
            pass
        finally:
            self.is_speaking = False
    
    def speak_async(self, text: str, callback: Optional[Callable] = None):
        """Convert text to speech asynchronously"""
        thread = threading.Thread(target=self.speak, args=(text, callback))
        thread.daemon = True
        thread.start()
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen for speech input and return transcribed text"""
        if not self.microphone_available:
            return None
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            text = self.recognizer.recognize_google(audio)
            return text.lower().strip()
            
        except Exception as e:
            return None
    
    def listen_async(self, callback: Callable[[Optional[str]], None], 
                    timeout: int = 5, phrase_time_limit: int = 10):
        """Listen for speech input asynchronously"""
        def listen_worker():
            result = self.listen(timeout, phrase_time_limit)
            callback(result)
        
        thread = threading.Thread(target=listen_worker)
        thread.daemon = True
        thread.start()
    
    def start_continuous_listening(self, callback: Callable[[str], None]):
        """Start continuous listening mode"""
        if not self.microphone_available:
            return
        
        self.is_listening = True
        
        def continuous_listen():
            while self.is_listening:
                try:
                    text = self.listen(timeout=1, phrase_time_limit=5)
                    if text:
                        callback(text)
                except Exception as e:
                    time.sleep(0.1)
        
        thread = threading.Thread(target=continuous_listen)
        thread.daemon = True
        thread.start()
    
    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        self.is_listening = False
    
    def is_available(self) -> bool:
        """Check if voice services are available"""
        return self.tts_available or self.microphone_available
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        if not self.tts_available:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            return [{"id": voice.id, "name": voice.name} for voice in voices] if voices else []
        except Exception as e:
            return []
    
    def set_voice(self, voice_id: str):
        """Set TTS voice by ID"""
        if not self.tts_available:
            return False
        
        try:
            self.tts_engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            return False
