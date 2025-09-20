"""
Tests for persona and participant management
"""

import pytest
from podcast.persona import (
    VoiceSettings,
    ParticipantProfile,
    ParticipantManager,
    ParticipantRole,
    create_default_moderator,
    create_tech_expert,
    create_business_analyst,
    create_social_commentator
)


class TestVoiceSettings:
    """Тесты для VoiceSettings"""

    def test_voice_settings_creation(self):
        """Тест создания настроек голоса"""
        voice = VoiceSettings(
            speaker_name="aidar",
            speed=1.2,
            pitch=1.1,
            volume=0.9
        )

        assert voice.speaker_name == "aidar"
        assert voice.speed == 1.2
        assert voice.pitch == 1.1
        assert voice.volume == 0.9

    def test_voice_settings_defaults(self):
        """Тест значений по умолчанию"""
        voice = VoiceSettings(speaker_name="kseniya")

        assert voice.speaker_name == "kseniya"
        assert voice.speed == 1.0
        assert voice.pitch == 1.0
        assert voice.volume == 1.0


class TestParticipantProfile:
    """Тесты для ParticipantProfile"""

    def test_participant_profile_creation(self):
        """Тест создания профиля участника"""
        voice = VoiceSettings(speaker_name="aidar")
        profile = ParticipantProfile(
            participant_id="test_mod",
            name="Тест Модератор",
            role=ParticipantRole.MODERATOR,
            voice_settings=voice,
            personality_description="Тестовый модератор",
            expertise_areas=["тестирование", "модерация"],
            speaking_style="professional",
            system_prompt="Ты тестовый модератор",
            special_instructions="Тестируй все",
            max_response_length=150,
            temperature=0.6
        )

        assert profile.participant_id == "test_mod"
        assert profile.name == "Тест Модератор"
        assert profile.role == ParticipantRole.MODERATOR
        assert profile.voice_settings == voice
        assert profile.personality_description == "Тестовый модератор"
        assert profile.expertise_areas == ["тестирование", "модерация"]
        assert profile.speaking_style == "professional"
        assert profile.system_prompt == "Ты тестовый модератор"
        assert profile.special_instructions == "Тестируй все"
        assert profile.max_response_length == 150
        assert profile.temperature == 0.6

    def test_full_system_prompt_generation(self):
        """Тест генерации полного системного промпта"""
        voice = VoiceSettings(speaker_name="test")
        profile = ParticipantProfile(
            participant_id="test_speaker",
            name="Тест Спикер",
            role=ParticipantRole.SPEAKER,
            voice_settings=voice,
            personality_description="Тестовый эксперт",
            expertise_areas=["тестирование"],
            speaking_style="casual",
            system_prompt="Ты тестовый эксперт",
            special_instructions="Будь дружелюбным",
            max_response_length=200,
            temperature=0.7
        )

        topic = "Тестирование ПО"
        search_context = {
            "facts": ["Факт 1", "Факт 2"],
            "sources": ["source1"]
        }

        full_prompt = profile.get_full_system_prompt(topic, search_context)

        assert topic in full_prompt
        assert profile.name in full_prompt
        assert profile.personality_description in full_prompt
        assert profile.system_prompt in full_prompt
        assert profile.special_instructions in full_prompt
        assert "тестирование" in full_prompt.lower()
        assert "Факт 1" in full_prompt
        assert "200 слов" in full_prompt

    def test_system_prompt_without_search_context(self):
        """Тест генерации промпта без контекста поиска"""
        voice = VoiceSettings(speaker_name="test")
        profile = ParticipantProfile(
            participant_id="test_speaker",
            name="Тест",
            role=ParticipantRole.SPEAKER,
            voice_settings=voice,
            personality_description="Тест",
            use_search_context=False
        )

        full_prompt = profile.get_full_system_prompt("Тема", {"facts": ["Факт"]})

        # Факты не должны включаться если use_search_context=False
        assert "Факт" not in full_prompt

    def test_profile_defaults(self):
        """Тест значений по умолчанию профиля"""
        voice = VoiceSettings(speaker_name="test")
        profile = ParticipantProfile(
            participant_id="test",
            name="Тест",
            role=ParticipantRole.SPEAKER,
            voice_settings=voice,
            personality_description="Тест"
        )

        assert profile.expertise_areas == []
        assert profile.speaking_style == "professional"
        assert profile.system_prompt == ""
        assert profile.special_instructions == ""
        assert profile.max_response_length == 200
        assert profile.temperature == 0.7
        assert profile.use_search_context is True


