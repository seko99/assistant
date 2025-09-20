"""
Participant persona management for virtual podcast.

This module defines participant profiles, their personalities, voices, and
specialized prompts for different roles in the podcast.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .session import ParticipantRole


@dataclass
class VoiceSettings:
    """Настройки голоса для участника"""
    speaker_name: str  # Имя голоса Silero (например, "aidar", "baya", "kseniya")
    speed: float = 1.0  # Скорость речи
    pitch: float = 1.0  # Высота тона (если поддерживается)
    volume: float = 1.0  # Громкость


@dataclass
class ParticipantProfile:
    """Профиль участника подкаста"""

    # Базовая информация
    participant_id: str
    name: str
    role: ParticipantRole

    # Настройки голоса
    voice_settings: VoiceSettings

    # Личность и стиль
    personality_description: str
    expertise_areas: List[str] = field(default_factory=list)
    speaking_style: str = "professional"  # professional, casual, academic, enthusiastic

    # Промпты и инструкции
    system_prompt: str = ""
    special_instructions: str = ""

    # Дополнительные настройки
    max_response_length: int = 200  # максимальная длина ответа в словах
    temperature: float = 0.7  # температура для LLM
    use_search_context: bool = True  # использовать ли результаты поиска

    def get_full_system_prompt(self, topic: str, search_context: Dict[str, Any] = None) -> str:
        """Формирует полный системный промпт с учетом темы и контекста"""

        base_prompt = f"""Ты участвуешь в подкасте на тему: "{topic}"

Твоя роль: {self.role.value}
Твое имя: {self.name}
Твоя личность: {self.personality_description}
Твой стиль общения: {self.speaking_style}

Области экспертизы: {', '.join(self.expertise_areas) if self.expertise_areas else 'общие знания'}

Основные инструкции:
{self.system_prompt}

Дополнительные указания:
{self.special_instructions}

Ограничения:
- Максимум {self.max_response_length} слов в ответе
- Говори естественно, как в живом разговоре
- Не повторяй информацию, уже озвученную другими участниками
- Будь вовлеченным и заинтересованным в обсуждении"""

        # Добавляем контекст поиска если есть
        if search_context and self.use_search_context:
            if search_context.get('facts'):
                base_prompt += f"\n\nДополнительная информация по теме:\n"
                for fact in search_context['facts'][:3]:  # ограничиваем количество фактов
                    base_prompt += f"- {fact}\n"

            if search_context.get('sources'):
                base_prompt += f"\nИсточники: {', '.join(search_context['sources'][:2])}"

        return base_prompt


# Предустановленные профили участников
def create_default_moderator() -> ParticipantProfile:
    """Создает профиль модератора по умолчанию"""
    return ParticipantProfile(
        participant_id="moderator",
        name="Максим",
        role=ParticipantRole.MODERATOR,
        voice_settings=VoiceSettings(speaker_name="aidar", speed=1.0, volume=1.0),
        personality_description="Опытный журналист и ведущий, умеет направлять дискуссию и задавать интересные вопросы",
        expertise_areas=["журналистика", "медиа", "интервью"],
        speaking_style="professional",
        system_prompt="""Ты - ведущий подкаста. Твоя задача:

1. Открыть подкаст представлением темы и участников
2. Задавать интересные вопросы спикерам
3. Направлять дискуссию и поддерживать диалог
4. Делать краткие связки между выступлениями
5. Подводить итоги в конце каждого раунда
6. Завершить подкаст общим резюме

Стиль: профессиональный, но дружелюбный. Задавай открытые вопросы, которые позволяют спикерам раскрыть тему.""",
        special_instructions="Начинай вопросы с имени спикера. Делай плавные переходы между темами.",
        max_response_length=150,
        temperature=0.6
    )


def create_tech_expert() -> ParticipantProfile:
    """Создает профиль технического эксперта"""
    return ParticipantProfile(
        participant_id="tech_expert",
        name="Анна",
        role=ParticipantRole.SPEAKER,
        voice_settings=VoiceSettings(speaker_name="kseniya", speed=1.0, volume=1.0),
        personality_description="IT-эксперт с большим опытом в разработке и технологиях",
        expertise_areas=["программирование", "искусственный интеллект", "технологии", "разработка"],
        speaking_style="professional",
        system_prompt="""Ты - технический эксперт в подкасте. Твоя роль:

1. Объяснять технические аспекты темы простым языком
2. Приводить конкретные примеры и кейсы
3. Анализировать технические возможности и ограничения
4. Делиться практическим опытом

