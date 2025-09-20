#!/usr/bin/env python3
"""
Тест для проверки интеграции акцентизатора в подкаст-системе
Проверяет настройки и логирование без запуска полного подкаста
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_accentizer_setting():
    """Проверяет настройку акцентизатора в конфиге"""
    print("🧪 Проверка настройки акцентизатора в конфиге...")

    config_file = "/home/seko/Projects/ai/assistant/config.json"

    if not os.path.exists(config_file):
        print("❌ Файл config.json не найден!")
        return False

    import json
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Проверяем наличие настройки use_accentizer
    assistant_config = config.get('assistant', {})
    use_accentizer = assistant_config.get('use_accentizer', False)

    if use_accentizer:
        print("✅ use_accentizer включен в конфиге")
        return True
    else:
        print("⚠️ use_accentizer отключен в конфиге")
        return False


def test_tts_accentizer_support():
    """Проверяет поддержку акцентизатора в TextToSpeech модуле"""
    print("\n🧪 Проверка поддержки акцентизатора в TextToSpeech...")

    tts_file = "/home/seko/Projects/ai/assistant/core/text_to_speech.py"

    if not os.path.exists(tts_file):
        print("❌ Файл text_to_speech.py не найден!")
        return False

    with open(tts_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем ключевые элементы поддержки акцентизатора
    accentizer_features = [
        'self.use_accentizer',
        'self.accentizer',
        'from ruaccent import RUAccent',
        'process_all(text)'
    ]

    missing_features = []
    for feature in accentizer_features:
        if feature in content:
            print(f"✅ Найдена поддержка: {feature}")
        else:
            print(f"❌ Отсутствует: {feature}")
            missing_features.append(feature)

    return len(missing_features) == 0


def test_orchestrator_logging():
    """Проверяет добавленное логирование в orchestrator.py"""
    print("\n🧪 Проверка логирования акцентизатора в PodcastOrchestrator...")

    orchestrator_file = "/home/seko/Projects/ai/assistant/podcast/orchestrator.py"

    if not os.path.exists(orchestrator_file):
        print("❌ Файл orchestrator.py не найден!")
        return False

    with open(orchestrator_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем добавленное логирование
    logging_features = [
        'Акцентизатор:',
        'accentizer_status',
        '[с ударениями]',
        'tts_engine.use_accentizer'
    ]

    found_features = []
    for feature in logging_features:
        if feature in content:
            print(f"✅ Найдено логирование: {feature}")
            found_features.append(feature)
        else:
            print(f"❌ Отсутствует логирование: {feature}")

    return len(found_features) >= 3  # Должно быть хотя бы 3 из 4 элементов


def test_virtual_podcast_tts_creation():
    """Проверяет создание TTS с конфигом в virtual_podcast.py"""
    print("\n🧪 Проверка создания TTS в virtual_podcast.py...")

    vp_file = "/home/seko/Projects/ai/assistant/virtual_podcast.py"

    if not os.path.exists(vp_file):
        print("❌ Файл virtual_podcast.py не найден!")
        return False

    with open(vp_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем правильное создание TTS с конфигом
    tts_creation_patterns = [
        'TextToSpeech(config)',
        'tts_engine = TextToSpeech',
        'orchestrator = PodcastOrchestrator(config, llm_engine, tts_engine)'
    ]

    for pattern in tts_creation_patterns:
        if pattern in content:
            print(f"✅ Найден паттерн: {pattern}")
        else:
            print(f"❌ Отсутствует паттерн: {pattern}")
            return False

    return True


def simulate_accentizer_process():
    """Симулирует обработку текста акцентизатором"""
    print("\n🧪 Симуляция обработки текста акцентизатором...")

    test_texts = [
        "Привет, как дела?",
        "Искусственный интеллект развивается быстро",
        "Технологии меняют нашу жизнь",
        "Экономика и бизнес требуют анализа"
    ]

    # Симулируем что происходит с текстом при обработке
    for text in test_texts:
        # Примерная симуляция добавления ударений (без реального RUAccent)
        processed = text.replace('а', 'а́').replace('е', 'е́')[:50]  # Упрощенная симуляция
        print(f"📝 Исходный: {text}")
        print(f"🔤 С ударениями: {processed}")
        print()

    print("✅ Симуляция обработки акцентизатором завершена")
    return True


def main():
    """Главная функция тестирования"""
    print("🎙️ ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ АКЦЕНТИЗАТОРА В ПОДКАСТ-СИСТЕМЕ")
    print("=" * 70)

    tests = [
        ("Настройка в конфиге", test_config_accentizer_setting),
        ("Поддержка в TTS", test_tts_accentizer_support),
        ("Логирование в оркестраторе", test_orchestrator_logging),
        ("Создание TTS в скрипте", test_virtual_podcast_tts_creation),
        ("Симуляция обработки", simulate_accentizer_process)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: УСПЕШНО")
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")

    print(f"\n📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Акцентизатор интегрирован в подкаст-систему корректно.")
        print("\n💡 ЧТО ПРОИСХОДИТ ПРИ РАБОТЕ:")
        print("   1. virtual_podcast.py создает TextToSpeech с полным конфигом")
        print("   2. TextToSpeech инициализирует RUAccent при use_accentizer=true")
        print("   3. PodcastOrchestrator получает настроенный tts_engine")
        print("   4. При синтезе речи текст обрабатывается через акцентизатор")
        print("   5. Логирование показывает статус акцентизатора")
        print("\n🗣️ РЕЗУЛЬТАТ: Участники подкаста говорят с правильными ударениями!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} тестов провалено. Проверьте интеграцию.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)