"""
LLM engine module for the Speech Assistant using local LMStudio API.
Обрабатывает диалог с пользователем через локально запущенную языковую модель.
"""

import time
from typing import Optional, Dict, List

from openai import OpenAI
from utils.config_keys import ConfigKeys


class LLMEngine:
    """Движок для работы с локальной языковой моделью через LMStudio API"""

    def __init__(self, config):
        self.config = config
        self.llm_config = config.get(ConfigKeys.LLM.LLM, {})

        # Настройки подключения
        self.base_url = self.llm_config.get(ConfigKeys.LLM.BASE_URL, "http://127.0.0.1:1234/v1")
        self.model = self.llm_config.get(ConfigKeys.LLM.MODEL, "local-model")
        self.temperature = self.llm_config.get(ConfigKeys.LLM.TEMPERATURE, 0.7)
        self.enabled = self.llm_config.get(ConfigKeys.LLM.ENABLED, True)

        # OpenAI клиент
        self.client = None

        # История диалога
        self.conversation_history = []

        # Системный промпт для ассистента "Иннокентий"
        self.system_prompt = """**Системный промпт (для голосового ассистента "Иннокентий")**

Ты – Иннокентий, голосовой помощник, созданный для того, чтобы отвечать на распознанные фразы пользователей.
Твоя задача: предоставить быстрый, точный и вежливый ответ, сохраняя при этом характер компетентного, дружелюбного и слегка скептического персонажа.

## Общие принципы взаимодействия
1. **Тон** – дружелюбный, но не излишне эмоциональный; всегда сохраняй профессионализм.
2. **Скептицизм** – в случае сомнений или противоречивой информации уточняй детали, указывая на возможные нюансы:
   *«Интересный вопрос! Но стоит помнить, что…»*
3. **Краткость** – ответы не длиннее 2–3 предложений, если пользователь не просит подробностей.
4. **Простота** – избегай жаргона и сложных терминов; объясняй на понятном языке.
5. **Конфиденциальность** – никогда не раскрывай личные данные пользователей, даже если они указаны в запросе.

## Формат ответа
- Если вопрос прост (погода, время, перевод), сразу отвечай:
  *«Сейчас 18 °C и облачно»*.
- Если требуется уточнение:
  *«Можете уточнить дату? Я не уверен, что вы имели в виду»*.
- При сомнении в достоверности источника:
  *«Я нашёл эту информацию в открытых базах, но лучше проверить в официальном источнике»*.

## Технические требования
- Работай с распознанными фразами как строкой текста.
- Если вход содержит несколько вопросов, отвечай по порядку.
- При отсутствии информации – честно скажи: «Извините, я не знаю» и предложи уточнить.

**Итого:**
Иннокентий — компетентный, дружелюбный и слегка скептический голосовой ассистент. Он быстро отвечает на запросы, при этом всегда проверяет факты и оставляет пространство для уточнения."""

    def initialize(self) -> bool:
        """Инициализация подключения к LMStudio API"""
        if not self.enabled:
            print("🤖 LLM отключен в конфигурации")
            return True

        try:
            print(f"🔍 Подключение к LMStudio: {self.base_url}")

            # Инициализируем клиент OpenAI для работы с LMStudio
            self.client = OpenAI(
                base_url=self.base_url,
                api_key="not-needed"  # LMStudio не требует API ключа
            )

            # Инициализируем историю диалога с системным промптом
            self.reset_conversation()

            # Проверяем подключение
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Привет"}],
                temperature=self.temperature,
                max_tokens=50
            )

            print(f"✅ LLM готов (модель: {self.model})")
            return True

        except Exception as e:
            print(f"❌ Ошибка подключения к LLM: {e}")
            print("⚠️ Ассистент продолжит работу без LLM (будет повторять распознанный текст)")
            self.enabled = False
            return False

    def reset_conversation(self):
        """Сброс истории диалога"""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def process_user_input(self, user_text: str) -> Optional[str]:
        """
        Обрабатывает пользовательский ввод и возвращает ответ от LLM

        Args:
            user_text: Распознанный текст пользователя

        Returns:
            Ответ от языковой модели или None в случае ошибки
        """
        if not self.enabled or not self.client or not user_text.strip():
            return None

        start_time = time.time()

        try:
            # Добавляем сообщение пользователя в историю
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })

            print(f"🤔 Обрабатываю: {user_text}")

            # Отправляем весь диалог в модель
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=self.temperature
            )

            # Получаем ответ
            answer = response.choices[0].message.content

            # Добавляем ответ ассистента в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            processing_time = time.time() - start_time
            print(f"💭 Ответ готов (время: {processing_time:.3f}s): {answer}")

            return answer

        except Exception as e:
            print(f"❌ Ошибка обработки LLM: {e}")
            # В случае ошибки возвращаем None, main.py будет использовать fallback
            return None

    def get_conversation_length(self) -> int:
        """Возвращает количество сообщений в диалоге (без системного промпта)"""
        return len(self.conversation_history) - 1  # -1 для системного промпта

    def get_last_user_message(self) -> Optional[str]:
        """Возвращает последнее сообщение пользователя"""
        for message in reversed(self.conversation_history):
            if message["role"] == "user":
                return message["content"]
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Возвращает последний ответ ассистента"""
        for message in reversed(self.conversation_history):
            if message["role"] == "assistant":
                return message["content"]
        return None

    def is_enabled(self) -> bool:
        """Проверяет, включен ли LLM"""
        return self.enabled and self.client is not None