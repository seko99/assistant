"""
Enumerations and constants for the Speech Parrot application.
"""

from enum import Enum


class ParrotState(Enum):
    """Состояния процесса попугая"""
    LISTENING = "listening"      # Ожидание ключевой фразы
    RECORDING = "recording"      # Запись для распознавания
    TRANSCRIBING = "transcribing" # Распознавание речи
    SYNTHESIZING = "synthesizing" # Синтез речи
    PLAYING = "playing"          # Воспроизведение