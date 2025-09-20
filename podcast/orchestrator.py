"""
Podcast orchestrator module.

This module handles the main flow of the virtual podcast, including
participant management, turn-taking, and session coordination.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .session import PodcastSession, ParticipantRole
from .persona import ParticipantManager, ParticipantProfile
from .context_enricher import PodcastContextEnricher, EnrichedContext
from .context_splitter import ContextSplitter
from core.llm_engine import LLMEngine, LLMSession
from core.text_to_speech import TextToSpeech
from utils.text_filters import filter_thinking_blocks


class PodcastOrchestrator:
    """Основной оркестратор виртуального подкаста"""

    def __init__(self, config: Dict[str, Any], llm_engine: LLMEngine, tts_engine: TextToSpeech):
        self.config = config
        self.podcast_config = config.get('podcast', {})
        self.llm_engine = llm_engine
        self.tts_engine = tts_engine

        # Компоненты подкаста
        self.participant_manager = ParticipantManager()
        self.context_enricher = PodcastContextEnricher(self.podcast_config)
        self.context_splitter = ContextSplitter()

        # Текущая сессия
        self.current_session: Optional[PodcastSession] = None
        self.participant_contexts: Dict[str, Dict[str, Any]] = {}
        self.llm_sessions: Dict[str, LLMSession] = {}

    def start_podcast(self, topic: str, rounds: Optional[int] = None,
                     output_dir: Optional[str] = None, no_audio: bool = False) -> PodcastSession:
        """
        Запускает новый подкаст

        Args:
            topic: Тема подкаста
            rounds: Количество раундов (опционально)
            output_dir: Директория для сохранения (опционально)
            no_audio: Режим только текст без аудио

        Returns:
            Созданная сессия подкаста
        """
        print(f"🎙️ Запуск виртуального подкаста на тему: {topic}")

        # Создаем сессию
        session_id = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        max_rounds = rounds or self.podcast_config.get('default_rounds', 3)
        output_format = "text" if no_audio else self.podcast_config.get('default_output_format', 'both')

        self.current_session = PodcastSession(
            topic=topic,
            session_id=session_id,
            max_rounds=max_rounds,
            output_format=output_format,
            output_directory=output_dir
        )

        # Настраиваем участников
        self._setup_participants()

        # Обогащаем контекст
        enriched_context = self._enrich_context(topic)
        self.current_session.enriched_context = enriched_context.to_dict()

        # Распределяем контекст между участниками
        self._distribute_context(enriched_context)

        # Создаем LLM сессии для участников
        self._create_llm_sessions()

        # Настраиваем выходную директорию
        self._setup_output_directory()

        # Активируем сессию
        self.current_session.is_active = True
        self.current_session.log_event("session_start", f"Подкаст запущен: {topic}")

        print(f"✅ Сессия {session_id} готова к началу")
        return self.current_session

    def run_podcast(self) -> bool:
        """
        Выполняет основной цикл подкаста

        Returns:
            True если подкаст завершился успешно
        """
        if not self.current_session or not self.current_session.is_active:
            print("❌ Нет активной сессии подкаста")
            return False

        try:
            # Открытие подкаста модератором
            self._opening_segment()

            # Основные раунды обсуждения
            for round_num in range(1, self.current_session.max_rounds + 1):
                if not self.current_session.start_new_round():
                    break

                print(f"\n🔄 Раунд {round_num}/{self.current_session.max_rounds}")
                success = self._run_discussion_round()

                if not success:
                    print(f"⚠️ Ошибка в раунде {round_num}")
                    break

            # Завершение подкаста
            self._closing_segment()

            # Финализация сессии
            self.current_session.complete_session()
            print(f"🎉 Подкаст завершен: {self.current_session.session_id}")

            return True

        except Exception as e:
            print(f"❌ Ошибка выполнения подкаста: {e}")
            self.current_session.log_event("error", f"Критическая ошибка: {e}")
            return False

    def _setup_participants(self):
        """Настраивает участников подкаста"""
        # Загружаем участников из конфигурации или используем по умолчанию
        if 'participants' in self.podcast_config:
            self.participant_manager.create_from_config(self.podcast_config)
        else:
            self.participant_manager.load_default_participants()

        # Заполняем список участников в сессии
        for participant_id in self.participant_manager.participants.keys():
            self.current_session.participants.append(participant_id)

        # Настраиваем очередь выступлений (модератор всегда первый)
        speaking_order = self.participant_manager.get_speaking_order()
        self.current_session.speaking_queue = speaking_order.copy()
        self.current_session.current_speaker = speaking_order[0] if speaking_order else None

        print(f"👥 Участники: {', '.join([p.name for p in self.participant_manager.participants.values()])}")

    def _enrich_context(self, topic: str) -> EnrichedContext:
        """Обогащает контекст темы"""
        print("🔍 Обогащение контекста...")
        enriched_context = self.context_enricher.enrich_context(topic)
        print(f"📚 Найдено {len(enriched_context.facts)} фактов из {len(enriched_context.search_results)} источников")
        return enriched_context

    def _distribute_context(self, enriched_context: EnrichedContext):
        """Распределяет контекст между участниками"""
        participants = self.participant_manager.participants
        self.participant_contexts = self.context_splitter.split_context_for_participants(
            enriched_context, participants
        )
        print("📋 Контекст распределен между участниками")

    def _create_llm_sessions(self):
        """Создает LLM сессии для каждого участника"""
        for participant_id, profile in self.participant_manager.participants.items():
            # Получаем персонализированный контекст
            participant_context = self.participant_contexts.get(participant_id, {})

            # Формируем полный системный промпт
            full_prompt = profile.get_full_system_prompt(
                self.current_session.topic,
                self.current_session.enriched_context
            )

            # Создаем LLM сессию
            llm_session = self.llm_engine.create_session(
                system_prompt=full_prompt,
                temperature=profile.temperature
            )

            if llm_session:
                self.llm_sessions[participant_id] = llm_session
                self.current_session.llm_sessions[participant_id] = llm_session
                print(f"🤖 LLM сессия создана для {profile.name}")
            else:
                print(f"⚠️ Не удалось создать LLM сессию для {profile.name}")

    def _setup_output_directory(self):
        """Настраивает директорию для сохранения результатов"""
        if not self.current_session.output_directory:
            output_base = "output"
            self.current_session.output_directory = os.path.join(
                output_base, self.current_session.session_id
            )

        # Создаем директорию
        Path(self.current_session.output_directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Выходная директория: {self.current_session.output_directory}")

    def _opening_segment(self):
        """Открытие подкаста модератором"""
        moderator = self.participant_manager.get_moderator()
        if not moderator:
            raise Exception("Модератор не найден")

        print("\n🎬 Открытие подкаста...")

        # Формируем приветственное сообщение
        participants_list = ", ".join([
            p.name for p in self.participant_manager.get_speakers()
        ])

        opening_prompt = f"""Открой подкаст на тему "{self.current_session.topic}".

