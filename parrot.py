#!/usr/bin/env python3
"""
Speech Parrot API

Объединяет функциональность трех компонентов:
1. Vosk - детекция ключевых слов (wake word detection)  
2. FasterWhisper - распознавание речи без определения пауз
3. Silero TTS - синтез речи

Процесс работы:
1. Ожидание ключевой фразы (vosk)
2. Запись речи для распознавания (faster-whisper)
3. Синтез и воспроизведение распознанного текста (silero)
4. Возврат к ожиданию ключевой фразы

Использование: python parrot.py
"""

import json
import os
import threading
import time
from collections import deque
from enum import Enum

import numpy as np
import sounddevice as sd
import soundfile as sf
import vosk
import torch
from faster_whisper import WhisperModel


class ParrotState(Enum):
    """Состояния процесса попугая"""
    LISTENING = "listening"      # Ожидание ключевой фразы
    RECORDING = "recording"      # Запись для распознавания  
    TRANSCRIBING = "transcribing" # Распознавание речи
    SYNTHESIZING = "synthesizing" # Синтез речи
    PLAYING = "playing"          # Воспроизведение


def load_config(config_file='config.json'):
    """Загружает конфигурацию из JSON файла"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл конфигурации {config_file} не найден")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в файле конфигурации: {e}")
        return None


class WakeWordDetector:
    """Детектор ключевых слов на основе Vosk"""
    
    def __init__(self, config, debug=False):
        self.config = config
        self.wake_config = config['wake_word']
        self.model = None
        self.recognizer = None
        self.keywords = self.wake_config['keywords']
        self.debug = debug  # Для отладочного вывода
        
        # Кольцевой буфер для pre-trigger аудио
        self.pre_trigger_duration = self.wake_config.get('pre_trigger_duration', 3.0)
        self.sample_rate = self.wake_config['sample_rate']
        self.chunk_size = self.wake_config['chunk_size']
        buffer_size = int(self.sample_rate * self.pre_trigger_duration)
        self.audio_buffer = deque(maxlen=buffer_size)
        
    def initialize(self):
        """Инициализация модели Vosk"""
        model_path = self.wake_config['model_path']
        
        if not os.path.exists(model_path):
            print(f"❌ Модель Vosk не найдена: {model_path}")
            print("   Скачайте модель с https://alphacephei.com/vosk/models")
            return False
            
        try:
            print(f"🔍 Загрузка модели Vosk: {model_path}")
            self.model = vosk.Model(model_path)
            
            # Создаем распознаватель с ключевыми словами в JSON формате
            keywords_json = json.dumps(self.keywords)
            sample_rate = self.wake_config['sample_rate']
            self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate, '["иннокентий"]')
            
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
            audio_int16 = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Проверяем финальный результат
            if self.recognizer.AcceptWaveform(audio_int16):
                result = json.loads(self.recognizer.Result())
                if 'text' in result and result['text']:
                    text = result['text'].lower()
                    if self.debug:
                        print(f"🔍 Vosk финальный результат: '{text}'")
                    # Проверяем наличие любого из ключевых слов
                    if 'иннокентий' in text:
                        detection_time = time.time() - start_time
                        # Получаем pre-trigger аудио
                        pre_trigger_audio = self.get_pre_trigger_audio()
                        return True, (text, detection_time, pre_trigger_audio)
            return False, ""
            
        except Exception as e:
            print(f"⚠️ Ошибка детекции ключевого слова: {e}")
            return False, ""


class SpeechRecognizer:
    """Распознаватель речи на основе FasterWhisper (упрощенная версия voice_recorder.py)"""
    
    def __init__(self, config):
        self.config = config
        self.transcription_config = config['transcription']
        self.whisper_model = None
        
    def initialize(self):
        """Инициализация модели FasterWhisper"""
        try:
            model_size = self.transcription_config.get('whisper_model', 'base')
            device = self.transcription_config.get('device', 'auto')
            compute_type = self.transcription_config.get('compute_type', 'auto')
            
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
            import torch
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
            language = self.transcription_config.get('language', 'ru')
            beam_size = self.transcription_config.get('beam_size', 5)
            
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


class TextToSpeech:
    """Синтез речи на основе Silero TTS"""
    
    def __init__(self, config):
        self.config = config
        self.parrot_config = config['parrot']
        self.model = None
        self.sample_rate = self.parrot_config['tts_sample_rate']
        self.speaker = self.parrot_config['tts_speaker']
        self.use_accentizer = self.parrot_config.get('use_accentizer', False)
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


class PauseDetector:
    """Детектор пауз в речи на основе анализа энергии сигнала"""
    
    def __init__(self, config, debug=False):
        self.config = config
        self.voice_config = config['voice_detection']
        self.debug = debug
        
        # Параметры детекции
        self.pause_threshold = self.voice_config.get('pause_threshold', 3.0)  # секунды
        self.voice_energy_threshold = self.voice_config.get('voice_energy_threshold', 0.01)
        self.min_recording_duration = self.voice_config.get('min_recording_duration', 0.5)  # секунды
        self.pause_detection_enabled = self.voice_config.get('pause_detection_enabled', True)
        
        # Состояние
        self.sample_rate = config['wake_word']['sample_rate']  # используем sample_rate от wake_word
        self.chunk_size = config['wake_word']['chunk_size']
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
            energy = self._calculate_energy(audio_chunk)
            self.calibration_samples.append(energy)
            
            if len(self.calibration_samples) == 10:
                self.noise_level = np.mean(self.calibration_samples) * 2.0  # немного выше среднего фона
                if self.debug:
                    print(f"🔊 Калибровка шума: {self.noise_level:.6f}")
    
    def _calculate_energy(self, audio_chunk):
        """Вычисляет RMS энергию аудио чанка"""
        return np.sqrt(np.mean(audio_chunk**2))
    
    def is_voice_detected(self, audio_chunk):
        """Определяет, есть ли голос в аудио чанке"""
        if not self.pause_detection_enabled:
            return True  # всегда считаем, что голос есть
            
        energy = self._calculate_energy(audio_chunk)
        
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


class SpeechParrot:
    """Основной класс попугая, объединяющий все компоненты"""
    
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
        self.state = ParrotState.LISTENING
        self.should_stop = threading.Event()
        
        # Аудио настройки
        self.sample_rate = self.config['wake_word']['sample_rate']
        self.chunk_size = self.config['wake_word']['chunk_size']
        
        # Буферы для записи
        self.recording_buffer = []
        self.recording_lock = threading.Lock()
        self.max_recording_duration = self.config['parrot']['max_recording_duration']
        self.recording_start_time = None
        self.recording_timer = None
        self.stop_reason = None  # для отслеживания причины остановки записи
        
    def initialize(self):
        """Инициализация всех компонентов"""
        print("🚀 Инициализация компонентов попугая...")
        
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
            if self.state == ParrotState.LISTENING:
                # Ищем ключевое слово
                wake_detected, result = self.wake_detector.detect_wake_word(audio_chunk)
                
                if wake_detected:
                    text, detection_time, pre_trigger_audio = result
                    print(f"🎉 Обнаружено ключевое слово: {text} (время: {detection_time:.3f}s)")
                    self._start_recording(pre_trigger_audio)
                elif self.debug and result:  # если есть любой текст
                    print(f"🔍 DEBUG: Vosk вернул текст: '{result}', wake_detected={wake_detected}")
                    
            elif self.state == ParrotState.RECORDING:
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
        self.state = ParrotState.RECORDING
        
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
        self.recording_timer = threading.Timer(self.max_recording_duration, lambda: self._stop_recording_and_process("timeout"))
        self.recording_timer.start()
    
    def _stop_recording_and_process(self, reason=None):
        """Останавливает запись и запускает обработку"""
        if self.state != ParrotState.RECORDING:
            return
        
        # Если причина не передана, используем сохраненную
        if reason is None:
            reason = self.stop_reason or "unknown"
            
        self.state = ParrotState.TRANSCRIBING
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
            self.state = ParrotState.SYNTHESIZING
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
                
            self.state = ParrotState.LISTENING
            self.recording_buffer = []
            self.recording_start_time = None
        print("👂 Жду ключевое слово...")
    
    def run(self):
        """Основной цикл работы попугая"""
        print("🦜 Запуск речевого попугая")
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
            print("\n🛑 Остановка попугая...")
            self.should_stop.set()
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            self.should_stop.set()
        
        print("✅ Попугай остановлен")


def main():
    """Основная функция"""
    import sys
    
    # Проверяем аргументы командной строки
    debug = "--debug" in sys.argv or "-d" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Speech Parrot - Речевой попугай")
        print()
        print("Использование:")
        print("  python parrot.py [--debug] [--help]")
        print()
        print("Опции:")
        print("  --debug, -d    Включить отладочный вывод")
        print("  --help, -h     Показать эту справку")
        return 0
    
    try:
        parrot = SpeechParrot(debug=debug)
        
        if debug:
            print("🔧 Режим отладки включен")
        
        if not parrot.initialize():
            print("❌ Не удалось инициализировать попугая")
            return 1
            
        parrot.run()
        return 0
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())