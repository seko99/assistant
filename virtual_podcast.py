#!/usr/bin/env python3
"""
Virtual Podcast Generator

Генерирует виртуальный подкаст с участием ИИ-персонажей на заданную тему.
Использует существующие компоненты: LLM Engine и Text-to-Speech.

Использование:
    python virtual_podcast.py --topic "Искусственный интеллект"
    python virtual_podcast.py --topic "Криптовалюты" --rounds 2 --no-audio
"""

import sys
import argparse
import os
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_engine import LLMEngine
from core.text_to_speech import TextToSpeech
from podcast.orchestrator import PodcastOrchestrator
from utils.config import load_config


def create_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Генератор виртуального подкаста",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовый подкаст на 3 раунда с аудио
  python virtual_podcast.py --topic "Искусственный интеллект"

  # Короткий подкаст без аудио
  python virtual_podcast.py --topic "Будущее работы" --rounds 2 --no-audio

  # Подкаст с кастомной директорией вывода
  python virtual_podcast.py --topic "Климатические изменения" --output-dir ./my_podcasts

  # Интерактивный режим
  python virtual_podcast.py

Участники подкаста:
  - Максим (модератор) - опытный журналист
  - Анна (техэксперт) - IT-специалист
  - Дмитрий (бизнес-аналитик) - стратег и экономист
  - Елена (социолог) - эксперт по социальным процессам
        """
    )

    parser.add_argument(
        '--topic', '-t',
        type=str,
        help='Тема подкаста для обсуждения'
    )

    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=None,
        help='Количество раундов обсуждения (по умолчанию: 3)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='Директория для сохранения результатов (по умолчанию: output/podcast_YYYYMMDD_HHMMSS)'
    )

    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Генерировать только текст без аудио синтеза'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.json',
        help='Путь к файлу конфигурации (по умолчанию: config.json)'
    )

    parser.add_argument(
        '--list-voices',
        action='store_true',
        help='Показать список доступных голосов и выйти'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Тестовый запуск - показать настройки и выйти'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробный вывод'
    )

    return parser


def get_topic_interactively() -> str:
    """Получает тему подкаста в интерактивном режиме"""
    print("🎙️ Генератор виртуального подкаста")
    print()
    print("Участники:")
    print("  • Максим (модератор) - опытный журналист")
    print("  • Анна (техэксперт) - IT-специалист")
    print("  • Дмитрий (бизнес-аналитик) - стратег и экономист")
    print("  • Елена (социолог) - эксперт по социальным процессам")
    print()

    while True:
        topic = input("Введите тему для обсуждения: ").strip()
        if topic:
            return topic
        print("⚠️ Тема не может быть пустой. Попробуйте еще раз.")


def show_voice_list():
    """Показывает список доступных голосов"""
    print("🗣️ Доступные голоса Silero TTS:")
    print()
    voices = [
        ("aidar", "Мужской голос (по умолчанию для модератора)"),
        ("kseniya", "Женский голос (по умолчанию для техэксперта)"),
        ("eugene", "Мужской голос (по умолчанию для бизнес-аналитика)"),
        ("baya", "Женский голос (по умолчанию для социолога)"),
        ("irina", "Женский голос"),
        ("madirus", "Мужской голос"),
        ("ruslan", "Мужской голос")
    ]

    for voice, description in voices:
        print(f"  • {voice:<10} - {description}")

    print()
    print("Голоса настраиваются в config.json в секции podcast.participants")


def validate_environment() -> tuple[bool, list[str]]:
    """Проверяет окружение и зависимости"""
    issues = []

    # Проверяем доступность компонентов
    try:
        import torch
        if not torch.cuda.is_available():
            issues.append("CUDA недоступна - TTS будет работать на CPU")
    except ImportError:
        issues.append("PyTorch не установлен")

    try:
        import sounddevice as sd
    except ImportError:
        issues.append("sounddevice не установлен")

    try:
        import torchaudio
    except ImportError:
        issues.append("torchaudio не установлен")

    # Проверяем директории
    if not os.path.exists('output'):
        try:
            os.makedirs('output')
        except Exception as e:
            issues.append(f"Не удается создать директорию output: {e}")

    return len(issues) == 0 or all("CUDA" in issue for issue in issues), issues


def main():
    """Основная функция"""
    parser = create_parser()
    args = parser.parse_args()

    # Показать список голосов и выйти
    if args.list_voices:
        show_voice_list()
        return 0

    # Проверяем окружение
    env_ok, env_issues = validate_environment()
    if args.verbose and env_issues:
        for issue in env_issues:
            print(f"⚠️ {issue}")

    if not env_ok:
        print("❌ Критические проблемы с окружением:")
        for issue in env_issues:
            if "CUDA" not in issue:  # CUDA предупреждение не критично
                print(f"  • {issue}")
        return 1

    # Загружаем конфигурацию
    print(f"📝 Загрузка конфигурации: {args.config}")
    config = load_config(args.config)
    if not config:
        print(f"❌ Не удалось загрузить конфигурацию из {args.config}")
        return 1

    # Получаем тему
    topic = args.topic
    if not topic:
        try:
            topic = get_topic_interactively()
        except KeyboardInterrupt:
            print("\n👋 Отменено пользователем")
            return 0

    # Настройки
    rounds = args.rounds
    output_dir = args.output_dir
    no_audio = args.no_audio

    if args.verbose:
        print(f"🎯 Тема: {topic}")
        print(f"🔄 Раундов: {rounds or config.get('podcast', {}).get('default_rounds', 3)}")
        print(f"🔊 Аудио: {'отключено' if no_audio else 'включено'}")
        print(f"📁 Вывод: {output_dir or 'автоматически'}")

    # Тестовый запуск
    if args.dry_run:
        print("✅ Конфигурация корректна")
        print("🧪 Тестовый запуск завершен")
        return 0

    try:
        # Инициализируем компоненты
        print("🚀 Инициализация компонентов...")

        llm_engine = LLMEngine(config)
        if not llm_engine.initialize():
            print("❌ Не удалось инициализировать LLM Engine")
            return 1

        tts_engine = TextToSpeech(config)
        if not tts_engine.initialize():
            print("❌ Не удалось инициализировать Text-to-Speech")
            return 1

        # Создаем оркестратор
        orchestrator = PodcastOrchestrator(config, llm_engine, tts_engine)

        # Запускаем подкаст
        print(f"🎙️ Создание подкаста на тему: '{topic}'")
        session = orchestrator.start_podcast(
            topic=topic,
            rounds=rounds,
            output_dir=output_dir,
            no_audio=no_audio
        )

        print(f"▶️ Запуск подкаста (ID: {session.session_id})")
        success = orchestrator.run_podcast()

        if success:
            # Сохраняем результаты
            print("💾 Сохранение результатов...")
            results = orchestrator.save_results()

            # Показываем результаты
            print("\n🎉 Подкаст успешно создан!")
            print(f"📁 Директория: {session.output_directory}")

            if results:
                print("📄 Файлы:")
                for file_type, file_path in results.items():
                    print(f"  • {file_type}: {file_path}")

            if session.transcript:
                print(f"📝 Реплик: {len(session.transcript)}")
                print(f"⏱️ Раундов: {session.current_round}")

            return 0
        else:
            print("❌ Ошибка при создании подкаста")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Подкаст остановлен пользователем")
        if 'session' in locals() and session:
            print(f"💾 Частичные результаты сохранены в: {session.output_directory}")
        return 0

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
        sys.exit(0)