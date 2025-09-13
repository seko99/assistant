"""
Text-to-speech module using Silero TTS.
"""

import time

import sounddevice as sd
import torch

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

    def synthesize_and_play(self, text):
        """Синтезирует и воспроизводит речь"""
        if not self.model or not text.strip():
            return False

        start_time = time.time()
        try:
            # Обрабатываем текст акцентизатором если нужно
            processed_text = text
            if self.use_accentizer and self.accentizer:
                processed_text = self.accentizer.process_all(text)

            # Генерируем аудио
            audio = self.model.apply_tts(
                text=processed_text,
                speaker=self.speaker,
                sample_rate=self.sample_rate
            )

            # Воспроизводим
            audio_np = audio.detach().cpu().numpy()
            synthesis_time = time.time() - start_time
            print(f"🗣️ Синтезируем: {text} (время: {synthesis_time:.3f}s)")

            sd.play(audio_np, self.sample_rate)
            sd.wait()  # Ждем окончания воспроизведения

            return True

        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")
            return False