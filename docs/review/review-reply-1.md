# План реализации замечаний Code Review

## P0 - Критические исправления

### 1. Унификация парсеров thinking-блоков
- **utils/text_filters.py**: Поддержать оба варианта тегов (`<think>` и `<thinking>`)
- Обновить паттерны в функциях: `filter_thinking_blocks`, `has_thinking_blocks`, `extract_thinking_content`
- Синхронизировать с существующими тестами в `tests/test_text_filters.py`

### 2. Исправление config_keys.py
- **utils/config_keys.py**: Устранить переопределение `ConfigKeys.LLM`
- Разделить на `ConfigSections.LLM = 'llm'` и `ConfigKeysLLM = LLMKeys`

### 3. Потокобезопасность в main.py
- **main.py**: Добавить единый лок для `_stop_recording_and_process`
- Сделать функцию идемпотентной с атомарным флагом "stopping"

## P1 - Важные улучшения

### 4. Аудио утилиты
- **utils/audio_utils.py**: Добавить `np.clip(audio_data, -1.0, 1.0)` в `convert_float32_to_int16`

### 5. Временные файлы ASR
- **core/speech_recognition.py**: Перейти на `tempfile.NamedTemporaryFile`
- Учесть флаги `save_audio_files`/`auto_delete_audio` из конфига

### 6. TTS офлайн поддержка
- **core/text_to_speech.py**: Graceful fallback при отсутствии сети
- Поддержка локального кэша модели
- Выбор аудиоустройства через конфиг

### 7. Логирование
- Заменить `print` на `logging` с уровнями
- Добавить конфигурируемый формат и уровень логов

### 8. Очистка тестовых артефактов
- Удалить/архивировать `test_podcast_fix.py`, `test_code_changes.py` из корня
- Либо синхронизировать с реальным кодом

## P2 - Средний приоритет

### 9. Документация
- Синхронизировать README с кодом (состояния PROCESSING/THINKING)
- Вычистить/задействовать неиспользуемые конфиг-ключи

### 10. Калибровка пауз
- **core/pause_detection.py**: Улучшить адаптацию к шуму
- Перенести калибровку в состояние RECORDING

## Быстрые победы (low effort, high value)
1. Клиппинг аудио (1 строка)
2. Поддержка обоих тегов thinking (обновить паттерны)
3. tempfile для ASR (убрать мусор в репо)
4. Исправить ConfigKeys.LLM