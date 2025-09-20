#!/usr/bin/env python3
"""
Test runner for virtual podcast components

Запускает тесты для ключевых компонентов виртуального подкаста.
Использование: python tests/run_tests.py
"""

import sys
import os
import importlib.util
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test_module(module_path: Path) -> tuple[int, int]:
    """
    Запускает тесты из модуля

    Returns:
        Tuple (passed_tests, total_tests)
    """
    spec = importlib.util.spec_from_file_location("test_module", module_path)
    test_module = importlib.util.module_from_spec(spec)

    passed = 0
    total = 0

    try:
        spec.loader.exec_module(test_module)

        # Найдем все тестовые классы и методы
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if name.startswith('Test') and hasattr(obj, '__dict__'):
                test_class = obj()

                for method_name in dir(test_class):
                    if method_name.startswith('test_'):
                        total += 1
                        try:
                            method = getattr(test_class, method_name)
                            method()
                            print(f"  ✅ {method_name}")
                            passed += 1
                        except Exception as e:
                            print(f"  ❌ {method_name}: {e}")

    except Exception as e:
        print(f"  ❌ Ошибка загрузки модуля: {e}")

    return passed, total


def main():
    """Основная функция запуска тестов"""
    print("🧪 Запуск тестов виртуального подкаста")
    print("=" * 50)

    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))

    if not test_files:
        print("❌ Тестовые файлы не найдены")
        return 1

    total_passed = 0
    total_tests = 0

    for test_file in test_files:
        print(f"\n📝 Запуск {test_file.name}:")
        passed, tests = run_test_module(test_file)
        total_passed += passed
        total_tests += tests

        if tests > 0:
            percentage = (passed / tests) * 100
            status = "✅" if passed == tests else "⚠️"
            print(f"  {status} {passed}/{tests} тестов пройдено ({percentage:.1f}%)")
        else:
            print("  ⚠️ Тесты не найдены")

    print("\n" + "=" * 50)
    print(f"📊 Итого: {total_passed}/{total_tests} тестов пройдено")

    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        if success_rate == 100:
            print("🎉 Все тесты пройдены успешно!")
            return 0
        elif success_rate >= 80:
            print(f"✅ Большинство тестов пройдено ({success_rate:.1f}%)")
            return 0
        else:
            print(f"⚠️ Много проваленных тестов ({success_rate:.1f}%)")
            return 1
    else:
        print("❌ Тесты не найдены или не выполнены")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)