class TestDefaultProfiles:
    """Тесты для предустановленных профилей"""

    def test_default_moderator(self):
        """Тест профиля модератора по умолчанию"""
        moderator = create_default_moderator()

        assert moderator.participant_id == "moderator"
        assert moderator.name == "Максим"
        assert moderator.role == ParticipantRole.MODERATOR
        assert moderator.voice_settings.speaker_name == "aidar"
        assert "журналист" in moderator.personality_description.lower()
        assert "журналистика" in moderator.expertise_areas
        assert len(moderator.system_prompt) > 0
        assert "ведущий" in moderator.system_prompt.lower()

    def test_tech_expert(self):
        """Тест профиля технического эксперта"""
        expert = create_tech_expert()

        assert expert.participant_id == "tech_expert"
        assert expert.name == "Анна"
        assert expert.role == ParticipantRole.SPEAKER
        assert expert.voice_settings.speaker_name == "kseniya"
        assert "IT" in expert.personality_description or "технолог" in expert.personality_description.lower()
        assert "программирование" in expert.expertise_areas or "технологии" in expert.expertise_areas
        assert "технический" in expert.system_prompt.lower()

    def test_business_analyst(self):
        """Тест профиля бизнес-аналитика"""
        analyst = create_business_analyst()

        assert analyst.participant_id == "business_analyst"
        assert analyst.name == "Дмитрий"
        assert analyst.role == ParticipantRole.SPEAKER
        assert analyst.voice_settings.speaker_name == "eugene"
        assert "бизнес" in analyst.personality_description.lower()
        assert "бизнес" in analyst.expertise_areas or "экономика" in analyst.expertise_areas
        assert "бизнес-аналитик" in analyst.system_prompt.lower()

    def test_social_commentator(self):
        """Тест профиля социального комментатора"""
        commentator = create_social_commentator()

        assert commentator.participant_id == "social_commentator"
        assert commentator.name == "Елена"
        assert commentator.role == ParticipantRole.SPEAKER
        assert commentator.voice_settings.speaker_name == "baya"
        assert "социолог" in commentator.personality_description.lower()
        assert "социология" in commentator.expertise_areas or "общество" in commentator.expertise_areas
        assert "социальный" in commentator.system_prompt.lower()


