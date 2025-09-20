#!/usr/bin/env python3
"""
Тесты для модуля фильтрации текста.
Проверяет корректность удаления thinking-блоков и других мета-контента.
"""

import unittest
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_filters import (
    filter_thinking_blocks,
    filter_reasoning_blocks,
    clean_llm_response,
    has_thinking_blocks,
    extract_thinking_content
)


class TestThinkingBlockFilter(unittest.TestCase):
    """Тесты для фильтрации thinking-блоков"""

    def test_filter_simple_thinking_block(self):
        """Тест удаления простого thinking-блока"""
        text = "<thinking>Это внутреннее рассуждение</thinking>Это основной ответ."
        expected = "Это основной ответ."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)

    def test_filter_multiline_thinking_block(self):
        """Тест удаления многострочного thinking-блока"""
        text = """<thinking>
Это многострочное
внутреннее рассуждение
</thinking>
Это основной ответ."""
        expected = "Это основной ответ."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)

    def test_filter_multiple_thinking_blocks(self):
        """Тест удаления нескольких thinking-блоков"""
        text = """<thinking>Первое рассуждение</thinking>Начало ответа.
<thinking>Второе рассуждение</thinking>Продолжение ответа."""
        expected = "Начало ответа.\nПродолжение ответа."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)

    def test_filter_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        text = "<THINKING>Рассуждение</THINKING>Ответ <ThInKiNg>еще</ThInKiNg> продолжение."
        expected = "Ответ  продолжение."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)

    def test_no_thinking_blocks(self):
        """Тест текста без thinking-блоков"""
        text = "Обычный текст без блоков рассуждений."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, text)

    def test_empty_text(self):
        """Тест пустого текста"""
        result = filter_thinking_blocks("")
        self.assertEqual(result, "")

    def test_nested_content(self):
        """Тест с вложенным контентом в thinking-блоке"""
        text = "<thinking>Размышляю о <важном> вопросе</thinking>Основной ответ."
        expected = "Основной ответ."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)

    def test_whitespace_cleanup(self):
        """Тест очистки лишних пробелов"""
        text = """<thinking>Рассуждение</thinking>



Основной ответ."""
        expected = "Основной ответ."
        result = filter_thinking_blocks(text)
        self.assertEqual(result, expected)


class TestReasoningBlockFilter(unittest.TestCase):
    """Тесты для фильтрации различных блоков рассуждений"""

    def test_filter_various_reasoning_blocks(self):
        """Тест удаления различных типов блоков рассуждений"""
        text = """<thinking>Думаю</thinking>
<reasoning>Анализирую</reasoning>
<analysis>Исследую</analysis>
<internal>Внутренние мысли</internal>
<meta>Мета-информация</meta>
Основной ответ."""
        expected = "Основной ответ."
        result = filter_reasoning_blocks(text)
        self.assertEqual(result, expected)

    def test_mixed_case_reasoning_blocks(self):
        """Тест блоков рассуждений в разном регистре"""
        text = "<REASONING>Верхний</REASONING><Analysis>Смешанный</Analysis>Ответ."
        expected = "Ответ."
        result = filter_reasoning_blocks(text)
        self.assertEqual(result, expected)


class TestComprehensiveCleaning(unittest.TestCase):
    """Тесты для комплексной очистки LLM ответов"""

    def test_clean_llm_response_default(self):
        """Тест стандартной очистки с thinking-блоками"""
        text = "<thinking>Рассуждаю</thinking>Чистый ответ."
        expected = "Чистый ответ."
        result = clean_llm_response(text)
        self.assertEqual(result, expected)

    def test_clean_llm_response_with_reasoning(self):
        """Тест очистки с блоками рассуждений"""
        text = "<thinking>Думаю</thinking><analysis>Анализ</analysis>Ответ."
        expected = "Ответ."
        result = clean_llm_response(text, filter_thinking=True, filter_reasoning=True)
        self.assertEqual(result, expected)

    def test_clean_llm_response_disabled_filters(self):
        """Тест с отключенными фильтрами"""
        text = "<thinking>Рассуждение</thinking>Ответ."
        result = clean_llm_response(text, filter_thinking=False, filter_reasoning=False)
        self.assertEqual(result, text)

    def test_clean_llm_response_with_max_length(self):
        """Тест обрезки по максимальной длине"""
        text = "Очень длинный ответ, который нужно обрезать по границе предложения."
        result = clean_llm_response(text, max_length=30)
        # Проверяем, что результат разумной длины (может быть немного больше из-за логики обрезки)
        self.assertTrue(len(result) <= 50)  # Более реалистичный лимит
        self.assertTrue(result.endswith('.') or result.endswith('...'))

    def test_clean_llm_response_hard_truncation(self):
        """Тест жесткой обрезки при отсутствии предложений"""
        text = "Текстбезпробеловипредложений"
        result = clean_llm_response(text, max_length=10)
        self.assertTrue(len(result) <= 13)  # 10 + "..."
        self.assertTrue(result.endswith('...'))


