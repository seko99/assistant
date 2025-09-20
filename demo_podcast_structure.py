#!/usr/bin/env python3
"""
Демонстрация структуры виртуального подкаста без внешних зависимостей
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_project_structure():
    """Показывает структуру проекта подкастов"""
    print("🎙️ Структура виртуального подкаста:")
    print("=" * 50)

    base_path = Path(__file__).parent

    # Основные компоненты
    components = [
        ("virtual_podcast.py", "Главный CLI скрипт"),
        ("config.json", "Конфигурация (обновлена с секцией podcast)"),
        ("podcast/__init__.py", "Инициализация модуля подкастов"),
        ("podcast/session.py", "Управление сессией и транскриптом"),
        ("podcast/persona.py", "Профили участников и голоса"),
        ("podcast/context_enricher.py", "Обогащение контекста темы"),
        ("podcast/context_splitter.py", "Распределение контекста"),
        ("podcast/orchestrator.py", "Основной оркестратор подкаста"),
        ("tests/test_podcast_session.py", "Тесты сессии"),
        ("tests/test_context_enricher.py", "Тесты контекста"),
        ("tests/test_persona.py", "Тесты участников"),
        ("tests/run_tests.py", "Запуск всех тестов"),
        ("VIRTUAL_PODCAST_README.md", "Документация")
    ]

    for file_path, description in components:
        full_path = base_path / file_path
        status = "✅" if full_path.exists() else "❌"
        print(f"{status} {file_path:<35} - {description}")

    print("\n📊 Статистика:")
    podcast_files = list((base_path / "podcast").glob("*.py"))
    test_files = list((base_path / "tests").glob("test_*.py"))

    print(f"  • Модулей подкаста: {len(podcast_files)}")
    print(f"  • Тестовых файлов: {len(test_files)}")
    print(f"  • Строк кода в podcast/: {count_lines_in_dir(base_path / 'podcast')}")


def count_lines_in_dir(directory):
    """Подсчитывает строки кода в директории"""
    total_lines = 0
    if directory.exists():
        for py_file in directory.glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                pass
    return total_lines


def show_participants():
    """Показывает участников подкаста"""
    print("\n👥 Участники подкаста:")
    print("=" * 50)

    participants = [
        {
            "name": "Максим",
            "role": "Модератор",
            "voice": "aidar",
            "description": "Опытный журналист, управляет ходом беседы",
            "expertise": ["журналистика", "медиа", "интервью"]
        },
        {
            "name": "Анна",
            "role": "Техэксперт",
            "voice": "kseniya",
            "description": "IT-специалист с опытом в разработке",
            "expertise": ["программирование", "ИИ", "технологии"]
        },
        {
            "name": "Дмитрий",
            "role": "Бизнес-аналитик",
            "voice": "eugene",
            "description": "Эксперт по стратегии и рыночному анализу",
            "expertise": ["бизнес", "экономика", "инвестиции"]
        },
        {
            "name": "Елена",
            "role": "Социолог",
            "voice": "baya",
            "description": "Специалист по общественным процессам",
            "expertise": ["социология", "культура", "общество"]
        }
    ]

    for p in participants:
        print(f"🎤 {p['name']} ({p['role']})")
        print(f"   Голос: {p['voice']}")
        print(f"   {p['description']}")
        print(f"   Экспертиза: {', '.join(p['expertise'])}")
        print()


def show_usage_examples():
    """Показывает примеры использования"""
    print("💡 Примеры использования:")
    print("=" * 50)

    examples = [
        ("Базовый подкаст", 'python virtual_podcast.py --topic "Искусственный интеллект"'),
        ("Короткий подкаст", 'python virtual_podcast.py --topic "Блокчейн" --rounds 2'),
        ("Только текст", 'python virtual_podcast.py --topic "Климат" --no-audio'),
        ("Кастомная папка", 'python virtual_podcast.py --topic "Образование" -o ./my_podcasts'),
        ("Интерактивный режим", 'python virtual_podcast.py'),
        ("Список голосов", 'python virtual_podcast.py --list-voices'),
        ("Тестовый запуск", 'python virtual_podcast.py --dry-run'),
    ]

    for description, command in examples:
        print(f"• {description}:")
        print(f"  {command}")
        print()


def show_features():
    """Показывает возможности системы"""
    print("🚀 Ключевые возможности:")
    print("=" * 50)

    features = [
        "✅ Автоматическая генерация подкастов по теме",
        "✅ 4 уникальных ИИ-участника с разными ролями",
        "✅ Поддержка разных голосов Silero TTS",
        "✅ Обогащение контекста через mock поиск",
        "✅ Гибкая конфигурация участников",
        "✅ Сохранение в JSON и Markdown форматах",
        "✅ CLI интерфейс с множеством опций",
        "✅ Режим только текста (--no-audio)",
        "✅ Настраиваемое количество раундов",
        "✅ Интеграция с существующими компонентами",
        "✅ Комплексная система тестирования",
        "✅ Подробная документация"
    ]

    for feature in features:
        print(f"  {feature}")


def main():
    """Главная функция демонстрации"""
    print("🎙️ ВИРТУАЛЬНЫЙ ПОДКАСТ - ДЕМОНСТРАЦИЯ СТРУКТУРЫ")
    print("=" * 60)
    print()

    show_project_structure()
    show_participants()
    show_features()
    show_usage_examples()

    print("📝 Для полной документации см. VIRTUAL_PODCAST_README.md")
    print("🧪 Для запуска тестов: python tests/run_tests.py")
    print("⚙️ Для работы требуется настроенный LLM сервер и зависимости")


if __name__ == "__main__":
    main()