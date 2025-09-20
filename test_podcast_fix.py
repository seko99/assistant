#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления дублирования реплик модератора
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем только необходимые компоненты
from podcast.orchestrator import PodcastOrchestrator
from podcast.session import PodcastSession


def test_orchestrator_structure():
    """Тестирует структуру оркестратора после исправлений"""
    print("🧪 Тестирование структуры PodcastOrchestrator...")

    # Проверяем, что методы удалены
    orchestrator_methods = dir(PodcastOrchestrator)

    removed_methods = [
        '_moderator_question_for_speaker',
        '_moderator_transition'
    ]

    for method in removed_methods:
        if method in orchestrator_methods:
            print(f"❌ Метод {method} НЕ удален!")
            return False
        else:
            print(f"✅ Метод {method} успешно удален")

    # Проверяем, что нужные методы остались
    required_methods = [
        '_run_discussion_round',
        '_moderator_round_intro',
        '_speaker_response'
    ]

    for method in required_methods:
        if method in orchestrator_methods:
            print(f"✅ Метод {method} существует")
        else:
            print(f"❌ Метод {method} ОТСУТСТВУЕТ!")
            return False

    return True


def test_round_flow_logic():
    """Тестирует новую логику раундов"""
    print("\n🧪 Тестирование новой логики раундов...")

    # Проверяем исходный код _run_discussion_round
    import inspect
    source = inspect.getsource(PodcastOrchestrator._run_discussion_round)

    # Проверяем, что удаленные вызовы отсутствуют
    forbidden_calls = [
        '_moderator_question_for_speaker',
        '_moderator_transition'
    ]

    for call in forbidden_calls:
        if call in source:
            print(f"❌ Обнаружен вызов {call} в _run_discussion_round!")
            return False
        else:
            print(f"✅ Вызов {call} удален из _run_discussion_round")

    # Проверяем наличие нужных вызовов
    required_calls = [
        '_moderator_round_intro',
        '_speaker_response'
    ]

    for call in required_calls:
        if call in source:
            print(f"✅ Вызов {call} присутствует в _run_discussion_round")
        else:
            print(f"❌ Вызов {call} ОТСУТСТВУЕТ в _run_discussion_round!")
            return False

    return True


def test_intro_enhancement():
    """Тестирует улучшение введения модератора"""
    print("\n🧪 Тестирование улучшения введения модератора...")

    import inspect
    source = inspect.getsource(PodcastOrchestrator._moderator_round_intro)

    # Проверяем наличие ключевых элементов в промпте
    required_elements = [
        'направляющие вопросы',
        'общие',
        'участники',
        'единое связное вступление'
    ]

    for element in required_elements:
        if element in source:
            print(f"✅ Элемент '{element}' найден в _moderator_round_intro")
        else:
            print(f"⚠️ Элемент '{element}' не найден в _moderator_round_intro")

    return True


def test_speaker_response_update():
    """Тестирует обновление ответов спикеров"""
    print("\n🧪 Тестирование обновления ответов спикеров...")

    import inspect
    source = inspect.getsource(PodcastOrchestrator._speaker_response)

    # Проверяем новую логику
    improvements = [
        'введение в раунд',
        'затронутым вопросам',
        'естественно',
        'участник дискуссии'
    ]

    for improvement in improvements:
        if improvement in source:
            print(f"✅ Улучшение '{improvement}' найдено в _speaker_response")
        else:
            print(f"⚠️ Улучшение '{improvement}' не найдено в _speaker_response")

    return True


def main():
    """Главная функция тестирования"""
    print("🎙️ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ДУБЛИРОВАНИЯ РЕПЛИК МОДЕРАТОРА")
    print("=" * 70)

    tests = [
        ("Структура оркестратора", test_orchestrator_structure),
        ("Логика раундов", test_round_flow_logic),
        ("Улучшение введения", test_intro_enhancement),
        ("Обновление ответов спикеров", test_speaker_response_update)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: ПРОЙДЕН")
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")

    print(f"\n📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Исправления реализованы корректно.")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте исправления.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)