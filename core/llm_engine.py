"""
LLM engine module for the Speech Assistant using local LMStudio API.
Обрабатывает диалог с пользователем через локально запущенную языковую модель.
"""

import time
from typing import Optional, Dict, List

from openai import OpenAI
from utils.config_keys import ConfigKeys, ConfigSections
from utils.text_filters import filter_thinking_blocks


class LLMSession:
    """Независимая сессия LLM с собственной историей диалога"""

    def __init__(self, client, model: str, system_prompt: str, temperature: float = 0.7, filter_thinking: bool = True):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.filter_thinking = filter_thinking
        self.conversation_history = [
            {"role": "system", "content": system_prompt}
        ]

    def send_message(self, message: str) -> Optional[str]:
        """Отправляет сообщение в рамках этой сессии"""
        if not message.strip():
            return None

        try:
            # Добавляем сообщение пользователя в историю
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            # Отправляем весь диалог в модель
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=self.temperature
            )

            # Получаем ответ
            answer = response.choices[0].message.content

            # Фильтруем thinking-блоки если включена фильтрация
            if self.filter_thinking and answer:
                answer = filter_thinking_blocks(answer)

            # Добавляем ответ ассистента в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            return answer

        except Exception as e:
            print(f"❌ Ошибка LLM сессии: {e}")
            return None

    def get_conversation_length(self) -> int:
        """Возвращает количество сообщений в диалоге (без системного промпта)"""
        return len(self.conversation_history) - 1

    def get_full_conversation(self) -> List[Dict[str, str]]:
        """Возвращает полную историю диалога"""
        return self.conversation_history.copy()

    def reset_conversation(self, new_system_prompt: Optional[str] = None):
        """Сбрасывает историю диалога, опционально с новым системным промптом"""
        if new_system_prompt:
            self.conversation_history = [
                {"role": "system", "content": new_system_prompt}
            ]
        else:
            # Сохраняем только системный промпт
            system_message = self.conversation_history[0]
            self.conversation_history = [system_message]


class LLMEngine:
    """Движок для работы с локальной языковой моделью через LMStudio API"""

    def __init__(self, config):
        self.config = config
        self.llm_config = config.get(ConfigSections.LLM, {})

        # Настройки подключения
        self.base_url = self.llm_config.get(ConfigKeys.LLM.BASE_URL, "http://127.0.0.1:1234/v1")
        self.model = self.llm_config.get(ConfigKeys.LLM.MODEL, "local-model")
        self.temperature = self.llm_config.get(ConfigKeys.LLM.TEMPERATURE, 0.7)
        self.enabled = self.llm_config.get(ConfigKeys.LLM.ENABLED, True)
        self.filter_thinking = self.llm_config.get("filter_thinking_blocks", True)

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

            # Фильтруем thinking-блоки если включена фильтрация
            if self.filter_thinking and answer:
                answer = filter_thinking_blocks(answer)

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

    def create_session(self, system_prompt: str, temperature: Optional[float] = None, filter_thinking: Optional[bool] = None) -> Optional[LLMSession]:
        """
        Создает новую независимую LLM сессию

        Args:
            system_prompt: Системный промпт для сессии
            temperature: Температура для сессии (опционально)
            filter_thinking: Включить фильтрацию thinking-блоков (опционально)

        Returns:
            Новая LLMSession или None если LLM недоступен
        """
        if not self.enabled or not self.client:
            return None

        session_temperature = temperature if temperature is not None else self.temperature
        session_filter_thinking = filter_thinking if filter_thinking is not None else self.filter_thinking

        return LLMSession(
            client=self.client,
            model=self.model,
            system_prompt=system_prompt,
            temperature=session_temperature,
            filter_thinking=session_filter_thinking
        )