class TestParticipantManager:
    """Тесты для ParticipantManager"""

    def test_participant_manager_creation(self):
        """Тест создания менеджера участников"""
        manager = ParticipantManager()
        assert len(manager.participants) == 0

    def test_add_participant(self):
        """Тест добавления участника"""
        manager = ParticipantManager()
        voice = VoiceSettings(speaker_name="test")
        profile = ParticipantProfile(
            participant_id="test",
            name="Тест",
            role=ParticipantRole.SPEAKER,
            voice_settings=voice,
            personality_description="Тест"
        )

        manager.add_participant(profile)
        assert len(manager.participants) == 1
        assert "test" in manager.participants
        assert manager.participants["test"] == profile

    def test_get_participant(self):
        """Тест получения участника"""
        manager = ParticipantManager()
        voice = VoiceSettings(speaker_name="test")
        profile = ParticipantProfile(
            participant_id="test",
            name="Тест",
            role=ParticipantRole.SPEAKER,
            voice_settings=voice,
            personality_description="Тест"
        )

        manager.add_participant(profile)

        retrieved = manager.get_participant("test")
        assert retrieved == profile

        not_found = manager.get_participant("nonexistent")
        assert not_found is None

    def test_get_moderator(self):
        """Тест получения модератора"""
        manager = ParticipantManager()

        # Добавляем модератора и спикера
        moderator = create_default_moderator()
        speaker = create_tech_expert()

        manager.add_participant(moderator)
        manager.add_participant(speaker)

        found_moderator = manager.get_moderator()
        assert found_moderator == moderator
        assert found_moderator.role == ParticipantRole.MODERATOR

    def test_get_speakers(self):
        """Тест получения спикеров"""
        manager = ParticipantManager()

        # Добавляем модератора и двух спикеров
        moderator = create_default_moderator()
        speaker1 = create_tech_expert()
        speaker2 = create_business_analyst()

        manager.add_participant(moderator)
        manager.add_participant(speaker1)
        manager.add_participant(speaker2)

        speakers = manager.get_speakers()
        assert len(speakers) == 2
        assert all(speaker.role == ParticipantRole.SPEAKER for speaker in speakers)
        assert speaker1 in speakers
        assert speaker2 in speakers
        assert moderator not in speakers

    def test_get_speaking_order(self):
        """Тест получения порядка выступления"""
        manager = ParticipantManager()

        moderator = create_default_moderator()
        speaker1 = create_tech_expert()
        speaker2 = create_business_analyst()

        manager.add_participant(moderator)
        manager.add_participant(speaker1)
        manager.add_participant(speaker2)

        order = manager.get_speaking_order()

        # Модератор должен быть первым
        assert order[0] == moderator.participant_id
        # Остальные должны быть спикерами
        assert speaker1.participant_id in order
        assert speaker2.participant_id in order
        assert len(order) == 3

    def test_load_default_participants(self):
        """Тест загрузки участников по умолчанию"""
        manager = ParticipantManager()
        manager.load_default_participants()

        assert len(manager.participants) == 4

        # Проверяем наличие всех типов участников
        moderator = manager.get_moderator()
        speakers = manager.get_speakers()

        assert moderator is not None
        assert len(speakers) == 3

        # Проверяем конкретных участников
        participant_ids = set(manager.participants.keys())
        expected_ids = {"moderator", "tech_expert", "business_analyst", "social_commentator"}
        assert participant_ids == expected_ids

    def test_create_from_config(self):
        """Тест создания участников из конфигурации"""
        config = {
            'participants': {
                'test_moderator': {
                    'name': 'Тест Модератор',
                    'role': 'moderator',
                    'voice': {
                        'speaker_name': 'aidar',
                        'speed': 1.1
                    },
                    'personality': 'Тестовый модератор',
                    'expertise': ['тестирование'],
                    'style': 'professional',
                    'system_prompt': 'Ты тестовый модератор',
                    'instructions': 'Тестируй',
                    'max_words': 150,
                    'temperature': 0.6
                },
                'test_speaker': {
                    'name': 'Тест Спикер',
                    'role': 'speaker',
                    'voice': {
                        'speaker_name': 'kseniya'
                    },
                    'personality': 'Тестовый спикер'
                }
            }
        }

        manager = ParticipantManager()
        manager.create_from_config(config)

        assert len(manager.participants) == 2

        # Проверяем модератора
        moderator = manager.get_participant('test_moderator')
        assert moderator is not None
        assert moderator.name == 'Тест Модератор'
        assert moderator.role == ParticipantRole.MODERATOR
        assert moderator.voice_settings.speaker_name == 'aidar'
        assert moderator.voice_settings.speed == 1.1
        assert moderator.expertise_areas == ['тестирование']
        assert moderator.max_response_length == 150
        assert moderator.temperature == 0.6

        # Проверяем спикера
        speaker = manager.get_participant('test_speaker')
        assert speaker is not None
        assert speaker.name == 'Тест Спикер'
        assert speaker.role == ParticipantRole.SPEAKER
        assert speaker.voice_settings.speaker_name == 'kseniya'

    def test_empty_config(self):
        """Тест с пустой конфигурацией"""
        manager = ParticipantManager()
        manager.create_from_config({})

        assert len(manager.participants) == 0

    def test_config_with_defaults(self):
        """Тест конфигурации с использованием значений по умолчанию"""
        config = {
            'participants': {
                'minimal_participant': {
                    'name': 'Минимальный'
                }
            }
        }

        manager = ParticipantManager()
        manager.create_from_config(config)

        participant = manager.get_participant('minimal_participant')
        assert participant is not None
        assert participant.name == 'Минимальный'
        assert participant.role == ParticipantRole.SPEAKER  # по умолчанию
        assert participant.voice_settings.speaker_name == 'aidar'  # по умолчанию