"""
Configuration utilities for the Speech Assistant application.
"""

import json


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