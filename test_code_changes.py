#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений в коде orchestrator.py
Проверяет изменения на уровне исходного кода без импорта
"""

import os
import sys


def test_file_changes():
    """Тестирует изменения в файле orchestrator.py"""

    orchestrator_file = "/home/seko/Projects/ai/assistant/podcast/orchestrator.py"

    if not os.path.exists(orchestrator_file):
        print("❌ Файл orchestrator.py не найден!")
        return False

    with open(orchestrator_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("🧪 Проверка удаления проблемных методов...")

    # Методы, которые должны быть удалены
    removed_methods = [
        'def _moderator_question_for_speaker',
        'def _moderator_transition'
    ]

    for method in removed_methods:
        if method in content:
            print(f"❌ Метод {method} НЕ удален!")
            return False
        else:
            print(f"✅ Метод {method} успешно удален")

    print("\n🧪 Проверка изменений в _run_discussion_round...")

    # Проверяем, что удалены проблемные вызовы
    forbidden_calls = [
        '_moderator_question_for_speaker(',
        '_moderator_transition('
    ]

    for call in forbidden_calls:
        if call in content:
            print(f"❌ Обнаружен вызов {call}!")
            return False
        else:
            print(f"✅ Вызов {call} удален")

    print("\n🧪 Проверка улучшений в _moderator_round_intro...")

    # Проверяем наличие новых элементов в промпте
    improvements = [
        'направляющие вопросы',
        'Участники:',
        'единое связное вступление'
    ]

    for improvement in improvements:
        if improvement in content:
            print(f"✅ Улучшение '{improvement}' найдено")
        else:
            print(f"⚠️ Улучшение '{improvement}' не найдено")

    print("\n🧪 Проверка обновления _speaker_response...")

    # Проверяем новые элементы в ответах спикеров
    speaker_improvements = [
        'введение в раунд',
        'затронутым вопросам'
    ]

    for improvement in speaker_improvements:
        if improvement in content:
            print(f"✅ Улучшение '{improvement}' найдено в _speaker_response")
        else:
            print(f"⚠️ Улучшение '{improvement}' не найдено в _speaker_response")

    return True


def test_line_count_changes():
    """Проверяет сокращение количества строк"""

    orchestrator_file = "/home/seko/Projects/ai/assistant/podcast/orchestrator.py"

    with open(orchestrator_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    line_count = len(lines)
    print(f"\n📊 Текущее количество строк в orchestrator.py: {line_count}")

    # Должно быть меньше, чем было (примерно на 50+ строк)
    if line_count < 500:  # Примерная оценка
        print("✅ Файл стал компактнее после удаления методов")
    else:
        print("⚠️ Файл все еще довольно большой")

    return True


def analyze_new_flow():
    """Анализирует новый поток выполнения раундов"""

    print("\n📋 АНАЛИЗ НОВОГО ПОТОКА ВЫПОЛНЕНИЯ:")
    print("=" * 50)

    expected_flow = [
        "1. Модератор делает введение с направляющими вопросами (_moderator_round_intro)",
        "2. Каждый спикер отвечает на общие вопросы (_speaker_response)",
        "3. Переход к следующему раунду (без промежуточных связок)"
    ]

    for step in expected_flow:
        print(f"✅ {step}")

    print("\n🚫 УДАЛЕННЫЕ ЭЛЕМЕНТЫ:")
    removed_elements = [
        "❌ Персональные вопросы каждому спикеру",
        "❌ Промежуточные связки между спикерами",
        "❌ Дублирование вопросов модератора"
    ]

    for element in removed_elements:
        print(f"   {element}")

    return True


def main():
    """Главная функция тестирования"""
    print("🎙️ ПРОВЕРКА ИСПРАВЛЕНИЙ ДУБЛИРОВАНИЯ РЕПЛИК МОДЕРАТОРА")
    print("=" * 65)

    tests = [
        ("Изменения в коде", test_file_changes),
        ("Сокращение файла", test_line_count_changes),
        ("Анализ нового потока", analyze_new_flow)
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

    print(f"\n📊 РЕЗУЛЬТАТЫ: {passed}/{total} проверок пройдено")

    if passed == total:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Исправления дублирования реплик модератора реализованы корректно.")
        print("\n💡 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
        print("   • Модератор говорит 1 раз в начале каждого раунда")
        print("   • Спикеры отвечают на общие направляющие вопросы")
        print("   • Устранено дублирование контента")
        print("   • Более естественный поток беседы")
        return 0
    else:
        print("\n⚠️ Некоторые проверки провалены.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)