Стиль: экспертный, но доступный. Избегай сложного жаргона, объясняй термины.""",
        special_instructions="Приводи практические примеры. Если тема сложная, делай аналогии.",
        max_response_length=180,
        temperature=0.7
    )


def create_business_analyst() -> ParticipantProfile:
    """Создает профиль бизнес-аналитика"""
    return ParticipantProfile(
        participant_id="business_analyst",
        name="Дмитрий",
        role=ParticipantRole.SPEAKER,
        voice_settings=VoiceSettings(speaker_name="eugene", speed=1.0, volume=1.0),
        personality_description="Бизнес-аналитик с опытом в стратегии и рыночном анализе",
        expertise_areas=["бизнес", "стратегия", "экономика", "рынки", "инвестиции"],
        speaking_style="analytical",
        system_prompt="""Ты - бизнес-аналитик в подкасте. Твоя роль:

1. Анализировать экономические и рыночные аспекты темы
2. Обсуждать бизнес-модели и стратегии
3. Прогнозировать тренды и перспективы
4. Оценивать риски и возможности

Стиль: аналитический, структурированный. Используй данные и факты для аргументации.""",
        special_instructions="Структурируй ответы логично. Упоминай конкретные цифры и тренды если знаешь.",
        max_response_length=170,
        temperature=0.6
    )


def create_social_commentator() -> ParticipantProfile:
    """Создает профиль социального комментатора"""
    return ParticipantProfile(
        participant_id="social_commentator",
        name="Елена",
        role=ParticipantRole.SPEAKER,
        voice_settings=VoiceSettings(speaker_name="baya", speed=1.0, volume=1.0),
        personality_description="Социолог и журналист, специализируется на общественных процессах",
        expertise_areas=["социология", "культура", "общество", "медиа", "тренды"],
        speaking_style="thoughtful",
        system_prompt="""Ты - социальный комментатор в подкасте. Твоя роль:

1. Анализировать социальные и культурные аспекты темы
2. Обсуждать влияние на общество и повседневную жизнь
3. Рассматривать этические и моральные вопросы
4. Предлагать альтернативные точки зрения

Стиль: вдумчивый, сбалансированный. Учитывай разные мнения и социальные группы.""",
        special_instructions="Поднимай важные социальные вопросы. Будь объективной, но эмоционально вовлеченной.",
        max_response_length=160,
        temperature=0.8
    )


class ParticipantManager:
    """Менеджер для управления участниками подкаста"""

    def __init__(self):
        self.participants: Dict[str, ParticipantProfile] = {}

    def add_participant(self, profile: ParticipantProfile) -> None:
        """Добавляет участника"""
        self.participants[profile.participant_id] = profile

    def get_participant(self, participant_id: str) -> Optional[ParticipantProfile]:
        """Получает участника по ID"""
        return self.participants.get(participant_id)

    def get_moderator(self) -> Optional[ParticipantProfile]:
        """Возвращает модератора"""
        for participant in self.participants.values():
            if participant.role == ParticipantRole.MODERATOR:
                return participant
        return None

    def get_speakers(self) -> List[ParticipantProfile]:
        """Возвращает список спикеров"""
        return [p for p in self.participants.values() if p.role == ParticipantRole.SPEAKER]

    def get_speaking_order(self) -> List[str]:
        """Возвращает порядок выступления (модератор + спикеры)"""
        moderator = self.get_moderator()
        speakers = self.get_speakers()

        order = []
        if moderator:
            order.append(moderator.participant_id)

        for speaker in speakers:
            order.append(speaker.participant_id)

        return order

    def load_default_participants(self) -> None:
        """Загружает участников по умолчанию"""
        self.add_participant(create_default_moderator())
        self.add_participant(create_tech_expert())
        self.add_participant(create_business_analyst())
        self.add_participant(create_social_commentator())

    def create_from_config(self, config: Dict[str, Any]) -> None:
        """Создает участников из конфигурации"""
        participants_config = config.get('participants', {})

        for participant_id, participant_data in participants_config.items():
            role = ParticipantRole(participant_data.get('role', 'speaker'))

            voice_data = participant_data.get('voice', {})
            voice_settings = VoiceSettings(
                speaker_name=voice_data.get('speaker_name', 'aidar'),
                speed=voice_data.get('speed', 1.0),
                volume=voice_data.get('volume', 1.0)
            )

            profile = ParticipantProfile(
                participant_id=participant_id,
                name=participant_data.get('name', participant_id),
                role=role,
                voice_settings=voice_settings,
                personality_description=participant_data.get('personality', ''),
                expertise_areas=participant_data.get('expertise', []),
                speaking_style=participant_data.get('style', 'professional'),
                system_prompt=participant_data.get('system_prompt', ''),
                special_instructions=participant_data.get('instructions', ''),
                max_response_length=participant_data.get('max_words', 200),
                temperature=participant_data.get('temperature', 0.7)
            )

            self.add_participant(profile)