Представь:
1. Себя как ведущего
2. Тему подкаста
3. Участников: {participants_list}
4. Краткий анонс того, что будет обсуждаться

Сделай это живо и интересно, создай атмосферу беседы."""

        # Получаем ответ от модератора
        response = self._get_participant_response(moderator.participant_id, opening_prompt)

        if response:
            # Сохраняем в транскрипт
            self.current_session.add_transcript_entry(
                moderator.participant_id,
                moderator.name,
                moderator.role,
                response
            )

            # Синтезируем речь
            self._synthesize_speech(moderator, response, "opening")
        else:
            print("❌ Не удалось получить открытие от модератора")

    def _run_discussion_round(self) -> bool:
        """Выполняет один раунд обсуждения"""
        moderator = self.participant_manager.get_moderator()
        speakers = self.participant_manager.get_speakers()

        if not moderator or not speakers:
            print("❌ Не найдены необходимые участники")
            return False

        # Модератор задает вопрос или делает введение в раунд
        round_intro = self._moderator_round_intro()

        # Каждый спикер высказывается
        for speaker in speakers:
            question = self._moderator_question_for_speaker(speaker)
            speaker_response = self._speaker_response(speaker)

            if not speaker_response:
                print(f"⚠️ Спикер {speaker.name} не ответил")
                continue

            # Короткая связка от модератора
            if speaker != speakers[-1]:  # не для последнего спикера
                self._moderator_transition()

        return True

    def _moderator_round_intro(self) -> Optional[str]:
        """Введение модератора в раунд"""
        moderator = self.participant_manager.get_moderator()
        if not moderator:
            return None

        round_num = self.current_session.current_round
        intro_prompt = f"""Это раунд {round_num} из {self.current_session.max_rounds}.

