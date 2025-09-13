"""
Speech recognition module using FasterWhisper.
"""

import os
import time

import soundfile as sf
import torch
from faster_whisper import WhisperModel

from utils.config_keys import ConfigKeys


class SpeechRecognizer:
    """Распознаватель речи на основе FasterWhisper (упрощенная версия voice_recorder.py)"""

    def __init__(self, config):
        self.config = config
        self.transcription_config = config[ConfigKeys.TRANSCRIPTION]
        self.whisper_model = None

    def initialize(self):
        """Инициализация модели FasterWhisper"""
        try:
            model_size = self.transcription_config.get(ConfigKeys.Transcription.WHISPER_MODEL, 'base')
            device = self.transcription_config.get(ConfigKeys.Transcription.DEVICE, 'auto')
            compute_type = self.transcription_config.get(ConfigKeys.Transcription.COMPUTE_TYPE, 'auto')

            # Автоопределение устройства если нужно
            if device == 'auto' or compute_type == 'auto':
                device, compute_type = self._detect_optimal_settings()

            print(f"🔍 Загрузка FasterWhisper: {model_size}/{device}/{compute_type}")

            self.whisper_model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )

            print(f"✅ FasterWhisper готов к работе")
            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации FasterWhisper: {e}")
            return False

    def _detect_optimal_settings(self):
        """Простое автоопределение настроек устройства"""
        try:
            # Проверяем доступность CUDA
            if torch.cuda.is_available():
                return "cuda", "float16"
        except:
            pass
        return "cpu", "int8"

    def transcribe_audio(self, audio_data, sample_rate):
        """Транскрибирует аудио в текст"""
        if not self.whisper_model:
            return ""

        start_time = time.time()
        try:
            # Сохраняем временный файл для FasterWhisper
            temp_filename = f"temp_recording_{int(time.time())}.wav"
            sf.write(temp_filename, audio_data, sample_rate)

            # Транскрибируем
            language = self.transcription_config.get(ConfigKeys.Transcription.LANGUAGE, 'ru')
            beam_size = self.transcription_config.get(ConfigKeys.Transcription.BEAM_SIZE, 5)

            segments, info = self.whisper_model.transcribe(
                temp_filename,
                language=language,
                beam_size=beam_size,
                word_timestamps=False
            )

            # Собираем текст
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)

            text = " ".join(text_segments).strip()
            transcription_time = time.time() - start_time

            # Удаляем временный файл
            try:
                os.remove(temp_filename)
            except:
                pass

            if text.strip():
                print(f"📄 Распознано: {text} (время: {transcription_time:.3f}s)")

            return text

        except Exception as e:
            print(f"❌ Ошибка транскрипции: {e}")
            return ""