"""
Podcast session management module.

This module defines data structures for managing virtual podcast sessions,
including participants, transcript, and session metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class ParticipantRole(Enum):
    """Роли участников подкаста"""
    MODERATOR = "moderator"
    SPEAKER = "speaker"


@dataclass
class TranscriptEntry:
    """Одна запись в транскрипте подкаста"""
    participant_id: str
    participant_name: str
    role: ParticipantRole
    text: str
    timestamp: datetime
    audio_file: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    round_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON сериализации"""
        return {
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "role": self.role.value,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "audio_file": self.audio_file,
            "sources": self.sources,
            "round_number": self.round_number
        }


@dataclass
class SessionEvent:
    """События сессии для логирования"""
    timestamp: datetime
    event_type: str
    message: str
    participant_id: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON сериализации"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "message": self.message,
            "participant_id": self.participant_id,
            "extra_data": self.extra_data
        }


@dataclass
class PodcastSession:
    """Основной класс для управления сессией подкаста"""

    # Основные параметры сессии
    topic: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # Участники и очередь
    participants: List[str] = field(default_factory=list)  # participant_ids
    speaking_queue: List[str] = field(default_factory=list)  # текущая очередь выступлений
    current_speaker: Optional[str] = None

    # Настройки сессии
    max_rounds: int = 3
    current_round: int = 0
    enable_search: bool = True
    output_format: str = "both"  # "audio", "text", "both"
    output_directory: Optional[str] = None

    # Контент сессии
    enriched_context: Dict[str, Any] = field(default_factory=dict)
    transcript: List[TranscriptEntry] = field(default_factory=list)
    events: List[SessionEvent] = field(default_factory=list)

    # Состояние сессии
    is_active: bool = False
    is_completed: bool = False

    # Ссылки на компоненты (будут установлены при инициализации)
    llm_sessions: Dict[str, Any] = field(default_factory=dict)  # participant_id -> LLMSession

    def add_transcript_entry(self, participant_id: str, participant_name: str,
                           role: ParticipantRole, text: str,
                           audio_file: Optional[str] = None,
                           sources: List[str] = None) -> None:
        """Добавляет запись в транскрипт"""
        entry = TranscriptEntry(
            participant_id=participant_id,
            participant_name=participant_name,
            role=role,
            text=text,
            timestamp=datetime.now(),
            audio_file=audio_file,
            sources=sources or [],
            round_number=self.current_round
        )
        self.transcript.append(entry)

    def log_event(self, event_type: str, message: str,
                  participant_id: Optional[str] = None,
                  extra_data: Dict[str, Any] = None) -> None:
        """Логирует событие сессии"""
        event = SessionEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            message=message,
            participant_id=participant_id,
            extra_data=extra_data or {}
        )
        self.events.append(event)

    def get_next_speaker(self) -> Optional[str]:
        """Возвращает следующего спикера из очереди"""
        if not self.speaking_queue:
            return None
        return self.speaking_queue[0]

    def advance_speaker(self) -> Optional[str]:
        """Переходит к следующему спикеру"""
        if not self.speaking_queue:
            return None

        # Перемещаем текущего спикера в конец очереди
        current = self.speaking_queue.pop(0)
        self.speaking_queue.append(current)

        # Устанавливаем нового текущего спикера
        self.current_speaker = self.speaking_queue[0] if self.speaking_queue else None

        return self.current_speaker

    def start_new_round(self) -> bool:
        """Начинает новый раунд обсуждения"""
        if self.current_round >= self.max_rounds:
            return False

        self.current_round += 1
        self.log_event("round_start", f"Начался раунд {self.current_round}")
        return True

    def can_continue(self) -> bool:
        """Проверяет, может ли сессия продолжаться"""
        return (not self.is_completed and
                self.is_active and
                self.current_round < self.max_rounds)

    def complete_session(self) -> None:
        """Завершает сессию"""
        self.is_active = False
        self.is_completed = True
        self.log_event("session_complete", "Сессия подкаста завершена")

    def get_transcript_for_participant(self, participant_id: str) -> List[TranscriptEntry]:
        """Возвращает все записи транскрипта для конкретного участника"""
        return [entry for entry in self.transcript if entry.participant_id == participant_id]

    def get_full_transcript_text(self) -> str:
        """Возвращает полный транскрипт в текстовом виде"""
        lines = []
        for entry in self.transcript:
            timestamp_str = entry.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{timestamp_str}] {entry.participant_name}: {entry.text}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация сессии в словарь для JSON сериализации"""
        return {
            "topic": self.topic,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "participants": self.participants,
            "speaking_queue": self.speaking_queue,
            "current_speaker": self.current_speaker,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round,
            "enable_search": self.enable_search,
            "output_format": self.output_format,
            "output_directory": self.output_directory,
            "enriched_context": self.enriched_context,
            "transcript": [entry.to_dict() for entry in self.transcript],
            "events": [event.to_dict() for event in self.events],
            "is_active": self.is_active,
            "is_completed": self.is_completed
        }