Сделай краткое введение в этот раунд обсуждения темы "{self.current_session.topic}".
Обозначь направление беседы и подготовь переход к вопросам спикерам."""

        response = self._get_participant_response(moderator.participant_id, intro_prompt)

        if response:
            self.current_session.add_transcript_entry(
                moderator.participant_id,
                moderator.name,
                moderator.role,
                response
            )
            self._synthesize_speech(moderator, response, f"round_{round_num}_intro")

        return response

    def _moderator_question_for_speaker(self, speaker: ParticipantProfile) -> Optional[str]:
        """Модератор задает вопрос конкретному спикеру"""
        moderator = self.participant_manager.get_moderator()
        if not moderator:
            return None

        question_prompt = f"""Задай интересный вопрос {speaker.name} - {speaker.personality_description}.

Учти его экспертизу: {', '.join(speaker.expertise_areas)}

Вопрос должен быть конкретным и позволять раскрыть тему с его точки зрения."""

        response = self._get_participant_response(moderator.participant_id, question_prompt)

        if response:
            self.current_session.add_transcript_entry(
                moderator.participant_id,
                moderator.name,
                moderator.role,
                response
            )
            self._synthesize_speech(moderator, response, f"question_to_{speaker.participant_id}")

        return response

    def _speaker_response(self, speaker: ParticipantProfile) -> Optional[str]:
        """Получает ответ от спикера"""
        # Формируем контекст вопроса
        last_moderator_entry = None
        for entry in reversed(self.current_session.transcript):
            if entry.role == ParticipantRole.MODERATOR:
                last_moderator_entry = entry
                break

        if last_moderator_entry:
            response_prompt = f"""Модератор спросил: "{last_moderator_entry.text}"

Ответь на этот вопрос исходя из своей экспертизы и роли в подкасте."""
        else:
            response_prompt = f"""Выскажи свое мнение по теме "{self.current_session.topic}" исходя из своей экспертизы."""

        response = self._get_participant_response(speaker.participant_id, response_prompt)

        if response:
            self.current_session.add_transcript_entry(
                speaker.participant_id,
                speaker.name,
                speaker.role,
                response
            )
            self._synthesize_speech(speaker, response, f"response_{self.current_session.current_round}")

        return response

    def _moderator_transition(self) -> Optional[str]:
        """Короткая связка модератора между спикерами"""
        moderator = self.participant_manager.get_moderator()
        if not moderator:
            return None

        transition_prompt = """Сделай короткую связку - поблагодари за ответ и сделай переход к следующему участнику.

Максимум 1-2 предложения."""

        response = self._get_participant_response(moderator.participant_id, transition_prompt)

        if response:
            self.current_session.add_transcript_entry(
                moderator.participant_id,
                moderator.name,
                moderator.role,
                response
            )
            self._synthesize_speech(moderator, response, "transition")

        return response

    def _closing_segment(self):
        """Завершение подкаста модератором"""
        moderator = self.participant_manager.get_moderator()
        if not moderator:
            print("❌ Модератор не найден для завершения")
            return

        print("\n🎬 Завершение подкаста...")

        # Формируем итоговое резюме
        transcript_summary = self._get_transcript_summary()

        closing_prompt = f"""Заверши подкаст на тему "{self.current_session.topic}".

Основные моменты обсуждения:
{transcript_summary}

