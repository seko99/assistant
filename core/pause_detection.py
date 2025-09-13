"""
Pause detection module for speech recording.
"""

import numpy as np

from utils.audio_utils import calculate_energy
from utils.config_keys import ConfigKeys


class PauseDetector:
    """Детектор пауз в речи на основе анализа энергии сигнала"""

    def __init__(self, config, debug=False):
        self.config = config
        self.voice_config = config[ConfigKeys.VOICE_DETECTION]
        self.debug = debug

        # Параметры детекции
        self.pause_threshold = self.voice_config.get(ConfigKeys.VoiceDetection.PAUSE_THRESHOLD, 3.0)  # секунды
        self.voice_energy_threshold = self.voice_config.get(ConfigKeys.VoiceDetection.VOICE_ENERGY_THRESHOLD, 0.01)
        self.min_recording_duration = self.voice_config.get(ConfigKeys.VoiceDetection.MIN_RECORDING_DURATION, 0.5)  # секунды
        self.pause_detection_enabled = self.voice_config.get(ConfigKeys.VoiceDetection.PAUSE_DETECTION_ENABLED, True)

        # Состояние
        self.sample_rate = config[ConfigKeys.WAKE_WORD][ConfigKeys.WakeWord.SAMPLE_RATE]  # используем sample_rate от wake_word
        self.chunk_size = config[ConfigKeys.WAKE_WORD][ConfigKeys.WakeWord.CHUNK_SIZE]
        self.samples_per_second = self.sample_rate / self.chunk_size

        # Счетчики
        self.reset()

    def reset(self):
        """Сбрасывает состояние детектора"""
        self.silence_chunks = 0
        self.total_chunks = 0
        self.noise_level = None
        self.calibration_samples = []

    def calibrate_noise_level(self, audio_chunk):
        """Калибрует уровень фонового шума"""
        if len(self.calibration_samples) < 10:  # собираем первые 10 чанков для калибровки
            energy = calculate_energy(audio_chunk)
            self.calibration_samples.append(energy)

            if len(self.calibration_samples) == 10:
                self.noise_level = np.mean(self.calibration_samples) * 2.0  # немного выше среднего фона
                if self.debug:
                    print(f"🔊 Калибровка шума: {self.noise_level:.6f}")

    def is_voice_detected(self, audio_chunk):
        """Определяет, есть ли голос в аудио чанке"""
        if not self.pause_detection_enabled:
            return True  # всегда считаем, что голос есть

        energy = calculate_energy(audio_chunk)

        # Калибруем если нужно
        if self.noise_level is None:
            self.calibrate_noise_level(audio_chunk)
            return True  # во время калибровки считаем что голос есть

        # Используем адаптивный порог: максимум из настроенного порога и калиброванного уровня шума
        threshold = max(self.voice_energy_threshold, self.noise_level)
        is_voice = energy > threshold

        if self.debug and self.total_chunks % 10 == 0:  # каждые 10 чанков
            print(f"🔊 Энергия: {energy:.6f}, порог: {threshold:.6f}, голос: {is_voice}")

        return is_voice

    def should_stop_recording(self, audio_chunk, recording_duration):
        """Определяет, нужно ли остановить запись"""
        if not self.pause_detection_enabled:
            return False

        # Минимальная длительность записи должна быть соблюдена
        if recording_duration < self.min_recording_duration:
            return False

        self.total_chunks += 1

        # Проверяем наличие голоса
        if self.is_voice_detected(audio_chunk):
            self.silence_chunks = 0  # сброс счетчика тишины
        else:
            self.silence_chunks += 1

        # Вычисляем время тишины
        silence_duration = self.silence_chunks / self.samples_per_second

        if self.debug and self.silence_chunks > 0 and self.silence_chunks % 5 == 0:
            print(f"🤫 Тишина: {silence_duration:.1f}s из {self.pause_threshold}s")

        # Останавливаем запись при превышении порога тишины
        return silence_duration >= self.pause_threshold