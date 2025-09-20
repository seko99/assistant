"""
Text-to-speech module using Silero TTS.
"""

import time
import os
from pathlib import Path
from typing import Optional

import sounddevice as sd
import torch
import torchaudio

from utils.config_keys import ConfigKeys


class TextToSpeech:
    """Синтез речи на основе Silero TTS"""

    def __init__(self, config):
        self.config = config
        self.assistant_config = config[ConfigKeys.ASSISTANT]
        self.model = None
        self.sample_rate = self.assistant_config[ConfigKeys.TTS.TTS_SAMPLE_RATE]
        self.speaker = self.assistant_config[ConfigKeys.TTS.TTS_SPEAKER]
        self.use_accentizer = self.assistant_config.get(ConfigKeys.TTS.USE_ACCENTIZER, False)
        self.accentizer = None

    def initialize(self):
        """Инициализация модели Silero TTS"""
        try:
            print("🔍 Загрузка Silero TTS...")

            # Загружаем модель Silero
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model, example_text = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker='ru_v3'
            )
            self.model.to(device)

            # Инициализируем акцентизатор если нужно
            if self.use_accentizer:
                try:
                    from ruaccent import RUAccent
                    self.accentizer = RUAccent()
                    self.accentizer.load(omograph_model_size='turbo', use_dictionary=True)
                    print("✅ RUAccent загружен")
                except ImportError:
                    print("⚠️ RUAccent не установлен, синтез без ударений")
                    self.use_accentizer = False

            print(f"✅ Silero TTS готов (динамик: {self.speaker})")
            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации Silero TTS: {e}")
            return False

    def synthesize_and_play(self, text, voice_override: Optional[str] = None, save_path: Optional[str] = None):
        """
        Синтезирует и воспроизводит речь

        Args:
            text: Текст для синтеза
            voice_override: Голос для использования (переопределяет настройку по умолчанию)
            save_path: Путь для сохранения аудио файла (опционально)
        """
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
            print(f"🗣️ Синтезируем ({speaker_to_use}): {text} (время: {synthesis_time:.3f}s)")

            # Сохраняем в файл если указан путь
            if save_path:
                self._save_audio_file(audio, save_path)
                print(f"💾 Аудио сохранено: {save_path}")

            # Воспроизводим
            sd.play(audio_np, self.sample_rate)
            sd.wait()  # Ждем окончания воспроизведения

            return True

        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")
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
                print(f"💾 Аудио сохранено: {save_path}")
                return save_path

            return None

        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")
            return None

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