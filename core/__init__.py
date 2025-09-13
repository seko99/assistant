"""
Core modules for Speech Parrot application.
"""

from .pause_detection import PauseDetector
from .speech_recognition import SpeechRecognizer
from .text_to_speech import TextToSpeech
from .wake_word import WakeWordDetector

__all__ = [
    'WakeWordDetector',
    'SpeechRecognizer',
    'TextToSpeech',
    'PauseDetector'
]