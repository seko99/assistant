#!/usr/bin/env python3
"""
Speech Assistant API

Объединяет функциональность трех компонентов:
1. Vosk - детекция ключевых слов (wake word detection)
2. FasterWhisper - распознавание речи без определения пауз
3. Silero TTS - синтез речи

Процесс работы:
1. Ожидание ключевой фразы (vosk)
2. Запись речи для распознавания (faster-whisper)
3. Синтез и воспроизведение распознанного текста (silero)
4. Возврат к ожиданию ключевой фразы

Использование: python main.py
"""

import sys
import threading
import time

import numpy as np
import sounddevice as sd

from core.pause_detection import PauseDetector
from core.speech_recognition import SpeechRecognizer
from core.text_to_speech import TextToSpeech
from core.wake_word import WakeWordDetector
from utils.config import load_config
from utils.config_keys import ConfigKeys
from utils.enums import AssistantState


class SpeechAssistant:
    """Основной класс ассистента, объединяющий все компоненты"""

    def __init__(self, config_file='config.json', debug=False):
        self.config = load_config(config_file)
        if not self.config:
            raise ValueError("Не удалось загрузить конфигурацию")

        self.debug = debug

        # Компоненты
        self.wake_detector = WakeWordDetector(self.config, debug=debug)
        self.speech_recognizer = SpeechRecognizer(self.config)
        self.tts = TextToSpeech(self.config)
        self.pause_detector = PauseDetector(self.config, debug=debug)

        # Состояние
        self.state = AssistantState.LISTENING
        self.should_stop = threading.Event()

        # Аудио настройки
        self.sample_rate = self.config[ConfigKeys.WAKE_WORD][ConfigKeys.WakeWord.SAMPLE_RATE]
        self.chunk_size = self.config[ConfigKeys.WAKE_WORD][ConfigKeys.WakeWord.CHUNK_SIZE]

        # Буферы для записи
        self.recording_buffer = []
        self.recording_lock = threading.Lock()
        self.max_recording_duration = self.config[ConfigKeys.ASSISTANT][ConfigKeys.TTS.MAX_RECORDING_DURATION]
        self.recording_start_time = None
        self.recording_timer = None
        self.stop_reason = None  # для отслеживания причины остановки записи

    def initialize(self):
        """Инициализация всех компонентов"""
        print("🚀 Инициализация компонентов ассистента...")

        if not self.wake_detector.initialize():
            return False

        if not self.speech_recognizer.initialize():
            return False

        if not self.tts.initialize():
            return False

        print("✅ Все компоненты инициализированы")
        return True

    def audio_callback(self, indata, frames, time_info, status):
        """Колбэк для обработки аудио потока"""
        if status:
            print(f"⚠️ Ошибка аудио потока: {status}")
            return

        # DEBUG: проверяем, что колбэк вызывается
        if self.debug and hasattr(self, '_callback_count'):
            self._callback_count += 1
            if self._callback_count % 100 == 0:  # каждые 100 вызовов
                print(f"🔍 DEBUG: audio_callback вызван {self._callback_count} раз")
        elif self.debug:
            self._callback_count = 1
            print("🔍 DEBUG: audio_callback начал работу")

        audio_chunk = indata[:, 0]  # первый канал

        with self.recording_lock:
            if self.state == AssistantState.LISTENING:
                # Ищем ключевое слово
                wake_detected, result = self.wake_detector.detect_wake_word(audio_chunk)

                if wake_detected:
                    text, detection_time, pre_trigger_audio = result
                    print(f"🎉 Обнаружено ключевое слово: {text} (время: {detection_time:.3f}s)")
                    self._start_recording(pre_trigger_audio)
                elif self.debug and result:  # если есть любой текст
                    print(f"🔍 DEBUG: Vosk вернул текст: '{result}', wake_detected={wake_detected}")

            elif self.state == AssistantState.RECORDING:
                # Записываем аудио для распознавания
                self.recording_buffer.extend(audio_chunk)

                # Проверяем условия остановки записи
                if self.recording_start_time:
                    duration = time.time() - self.recording_start_time

                    # Проверяем детекцию пауз
                    if self.pause_detector.should_stop_recording(audio_chunk, duration):
                        self.stop_reason = "pause"
                        if self.debug:
                            print(f"🤫 Остановка по паузе (длительность: {duration:.1f}s)")
                        self._stop_recording_and_process()
                    # Проверяем максимальное время записи
                    elif duration >= self.max_recording_duration:
                        self.stop_reason = "timeout"
                        print(f"⏰ Достигнут лимит записи ({self.max_recording_duration}с)")
                        self._stop_recording_and_process()

    def _start_recording(self, pre_trigger_audio=None):
        """Начинает запись для распознавания"""
        self.state = AssistantState.RECORDING

        # Сбрасываем детектор пауз
        self.pause_detector.reset()
        self.stop_reason = None

        # Если есть pre-trigger аудио, используем его как начало записи
        if pre_trigger_audio is not None and len(pre_trigger_audio) > 0:
            self.recording_buffer = list(pre_trigger_audio)
            print(f"🔴 Начинаю запись с pre-trigger ({len(pre_trigger_audio)} сэмплов)...")
        else:
            self.recording_buffer = []
            print("🔴 Начинаю запись...")

        self.recording_start_time = time.time()

        # Отменяем предыдущий таймер если есть
        if self.recording_timer:
            self.recording_timer.cancel()

        # Запускаем новый таймер для остановки записи (как fallback)
        self.recording_timer = threading.Timer(
            self.max_recording_duration,
            lambda: self._stop_recording_and_process("timeout")
        )
        self.recording_timer.start()

    def _stop_recording_and_process(self, reason=None):
        """Останавливает запись и запускает обработку"""
        if self.state != AssistantState.RECORDING:
            return

        # Если причина не передана, используем сохраненную
        if reason is None:
            reason = self.stop_reason or "unknown"

        self.state = AssistantState.TRANSCRIBING
        duration = time.time() - self.recording_start_time if self.recording_start_time else 0

        # Отображаем причину остановки
        if reason == "pause":
            print(f"⏹️ Запись остановлена по паузе ({duration:.1f}с)")
        elif reason == "timeout":
            print(f"⏹️ Запись остановлена по таймауту ({duration:.1f}с)")
        else:
            print(f"⏹️ Запись остановлена ({duration:.1f}с)")

        # Копируем буфер для обработки в отдельном потоке
        audio_data = np.array(self.recording_buffer.copy(), dtype=np.float32)
        processing_thread = threading.Thread(
            target=self._process_recording,
            args=(audio_data,),
            daemon=True
        )
        processing_thread.start()

    def _process_recording(self, audio_data):
        """Обрабатывает записанное аудио (распознавание + синтез)"""
        try:
            if len(audio_data) == 0:
                print("⚠️ Пустая запись")
                self._reset_to_listening()
                return

            # Распознаем речь
            print("📝 Распознаю речь...")
            text = self.speech_recognizer.transcribe_audio(audio_data, self.sample_rate)

            if not text.strip():
                print("❌ Текст не распознан")
                self._reset_to_listening()
                return

            # Синтезируем и воспроизводим
            self.state = AssistantState.SYNTHESIZING
            success = self.tts.synthesize_and_play(text)

            if success:
                print("✅ Воспроизведение завершено")
            else:
                print("❌ Ошибка воспроизведения")

        except Exception as e:
            print(f"❌ Ошибка обработки записи: {e}")
        finally:
            self._reset_to_listening()

    def _reset_to_listening(self):
        """Возвращает состояние к прослушиванию ключевых слов"""
        with self.recording_lock:
            # Отменяем таймер если активен
            if self.recording_timer:
                self.recording_timer.cancel()
                self.recording_timer = None

            self.state = AssistantState.LISTENING
            self.recording_buffer = []
            self.recording_start_time = None
        print("👂 Жду ключевое слово...")

    def run(self):
        """Основной цикл работы ассистента"""
        print("🤖 Запуск речевого ассистента")
        print(f"   Ключевые слова: {self.wake_detector.keywords}")
        print(f"   Максимальная запись: {self.max_recording_duration}с")
        print("   Для остановки нажмите Ctrl+C")
        print()

        self._reset_to_listening()

        try:
            # Запускаем аудио поток
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype='float32'
            ):
                while not self.should_stop.is_set():
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n🛑 Остановка ассистента...")
            self.should_stop.set()
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            self.should_stop.set()

        print("✅ Ассистент остановлен")


def main():
    """Основная функция"""
    # Проверяем аргументы командной строки
    debug = "--debug" in sys.argv or "-d" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Speech Assistant - Речевой ассистент")
        print()
        print("Использование:")
        print("  python main.py [--debug] [--help]")
        print()
        print("Опции:")
        print("  --debug, -d    Включить отладочный вывод")
        print("  --help, -h     Показать эту справку")
        return 0

    try:
        assistant = SpeechAssistant(debug=debug)

        if debug:
            print("🔧 Режим отладки включен")

        if not assistant.initialize():
            print("❌ Не удалось инициализировать ассистента")
            return 1

        assistant.run()
        return 0

    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())