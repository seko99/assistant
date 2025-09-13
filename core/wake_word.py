"""
Wake word detection module using Vosk.
"""

import json
import os
import time
from collections import deque

import numpy as np
import vosk

from utils.audio_utils import convert_float32_to_int16
from utils.config_keys import ConfigKeys


class WakeWordDetector:
    """Детектор ключевых слов на основе Vosk"""

    def __init__(self, config, debug=False):
        self.config = config
        self.wake_config = config[ConfigKeys.WAKE_WORD]
        self.model = None
        self.recognizer = None
        self.keywords = self.wake_config[ConfigKeys.WakeWord.KEYWORDS]
        self.debug = debug  # Для отладочного вывода

        # Кольцевой буфер для pre-trigger аудио
        self.pre_trigger_duration = self.wake_config.get(ConfigKeys.WakeWord.PRE_TRIGGER_DURATION, 3.0)
        self.sample_rate = self.wake_config[ConfigKeys.WakeWord.SAMPLE_RATE]
        self.chunk_size = self.wake_config[ConfigKeys.WakeWord.CHUNK_SIZE]
        buffer_size = int(self.sample_rate * self.pre_trigger_duration)
        self.audio_buffer = deque(maxlen=buffer_size)

    def initialize(self):
        """Инициализация модели Vosk"""
        model_path = self.wake_config[ConfigKeys.WakeWord.MODEL_PATH]

        if not os.path.exists(model_path):
            print(f"❌ Модель Vosk не найдена: {model_path}")
            print("   Скачайте модель с https://alphacephei.com/vosk/models")
            return False

        try:
            print(f"🔍 Загрузка модели Vosk: {model_path}")
            self.model = vosk.Model(model_path)

            # Создаем распознаватель с ключевыми словами в JSON формате
            keywords_json = json.dumps(self.keywords, ensure_ascii=False)
            sample_rate = self.wake_config[ConfigKeys.WakeWord.SAMPLE_RATE]
            self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate, keywords_json)

            print(f"✅ Vosk готов к работе с ключевыми словами: {self.keywords}")
            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации Vosk: {e}")
            return False

    def add_audio_to_buffer(self, audio_data):
        """Добавляет аудио данные в кольцевой буфер"""
        self.audio_buffer.extend(audio_data)

    def get_pre_trigger_audio(self):
        """Возвращает накопленное pre-trigger аудио"""
        return np.array(list(self.audio_buffer), dtype=np.float32)

    def detect_wake_word(self, audio_data):
        """Проверяет наличие ключевого слова в аудио данных"""
        if not self.recognizer:
            if self.debug:
                print("🔍 DEBUG: recognizer не инициализирован!")
            return False, ""

        # Добавляем аудио в буфер
        self.add_audio_to_buffer(audio_data)

        # DEBUG счетчик вызовов
        if self.debug:
            if not hasattr(self, '_detect_count'):
                self._detect_count = 0
                print("🔍 DEBUG: detect_wake_word начал работу")
            self._detect_count += 1
            if self._detect_count % 50 == 0:  # каждые 50 вызовов
                print(f"🔍 DEBUG: detect_wake_word вызван {self._detect_count} раз")

        start_time = time.time()
        try:
            # Конвертируем float32 в int16 для Vosk
            audio_int16 = convert_float32_to_int16(audio_data)

            # Проверяем финальный результат
            if self.recognizer.AcceptWaveform(audio_int16):
                result = json.loads(self.recognizer.Result())
                if 'text' in result and result['text']:
                    text = result['text'].lower()
                    if self.debug:
                        print(f"🔍 Vosk финальный результат: '{text}'")
                    # Проверяем наличие любого из ключевых слов
                    if any(keyword in text for keyword in self.keywords):
                        detection_time = time.time() - start_time
                        # Получаем pre-trigger аудио
                        pre_trigger_audio = self.get_pre_trigger_audio()
                        return True, (text, detection_time, pre_trigger_audio)
            return False, ""

        except Exception as e:
            print(f"⚠️ Ошибка детекции ключевого слова: {e}")
            return False, ""