Сделай краткое резюме ключевых идей и поблагодари участников."""

        response = self._get_participant_response(moderator.participant_id, closing_prompt)

        if response:
            self.current_session.add_transcript_entry(
                moderator.participant_id,
                moderator.name,
                moderator.role,
                response
            )
            self._synthesize_speech(moderator, response, "closing")

    def _get_participant_response(self, participant_id: str, prompt: str) -> Optional[str]:
        """Получает ответ от участника через LLM"""
        llm_session = self.llm_sessions.get(participant_id)
        if not llm_session:
            print(f"❌ LLM сессия не найдена для {participant_id}")
            return None

        profile = self.participant_manager.get_participant(participant_id)
        if profile:
            print(f"🎙️ {profile.name} отвечает...")

        try:
            response = llm_session.send_message(prompt)

            # Дополнительная фильтрация thinking-блоков на уровне оркестратора
            # (на случай если они прошли через LLM сессию)
            if response:
                response = filter_thinking_blocks(response)

            return response
        except Exception as e:
            print(f"❌ Ошибка получения ответа от {participant_id}: {e}")
            return None

    def _synthesize_speech(self, profile: ParticipantProfile, text: str, segment_name: str):
        """Синтезирует речь для участника"""
        if self.current_session.output_format == "text":
            print(f"📝 {profile.name}: {text}")
            return

        # Формируем путь для сохранения аудио
        audio_filename = f"{profile.participant_id}_{segment_name}_{int(time.time())}.wav"
        audio_path = os.path.join(self.current_session.output_directory, audio_filename)

        try:
            if self.current_session.output_format == "audio":
                # Только синтез без воспроизведения
                result = self.tts_engine.synthesize_only(
                    text,
                    voice_override=profile.voice_settings.speaker_name,
                    save_path=audio_path
                )
            else:
                # Синтез с воспроизведением
                result = self.tts_engine.synthesize_and_play(
                    text,
                    voice_override=profile.voice_settings.speaker_name,
                    save_path=audio_path
                )

            if result:
                # Обновляем последнюю запись транскрипта с путем к аудио
                if self.current_session.transcript:
                    self.current_session.transcript[-1].audio_file = audio_filename

        except Exception as e:
            print(f"❌ Ошибка синтеза речи для {profile.name}: {e}")

    def _get_transcript_summary(self) -> str:
        """Создает краткое резюме транскрипта для завершения"""
        speakers_points = {}

        for entry in self.current_session.transcript:
            if entry.role == ParticipantRole.SPEAKER:
                if entry.participant_name not in speakers_points:
                    speakers_points[entry.participant_name] = []

                # Берем первые 100 символов ответа как ключевую идею
                key_point = entry.text[:100] + "..." if len(entry.text) > 100 else entry.text
                speakers_points[entry.participant_name].append(key_point)

        summary_parts = []
        for speaker, points in speakers_points.items():
            summary_parts.append(f"{speaker}: {points[0] if points else 'участвовал в обсуждении'}")

        return "\n".join(summary_parts)

    def save_results(self) -> Dict[str, str]:
        """Сохраняет результаты подкаста в файлы"""
        if not self.current_session:
            return {}

        output_dir = self.current_session.output_directory
        results = {}

        try:
            # Сохраняем полный транскрипт в JSON
            transcript_json_path = os.path.join(output_dir, "transcript.json")
            import json
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, ensure_ascii=False, indent=2)
            results['transcript_json'] = transcript_json_path

            # Сохраняем человекочитаемый транскрипт в Markdown
            transcript_md_path = os.path.join(output_dir, "transcript.md")
            with open(transcript_md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Подкаст: {self.current_session.topic}\n\n")
                f.write(f"**Дата:** {self.current_session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Раундов:** {self.current_session.current_round}\n")
                f.write(f"**Участники:** {', '.join([p.name for p in self.participant_manager.participants.values()])}\n\n")

                f.write("## Транскрипт\n\n")
                for entry in self.current_session.transcript:
                    timestamp = entry.timestamp.strftime('%H:%M:%S')
                    f.write(f"**[{timestamp}] {entry.participant_name}:** {entry.text}\n\n")

            results['transcript_md'] = transcript_md_path

            print(f"💾 Результаты сохранены в: {output_dir}")
            return results

        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
            return {}