"""
Tests for podcast session functionality
"""

import pytest
from datetime import datetime
from podcast.session import PodcastSession, TranscriptEntry, SessionEvent, ParticipantRole


class TestPodcastSession:
    """Тесты для PodcastSession"""

    def test_session_creation(self):
        """Тест создания сессии"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        assert session.topic == "Test Topic"
        assert session.session_id == "test_123"
        assert session.max_rounds == 3
        assert session.current_round == 0
        assert not session.is_active
        assert not session.is_completed
        assert len(session.participants) == 0
        assert len(session.transcript) == 0

    def test_add_transcript_entry(self):
        """Тест добавления записи в транскрипт"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        session.add_transcript_entry(
            participant_id="moderator",
            participant_name="Тест Модератор",
            role=ParticipantRole.MODERATOR,
            text="Добро пожаловать в подкаст!",
            sources=["test_source"]
        )

        assert len(session.transcript) == 1
        entry = session.transcript[0]
        assert entry.participant_id == "moderator"
        assert entry.participant_name == "Тест Модератор"
        assert entry.role == ParticipantRole.MODERATOR
        assert entry.text == "Добро пожаловать в подкаст!"
        assert entry.sources == ["test_source"]
        assert entry.round_number == 0

    def test_log_event(self):
        """Тест логирования событий"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        session.log_event(
            event_type="test_event",
            message="Тестовое событие",
            participant_id="test_participant",
            extra_data={"key": "value"}
        )

        assert len(session.events) == 1
        event = session.events[0]
        assert event.event_type == "test_event"
        assert event.message == "Тестовое событие"
        assert event.participant_id == "test_participant"
        assert event.extra_data == {"key": "value"}

    def test_round_management(self):
        """Тест управления раундами"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123",
            max_rounds=2
        )

        # Первый раунд
        assert session.start_new_round()
        assert session.current_round == 1
        assert session.can_continue()

        # Второй раунд
        assert session.start_new_round()
        assert session.current_round == 2
        assert not session.can_continue()  # достигнут максимум

        # Третий раунд не должен начаться
        assert not session.start_new_round()
        assert session.current_round == 2

    def test_speaker_queue(self):
        """Тест очереди спикеров"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        session.speaking_queue = ["moderator", "speaker1", "speaker2"]
        session.current_speaker = "moderator"

        # Проверяем получение следующего спикера
        next_speaker = session.get_next_speaker()
        assert next_speaker == "moderator"

        # Переходим к следующему спикеру
        current = session.advance_speaker()
        assert current == "speaker1"
        assert session.current_speaker == "speaker1"
        assert session.speaking_queue == ["speaker1", "speaker2", "moderator"]

    def test_session_completion(self):
        """Тест завершения сессии"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        session.is_active = True
        session.complete_session()

        assert not session.is_active
        assert session.is_completed
        assert len(session.events) == 1
        assert session.events[0].event_type == "session_complete"

    def test_transcript_filtering(self):
        """Тест фильтрации транскрипта по участникам"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        # Добавляем записи разных участников
        session.add_transcript_entry(
            "moderator", "Модератор", ParticipantRole.MODERATOR, "Вопрос 1"
        )
        session.add_transcript_entry(
            "speaker1", "Спикер 1", ParticipantRole.SPEAKER, "Ответ 1"
        )
        session.add_transcript_entry(
            "moderator", "Модератор", ParticipantRole.MODERATOR, "Вопрос 2"
        )

        # Проверяем фильтрацию
        moderator_entries = session.get_transcript_for_participant("moderator")
        assert len(moderator_entries) == 2
        assert all(entry.participant_id == "moderator" for entry in moderator_entries)

        speaker_entries = session.get_transcript_for_participant("speaker1")
        assert len(speaker_entries) == 1
        assert speaker_entries[0].participant_id == "speaker1"

    def test_full_transcript_text(self):
        """Тест получения полного текста транскрипта"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123"
        )

        session.add_transcript_entry(
            "moderator", "Модератор", ParticipantRole.MODERATOR, "Добро пожаловать!"
        )
        session.add_transcript_entry(
            "speaker1", "Спикер", ParticipantRole.SPEAKER, "Спасибо!"
        )

        full_text = session.get_full_transcript_text()
        assert "Модератор: Добро пожаловать!" in full_text
        assert "Спикер: Спасибо!" in full_text

    def test_session_serialization(self):
        """Тест сериализации сессии в словарь"""
        session = PodcastSession(
            topic="Test Topic",
            session_id="test_123",
            max_rounds=2
        )

        session.participants = ["moderator", "speaker1"]
        session.add_transcript_entry(
            "moderator", "Модератор", ParticipantRole.MODERATOR, "Тест"
        )
        session.log_event("test", "Тестовое событие")

        session_dict = session.to_dict()

        assert session_dict["topic"] == "Test Topic"
        assert session_dict["session_id"] == "test_123"
        assert session_dict["max_rounds"] == 2
        assert session_dict["participants"] == ["moderator", "speaker1"]
        assert len(session_dict["transcript"]) == 1
        assert len(session_dict["events"]) == 1


class TestTranscriptEntry:
    """Тесты для TranscriptEntry"""

    def test_transcript_entry_creation(self):
        """Тест создания записи транскрипта"""
        entry = TranscriptEntry(
            participant_id="test_id",
            participant_name="Тест",
            role=ParticipantRole.SPEAKER,
            text="Тестовый текст",
            audio_file="test.wav",
            sources=["source1", "source2"],
            round_number=1
        )

        assert entry.participant_id == "test_id"
        assert entry.participant_name == "Тест"
        assert entry.role == ParticipantRole.SPEAKER
        assert entry.text == "Тестовый текст"
        assert entry.audio_file == "test.wav"
        assert entry.sources == ["source1", "source2"]
        assert entry.round_number == 1

    def test_transcript_entry_serialization(self):
        """Тест сериализации записи транскрипта"""
        entry = TranscriptEntry(
            participant_id="test_id",
            participant_name="Тест",
            role=ParticipantRole.SPEAKER,
            text="Тестовый текст"
        )

        entry_dict = entry.to_dict()

        assert entry_dict["participant_id"] == "test_id"
        assert entry_dict["participant_name"] == "Тест"
        assert entry_dict["role"] == "speaker"
        assert entry_dict["text"] == "Тестовый текст"
        assert "timestamp" in entry_dict


class TestSessionEvent:
    """Тесты для SessionEvent"""

    def test_session_event_creation(self):
        """Тест создания события сессии"""
        event = SessionEvent(
            timestamp=datetime.now(),
            event_type="test",
            message="Тестовое сообщение",
            participant_id="test_participant",
            extra_data={"key": "value"}
        )

        assert event.event_type == "test"
        assert event.message == "Тестовое сообщение"
        assert event.participant_id == "test_participant"
        assert event.extra_data == {"key": "value"}

    def test_session_event_serialization(self):
        """Тест сериализации события сессии"""
        event = SessionEvent(
            timestamp=datetime.now(),
            event_type="test",
            message="Тестовое сообщение"
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "test"
        assert event_dict["message"] == "Тестовое сообщение"
        assert "timestamp" in event_dict