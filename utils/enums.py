"""
Enumerations and constants for the Speech Assistant application.
"""

from enum import Enum


class AssistantState(Enum):
    """Состояния процесса ассистента"""
    LISTENING = "listening"      # Ожидание ключевой фразы
    RECORDING = "recording"      # Запись для распознавания
    TRANSCRIBING = "transcribing" # Распознавание речи
    SYNTHESIZING = "synthesizing" # Синтез речи
    PLAYING = "playing"          # Воспроизведение