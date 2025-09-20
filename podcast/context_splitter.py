"""
Context splitting module for virtual podcast.

This module handles distributing enriched context among different
participants based on their roles and expertise areas.
"""

from typing import Dict, List, Any, Optional
from .persona import ParticipantProfile, ParticipantRole
from .context_enricher import EnrichedContext


class ContextSplitter:
    """Распределяет контекст между участниками подкаста"""

    def __init__(self):
        pass

    def split_context_for_participants(self,
                                     enriched_context: EnrichedContext,
                                     participants: Dict[str, ParticipantProfile]) -> Dict[str, Dict[str, Any]]:
        """
        Распределяет обогащенный контекст между участниками

        Args:
            enriched_context: Обогащенный контекст темы
            participants: Словарь участников {participant_id: profile}

        Returns:
            Словарь {participant_id: персонализированный контекст}
        """
        distributed_context = {}

        for participant_id, profile in participants.items():
            participant_context = self._create_participant_context(
                enriched_context, profile
            )
            distributed_context[participant_id] = participant_context

        return distributed_context

    def _create_participant_context(self,
                                  enriched_context: EnrichedContext,
                                  profile: ParticipantProfile) -> Dict[str, Any]:
        """Создает персонализированный контекст для участника"""

        # Базовый контекст для всех участников
        participant_context = {
            "topic": enriched_context.topic,
            "overview": enriched_context.overview,
            "role": profile.role.value,
            "participant_name": profile.name
        }

        if profile.role == ParticipantRole.MODERATOR:
            participant_context.update(self._get_moderator_context(enriched_context, profile))
        else:
            participant_context.update(self._get_speaker_context(enriched_context, profile))

        return participant_context

    def _get_moderator_context(self,
                             enriched_context: EnrichedContext,
                             profile: ParticipantProfile) -> Dict[str, Any]:
        """Формирует контекст для модератора"""

        # Модератор получает полный обзор для управления дискуссией
        context = {
            "role_instructions": """Ты ведущий подкаста. Твои задачи:
1. Открыть подкаст представлением темы и участников
2. Задавать вопросы спикерам по очереди
3. Направлять дискуссию и поддерживать диалог
4. Делать плавные переходы между выступлениями
5. Подводить итоги в конце каждого раунда""",

            "full_facts": enriched_context.facts,
            "search_results_summary": self._summarize_search_results(enriched_context),
            "discussion_points": self._generate_discussion_points(enriched_context),
            "transition_phrases": [
                "Интересная точка зрения! А что думает по этому поводу",
                "Спасибо за комментарий. Хотелось бы услышать мнение",
                "Это поднимает важный вопрос. Как видит эту проблему",
                "Давайте рассмотрим другой аспект. Что скажет",
                "Отличный анализ! А как это связано с опытом"
            ]
        }

        return context

    def _get_speaker_context(self,
                           enriched_context: EnrichedContext,
                           profile: ParticipantProfile) -> Dict[str, Any]:
        """Формирует контекст для спикера"""

        # Фильтруем факты по области экспертизы спикера
        relevant_facts = self._filter_facts_by_expertise(
            enriched_context.facts, profile.expertise_areas
        )

        # Подбираем релевантные результаты поиска
        relevant_search_results = self._filter_search_results_by_expertise(
            enriched_context.search_results, profile.expertise_areas
        )

        context = {
            "role_instructions": f"""Ты {profile.personality_description}

Твоя задача в подкасте:
1. Отвечать на вопросы модератора из своей области экспертизы
2. Приводить конкретные примеры и практические кейсы
3. Взаимодействовать с другими участниками
4. Поддерживать живую и интересную дискуссию

Твои области экспертизы: {', '.join(profile.expertise_areas)}
Стиль общения: {profile.speaking_style}""",

            "relevant_facts": relevant_facts,
            "expertise_areas": profile.expertise_areas,
            "speaking_style_tips": self._get_speaking_style_tips(profile.speaking_style),
            "relevant_search_summary": self._summarize_relevant_search_results(relevant_search_results)
        }

        return context

    def _filter_facts_by_expertise(self, facts: List[str], expertise_areas: List[str]) -> List[str]:
        """Фильтрует факты по области экспертизы"""
        if not expertise_areas:
            return facts[:3]  # возвращаем первые 3 факта если нет специализации

        relevant_facts = []
        expertise_keywords = set()

        # Собираем ключевые слова из областей экспертизы
        for area in expertise_areas:
            expertise_keywords.update(area.lower().split())

        # Фильтруем факты по ключевым словам
        for fact in facts:
            fact_lower = fact.lower()
            if any(keyword in fact_lower for keyword in expertise_keywords):
                relevant_facts.append(fact)

        # Если релевантных фактов мало, добавляем общие
        if len(relevant_facts) < 2:
            for fact in facts:
                if fact not in relevant_facts:
                    relevant_facts.append(fact)
                if len(relevant_facts) >= 3:
                    break

        return relevant_facts[:4]  # ограничиваем количество

    def _filter_search_results_by_expertise(self, search_results, expertise_areas):
        """Фильтрует результаты поиска по области экспертизы"""
        if not expertise_areas or not search_results:
            return search_results[:2]

        relevant_results = []
        expertise_keywords = set()

        for area in expertise_areas:
            expertise_keywords.update(area.lower().split())

        for result in search_results:
            result_text = (result.title + " " + result.summary).lower()
            if any(keyword in result_text for keyword in expertise_keywords):
                relevant_results.append(result)

        return relevant_results[:3]

    def _summarize_search_results(self, enriched_context: EnrichedContext) -> str:
        """Создает краткое резюме результатов поиска для модератора"""
        if not enriched_context.search_results:
            return "Результаты поиска недоступны, обсуждение будет основано на экспертизе участников."

        summary_parts = []
        for i, result in enumerate(enriched_context.search_results[:3], 1):
            summary_parts.append(f"{i}. {result.title}: {result.summary[:100]}...")

        return "Ключевые источники:\n" + "\n".join(summary_parts)

    def _summarize_relevant_search_results(self, search_results) -> str:
        """Создает краткое резюме релевантных результатов для спикера"""
        if not search_results:
            return "Дополнительная информация из внешних источников недоступна."

        summaries = []
        for result in search_results[:2]:
            summaries.append(f"• {result.summary}")

        return "Дополнительная информация:\n" + "\n".join(summaries)

    def _generate_discussion_points(self, enriched_context: EnrichedContext) -> List[str]:
        """Генерирует точки для обсуждения для модератора"""
        topic = enriched_context.topic

        base_questions = [
            f"Как каждый из вас видит текущее состояние {topic.lower()}?",
            f"Какие основные вызовы существуют в области {topic.lower()}?",
            f"Какие тенденции вы видите в развитии {topic.lower()}?",
            f"Как {topic.lower()} влияет на повседневную жизнь людей?",
            f"Какие возможности открывает {topic.lower()} в будущем?"
        ]

        # Добавляем вопросы на основе фактов
        fact_based_questions = []
        for fact in enriched_context.facts[:2]:
            if len(fact) > 50:  # берем только содержательные факты
                fact_based_questions.append(f"Что вы думаете о том, что {fact.lower()}?")

        return base_questions + fact_based_questions

    def _get_speaking_style_tips(self, speaking_style: str) -> List[str]:
        """Возвращает советы по стилю общения"""
        style_tips = {
            "professional": [
                "Используй структурированные ответы",
                "Приводи конкретные примеры",
                "Ссылайся на данные и исследования",
                "Поддерживай деловой тон"
            ],
            "casual": [
                "Говори простым языком",
                "Используй понятные аналогии",
                "Делись личным опытом",
                "Будь дружелюбным и открытым"
            ],
            "academic": [
                "Структурируй информацию логично",
                "Ссылайся на исследования и теории",
                "Используй точную терминологию",
                "Анализируй причинно-следственные связи"
            ],
            "enthusiastic": [
                "Проявляй энергию и интерес",
                "Используй яркие примеры",
                "Выражай эмоции по поводу темы",
                "Мотивируй других участников"
            ],
            "analytical": [
                "Структурируй ответы по пунктам",
                "Приводи цифры и статистику",
                "Анализируй плюсы и минусы",
                "Делай обоснованные выводы"
            ],
            "thoughtful": [
                "Рассматривай вопрос с разных сторон",
                "Делись размышлениями и сомнениями",
                "Поднимай глубокие вопросы",
                "Проявляй эмпатию к разным точкам зрения"
            ]
        }

        return style_tips.get(speaking_style, style_tips["professional"])

    def get_context_summary_for_participant(self,
                                          participant_context: Dict[str, Any]) -> str:
        """Создает текстовое резюме контекста для участника"""
        lines = [
            f"Тема подкаста: {participant_context['topic']}",
            f"Твоя роль: {participant_context['role']}",
            f"Имя: {participant_context['participant_name']}",
            "",
            "Обзор темы:",
            participant_context['overview']
        ]

        if 'relevant_facts' in participant_context:
            lines.extend([
                "",
                "Ключевые факты для твоей области:",
                *[f"• {fact}" for fact in participant_context['relevant_facts']]
            ])

        if 'role_instructions' in participant_context:
            lines.extend([
                "",
                "Инструкции:",
                participant_context['role_instructions']
            ])

        return "\n".join(lines)