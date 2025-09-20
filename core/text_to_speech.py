"""
Text-to-speech module using Silero TTS.
"""

import time
import os
from pathlib import Path
from typing import Optional, Union

import sounddevice as sd
import torch
import torchaudio

from utils.config_keys import ConfigKeys, ConfigSections
from utils.logger import get_logger


class TextToSpeech:
    """Синтез речи на основе Silero TTS"""

    def __init__(self, config):
        self.config = config
        self.assistant_config = config[ConfigSections.ASSISTANT]
        self.model = None
        self.sample_rate = self.assistant_config[ConfigKeys.TTS.TTS_SAMPLE_RATE]
        self.speaker = self.assistant_config[ConfigKeys.TTS.TTS_SPEAKER]
        self.use_accentizer = self.assistant_config.get(ConfigKeys.TTS.USE_ACCENTIZER, False)
        self.playback_device = self.assistant_config.get('playback_device', None)
        self.offline_mode = False  # Флаг для офлайн режима
        self.accentizer = None
        self.logger = get_logger('tts')

    def initialize(self):
        """Инициализация модели Silero TTS с graceful fallback"""
        try:
            self.logger.info("Загрузка Silero TTS...")

            # Проверяем наличие локального кэша модели
            model_loaded = False

            # Пытаемся загрузить модель с таймаутом
            try:
                device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model, example_text = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language='ru',
                    speaker='ru_v3',
                    force_reload=False  # Используем кэш если есть
                )
                self.model.to(device)
                model_loaded = True
                self.logger.info("Модель Silero успешно загружена")

            except Exception as model_error:
                self.logger.warning(f"Ошибка загрузки модели Silero: {model_error}")
                self.logger.warning("Проверьте интернет-соединение или локальный кэш")

                # Пытаемся работать в офлайн режиме
                self.offline_mode = True
                self.logger.info("Переход в офлайн режим (только сохранение в файл)")

            # Инициализируем акцентизатор если нужно
            if self.use_accentizer and not self.offline_mode:
                try:
                    from ruaccent import RUAccent
                    self.accentizer = RUAccent()
                    self.accentizer.load(omograph_model_size='turbo', use_dictionary=True)
                    self.logger.info("RUAccent загружен")
                except ImportError:
                    self.logger.warning("RUAccent не установлен, синтез без ударений")
                    self.use_accentizer = False
                except Exception as accent_error:
                    self.logger.warning(f"Ошибка загрузки RUAccent: {accent_error}")
                    self.use_accentizer = False

            # Проверяем доступность аудио устройств
            if not self.offline_mode:
                self._check_audio_device()

            if model_loaded:
                self.logger.info(f"Silero TTS готов (динамик: {self.speaker})")
            else:
                self.logger.warning("TTS работает в ограниченном режиме")

            return True  # Возвращаем True даже в офлайн режиме

        except Exception as e:
            self.logger.critical(f"Критическая ошибка инициализации TTS: {e}")
            return False

    def synthesize_and_play(self, text, voice_override: Optional[str] = None, save_path: Optional[str] = None):
        """
        Синтезирует и воспроизводит речь

        Args:
            text: Текст для синтеза
            voice_override: Голос для использования (переопределяет настройку по умолчанию)
            save_path: Путь для сохранения аудио файла (опционально)
        """
        if self.offline_mode:
            self.logger.warning("Офлайн режим: синтез недоступен. Используйте synthesize_only.")
            return False

        if not self.model or not text.strip():
            return False

        start_time = time.time()
        try:
            # Определяем голос для использования
            speaker_to_use = voice_override if voice_override else self.speaker

            # Обрабатываем текст акцентизатором если нужно
            processed_text = text
            if self.use_accentizer and self.accentizer:
                processed_text = self.accentizer.process_all(text)

            # Генерируем аудио
            audio = self.model.apply_tts(
                text=processed_text,
                speaker=speaker_to_use,
                sample_rate=self.sample_rate
            )

            audio_np = audio.detach().cpu().numpy()
            synthesis_time = time.time() - start_time
            self.logger.info(f"Синтезируем ({speaker_to_use}): {text} (время: {synthesis_time:.3f}s)")

            # Сохраняем в файл если указан путь
            if save_path:
                self._save_audio_file(audio, save_path)
                self.logger.info(f"Аудио сохранено: {save_path}")

            # Воспроизводим только если не в офлайн режиме
            if not self.offline_mode:
                try:
                    device_id = self.playback_device if self.playback_device is not None else sd.default.device[1]
                    sd.play(audio_np, self.sample_rate, device=device_id)
                    sd.wait()  # Ждем окончания воспроизведения
                except Exception as audio_error:
                    self.logger.error(f"Ошибка воспроизведения аудио: {audio_error}")
                    return False
            else:
                self.logger.info("Офлайн режим: воспроизведение пропущено")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка синтеза речи: {e}")
            return False

    def synthesize_only(self, text, voice_override: Optional[str] = None, save_path: Optional[str] = None):
        """
        Синтезирует речь без воспроизведения (для режима --no-audio)

        Args:
            text: Текст для синтеза
            voice_override: Голос для использования
            save_path: Путь для сохранения аудио файла

        Returns:
            Путь к сохраненному файлу или None
        """
        if not self.model or not text.strip():
            return None

        start_time = time.time()
        try:
            # Определяем голос для использования
            speaker_to_use = voice_override if voice_override else self.speaker

            # Обрабатываем текст акцентизатором если нужно
            processed_text = text
            if self.use_accentizer and self.accentizer:
                processed_text = self.accentizer.process_all(text)

            # Генерируем аудио
            audio = self.model.apply_tts(
                text=processed_text,
                speaker=speaker_to_use,
                sample_rate=self.sample_rate
            )

            synthesis_time = time.time() - start_time
            print(f"🔄 Синтез ({speaker_to_use}): {text} (время: {synthesis_time:.3f}s)")

            # Сохраняем в файл
            if save_path:
                self._save_audio_file(audio, save_path)
                self.logger.info(f"Аудио сохранено: {save_path}")
                return save_path

            return None

        except Exception as e:
            self.logger.error(f"Ошибка синтеза речи: {e}")
            return None

    def _check_audio_device(self):
        """Проверяет доступность аудио устройств"""
        try:
            if self.playback_device is not None:
                # Проверяем указанное устройство
                devices = sd.query_devices()
                if self.playback_device >= len(devices):
                    print(f"⚠️ Устройство {self.playback_device} не найдено, используется по умолчанию")
                    self.playback_device = None
                else:
                    device_info = devices[self.playback_device]
                    print(f"🔊 Аудио устройство: {device_info['name']}")
            else:
                # Используем устройство по умолчанию
                default_device = sd.default.device[1]
                device_info = sd.query_devices(default_device)
                print(f"🔊 Аудио устройство по умолчанию: {device_info['name']}")

        except Exception as e:
            print(f"⚠️ Ошибка проверки аудио устройств: {e}")
            self.playback_device = None

    def _save_audio_file(self, audio_tensor, file_path: str):
        """Сохраняет аудио тензор в файл"""
        try:
            # Создаем директорию если не существует
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Преобразуем в правильный формат для сохранения
            audio_to_save = audio_tensor.unsqueeze(0) if audio_tensor.dim() == 1 else audio_tensor

            # Сохраняем в WAV формате
            torchaudio.save(file_path, audio_to_save, self.sample_rate)

        except Exception as e:
            print(f"❌ Ошибка сохранения аудио файла {file_path}: {e}")
            raise