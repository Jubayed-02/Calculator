import pyttsx3
import speech_recognition as sr
from PyQt5.QtCore import QThread, pyqtSignal
import re

class VoiceThread(QThread):
    text_heard = pyqtSignal(str)
    status_update = pyqtSignal(str)
    speaking_finished = pyqtSignal()  # New signal
    
    # ... existing code ...
    
    def speak_and_wait(self, text):
        """Speak text and emit signal when done"""
        if self.tts_engine:
            clean_text = str(text).replace('*', ' times ').replace('/', ' divided by ')
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
            self.speaking_finished.emit()
    
    def __init__(self):
        super().__init__()
        self.tts_engine = None
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self._init_tts()
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            # Try to set a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"TTS initialization error: {e}")
    
    def speak(self, text):
        """Speak text aloud"""
        if self.tts_engine:
            # Clean text for speaking
            clean_text = str(text).replace('*', ' times ').replace('/', ' divided by ')
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
    
    def run(self):
        """Listen for voice input"""
        self.is_listening = True
        self.status_update.emit("Listening...")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            self.status_update.emit("Processing...")
            
            try:
                text = self.recognizer.recognize_google(audio)
                
                # Clean the recognized text for calculator
                word_to_op = {
                    'plus': '+', 'minus': '-', 'times': '*', 'multiplied by': '*',
                    'divided by': '/', 'over': '/', 'to the power of': '^',
                    'squared': '^2', 'cubed': '^3', 'percent': '%',
                    'point': '.', 'dot': '.'
                }
                
                # Replace words with operators
                calc_text = text.lower()
                for word, op in word_to_op.items():
                    calc_text = calc_text.replace(word, op)
                
                # Remove non-math characters
                calc_text = re.sub(r'[^0-9\.\+\-\*/\(\)\^% ]', '', calc_text)
                calc_text = calc_text.replace(' ', '')
                
                if calc_text:
                    self.text_heard.emit(calc_text)
                    self.status_update.emit("Ready")
                else:
                    self.status_update.emit("No math detected")
                    
            except sr.UnknownValueError:
                self.status_update.emit("Could not understand audio")
            except sr.RequestError as e:
                self.status_update.emit(f"Recognition error: {e}")
                
        except Exception as e:
            self.status_update.emit(f"Microphone error: {e}")
        
        self.is_listening = False