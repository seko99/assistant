"""
Context enrichment module for virtual podcast.

This module handles enriching podcast topics with additional context
through various search providers (mock, web, MCP servers).
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random


@dataclass
class SearchResult:
    """Результат поиска"""
    title: str
    summary: str
    url: Optional[str] = None
    relevance_score: float = 0.0
    source: str = "unknown"


@dataclass
class EnrichedContext:
    """Обогащенный контекст для подкаста"""
    topic: str
    overview: str
    facts: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    search_results: List[SearchResult] = field(default_factory=list)
    search_time: float = 0.0
    search_provider: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "topic": self.topic,
            "overview": self.overview,
            "facts": self.facts,
            "sources": self.sources,
            "search_results": [
                {
                    "title": r.title,
                    "summary": r.summary,
                    "url": r.url,
                    "relevance_score": r.relevance_score,
                    "source": r.source
                }
                for r in self.search_results
            ],
            "search_time": self.search_time,
            "search_provider": self.search_provider
        }


class SearchProvider(ABC):
    """Абстрактный базовый класс для провайдеров поиска"""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Выполняет поиск по запросу"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность провайдера"""
        pass


class MockSearchProvider(SearchProvider):
    """Mock провайдер для тестирования и работы без интернета"""

    def __init__(self):
        # Предзаготовленные результаты для разных тем
        self.mock_data = {
            "искусственный интеллект": [
                SearchResult(
                    title="Развитие ИИ в 2024 году",
                    summary="Искусственный интеллект продолжает развиваться с появлением новых языковых моделей и применений в различных отраслях",
                    url="https://example.com/ai-2024",
                    relevance_score=0.95,
                    source="mock_tech_news"
                ),
                SearchResult(
                    title="Этические аспекты ИИ",
                    summary="Вопросы этики ИИ становятся все более актуальными с развитием технологий машинного обучения",
                    url="https://example.com/ai-ethics",
                    relevance_score=0.88,
                    source="mock_ethics"
                ),
                SearchResult(
                    title="ИИ в бизнесе",
                    summary="Компании активно внедряют ИИ для автоматизации процессов и улучшения эффективности",
                    url="https://example.com/ai-business",
                    relevance_score=0.82,
                    source="mock_business"
                )
            ],
            "криптовалюта": [
                SearchResult(
                    title="Тренды криптовалютного рынка",
                    summary="Криптовалютный рынок показывает волатильность с новыми регулятивными изменениями",
                    url="https://example.com/crypto-trends",
                    relevance_score=0.90,
                    source="mock_finance"
                ),
                SearchResult(
                    title="Технология блокчейн",
                    summary="Блокчейн находит применение не только в криптовалютах, но и в других отраслях",
                    url="https://example.com/blockchain-tech",
                    relevance_score=0.85,
                    source="mock_tech"
                )
            ],
            "климат": [
                SearchResult(
                    title="Изменение климата и технологии",
                    summary="Новые технологии помогают в борьбе с изменением климата и снижении углеродного следа",
                    url="https://example.com/climate-tech",
                    relevance_score=0.92,
                    source="mock_environment"
                ),
                SearchResult(
                    title="Зеленая энергетика",
                    summary="Возобновляемые источники энергии становятся более доступными и эффективными",
                    url="https://example.com/green-energy",
                    relevance_score=0.87,
                    source="mock_energy"
                )
            ],
            "образование": [
                SearchResult(
                    title="Цифровое образование",
                    summary="Онлайн обучение и образовательные технологии меняют подходы к образованию",
                    url="https://example.com/digital-education",
                    relevance_score=0.89,
                    source="mock_education"
                ),
                SearchResult(
                    title="Будущее образования",
                    summary="Персонализированное обучение и ИИ-помощники становятся частью образовательного процесса",
                    url="https://example.com/future-education",
                    relevance_score=0.84,
                    source="mock_future"
                )
            ]
        }

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Выполняет mock поиск"""
        time.sleep(0.5)  # имитируем задержку поиска

        query_lower = query.lower()

        # Ищем подходящие результаты по ключевым словам
        results = []
        for topic, topic_results in self.mock_data.items():
            if any(keyword in query_lower for keyword in topic.split()):
                results.extend(topic_results)

        # Если ничего не найдено, возвращаем общие результаты
        if not results:
            results = [
                SearchResult(
                    title=f"Общая информация по запросу: {query}",
                    summary=f"Тема '{query}' представляет интерес и заслуживает обсуждения с различных точек зрения",
                    url="https://example.com/general",
                    relevance_score=0.5,
                    source="mock_general"
                ),
                SearchResult(
                    title=f"Актуальные тренды: {query}",
                    summary=f"Современные тенденции в области '{query}' показывают интересные направления развития",
                    url="https://example.com/trends",
                    relevance_score=0.45,
                    source="mock_trends"
                )
            ]

        # Сортируем по релевантности и ограничиваем количество
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]

    def is_available(self) -> bool:
        """Mock провайдер всегда доступен"""
        return True


class WebSearchProvider(SearchProvider):
    """Провайдер для веб-поиска (заглушка для будущей реализации)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Заглушка для веб-поиска"""
        # TODO: Реализовать реальный веб-поиск
        raise NotImplementedError("Web search not implemented yet")

    def is_available(self) -> bool:
        """Проверяет наличие API ключа"""
        return self.api_key is not None


class PodcastContextEnricher:
    """Основной класс для обогащения контекста подкаста"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.search_config = config.get('search', {})

        # Инициализируем провайдер поиска
        provider_type = self.search_config.get('provider', 'mock')
        self.search_provider = self._create_search_provider(provider_type)

        # Настройки поиска
        self.max_results = self.search_config.get('max_results', 5)
        self.timeout = self.search_config.get('timeout', 10)

    def _create_search_provider(self, provider_type: str) -> SearchProvider:
        """Создает провайдер поиска по типу"""
        if provider_type == 'mock':
            return MockSearchProvider()
        elif provider_type == 'web':
            api_key = self.search_config.get('api_key')
            return WebSearchProvider(api_key)
        else:
            raise ValueError(f"Unknown search provider: {provider_type}")

    def enrich_context(self, topic: str) -> EnrichedContext:
        """Обогащает контекст для темы подкаста"""
        start_time = time.time()

        # Проверяем доступность провайдера
        if not self.search_provider.is_available():
            return self._create_fallback_context(topic)

        try:
            # Выполняем поиск
            search_results = self.search_provider.search(topic, self.max_results)
            search_time = time.time() - start_time

            # Формируем обогащенный контекст
            context = self._process_search_results(topic, search_results, search_time)
            return context

        except Exception as e:
            print(f"⚠️ Ошибка поиска: {e}")
            return self._create_fallback_context(topic)

    def _process_search_results(self, topic: str, search_results: List[SearchResult], search_time: float) -> EnrichedContext:
        """Обрабатывает результаты поиска в обогащенный контекст"""

        # Формируем обзор темы
        if search_results:
            overview = f"По теме '{topic}' найдено {len(search_results)} релевантных источников. "
            overview += "Основные аспекты для обсуждения включают различные точки зрения и актуальные тренды."
        else:
            overview = f"Тема '{topic}' представляет интерес для детального обсуждения."

        # Извлекаем факты из результатов поиска
        facts = []
        sources = []

        for result in search_results:
            if result.summary and len(result.summary) > 20:
                facts.append(result.summary)

            if result.url:
                sources.append(result.url)
            elif result.source:
                sources.append(result.source)

        # Ограничиваем количество фактов
        facts = facts[:6]
        sources = list(set(sources))[:4]  # убираем дубликаты

        provider_name = type(self.search_provider).__name__.replace('SearchProvider', '').lower()

        return EnrichedContext(
            topic=topic,
            overview=overview,
            facts=facts,
            sources=sources,
            search_results=search_results,
            search_time=search_time,
            search_provider=provider_name
        )

    def _create_fallback_context(self, topic: str) -> EnrichedContext:
        """Создает базовый контекст без поиска"""
        return EnrichedContext(
            topic=topic,
            overview=f"Тема '{topic}' будет обсуждаться участниками подкаста на основе их экспертизы и опыта.",
            facts=[
                f"Тема '{topic}' актуальна в современном мире",
                "Различные эксперты могут иметь разные точки зрения на эту тему",
                "Обсуждение поможет раскрыть разные аспекты темы"
            ],
            sources=["expert_knowledge"],
            search_results=[],
            search_time=0.0,
            search_provider="fallback"
        )

    def refresh_context(self, topic: str, current_context: EnrichedContext) -> EnrichedContext:
        """Обновляет контекст (например, по запросу модератора)"""
        print(f"🔄 Обновление контекста для темы: {topic}")
        return self.enrich_context(topic)

    def is_search_enabled(self) -> bool:
        """Проверяет, включен ли поиск"""
        return self.search_provider.is_available()

    def get_provider_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущем провайдере поиска"""
        return {
            "provider": type(self.search_provider).__name__,
            "available": self.search_provider.is_available(),
            "max_results": self.max_results,
            "timeout": self.timeout
        }