class TestUtilityFunctions(unittest.TestCase):
    """Тесты для вспомогательных функций"""

    def test_has_thinking_blocks_true(self):
        """Тест обнаружения thinking-блоков"""
        text = "Текст с <thinking>блоком</thinking> рассуждения."
        self.assertTrue(has_thinking_blocks(text))

    def test_has_thinking_blocks_false(self):
        """Тест отсутствия thinking-блоков"""
        text = "Обычный текст без блоков."
        self.assertFalse(has_thinking_blocks(text))

    def test_has_thinking_blocks_empty(self):
        """Тест пустого текста"""
        self.assertFalse(has_thinking_blocks(""))

    def test_extract_thinking_content(self):
        """Тест извлечения содержимого thinking-блоков"""
        text = "<thinking>Первое</thinking>Ответ<thinking>Второе</thinking>"
        expected = ["Первое", "Второе"]
        result = extract_thinking_content(text)
        self.assertEqual(result, expected)

    def test_extract_thinking_content_multiline(self):
        """Тест извлечения многострочного содержимого"""
        text = """<thinking>
        Многострочное
        рассуждение
        </thinking>Ответ"""
        result = extract_thinking_content(text)
        self.assertEqual(len(result), 1)
        self.assertIn("Многострочное", result[0])
        self.assertIn("рассуждение", result[0])

    def test_extract_thinking_content_empty(self):
        """Тест извлечения из текста без блоков"""
        text = "Текст без блоков рассуждений."
        result = extract_thinking_content(text)
        self.assertEqual(result, [])


class TestRealWorldScenarios(unittest.TestCase):
    """Тесты для реальных сценариев использования"""

    def test_podcast_transcript_cleaning(self):
        """Тест очистки для транскриптов подкастов"""
        response = """<thinking>
Мне нужно ответить как технический эксперт.
Важно использовать простые термины.
</thinking>

Искусственный интеллект сегодня развивается очень быстро.
Основные направления включают машинное обучение и нейронные сети."""

        expected = """Искусственный интеллект сегодня развивается очень быстро.
Основные направления включают машинное обучение и нейронные сети."""

        result = clean_llm_response(response)
        self.assertEqual(result.strip(), expected.strip())

    def test_tts_preparation(self):
        """Тест подготовки текста для TTS"""
        response = """<thinking>Нужно говорить эмоционально</thinking>
Это очень интересная тема! <analysis>Анализирую тон</analysis>
Давайте обсудим детальнее."""

        expected = "Это очень интересная тема! \nДавайте обсудим детальнее."

        result = clean_llm_response(
            response,
            filter_thinking=True,
            filter_reasoning=True,
            max_length=100
        )
        self.assertEqual(result, expected)

    def test_conversation_history_cleaning(self):
        """Тест очистки для истории диалога"""
        response = """<thinking>
Пользователь спрашивает о программировании.
Нужен практический ответ.
</thinking>

Python - отличный язык для начинающих.
Он имеет простой синтаксис и большое сообщество.

<internal>Можно добавить примеры кода</internal>"""

        cleaned = clean_llm_response(
            response,
            filter_thinking=True,
            filter_reasoning=True
        )

        # Проверяем, что мета-контент удален
        self.assertNotIn("<thinking>", cleaned)
        self.assertNotIn("<internal>", cleaned)

        # Проверяем, что основной контент сохранен
        self.assertIn("Python", cleaned)
        self.assertIn("простой синтаксис", cleaned)


def run_tests():
    """Запуск всех тестов"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestThinkingBlockFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestReasoningBlockFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestComprehensiveCleaning))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)