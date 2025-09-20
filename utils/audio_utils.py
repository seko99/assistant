"""
Audio utilities and helper functions for the Speech Assistant application.
"""

import numpy as np


def calculate_energy(audio_chunk):
    """
    Вычисляет RMS энергию аудио чанка.

    Args:
        audio_chunk: numpy array с аудио данными

    Returns:
        float: RMS энергия сигнала
    """
    return np.sqrt(np.mean(audio_chunk**2))


def convert_float32_to_int16(audio_data):
    """
    Конвертирует аудио из float32 в int16 формат.

    Args:
        audio_data: numpy array в формате float32

    Returns:
        bytes: аудио данные в формате int16
    """
    # Клиппинг аудио данных в диапазон [-1.0, 1.0] перед конвертацией
    clipped_audio = np.clip(audio_data, -1.0, 1.0)
    return (clipped_audio * 32767).astype(np.int16).tobytes()