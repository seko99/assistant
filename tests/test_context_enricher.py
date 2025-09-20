"""
Tests for context enricher functionality
"""

import pytest
from podcast.context_enricher import (
    MockSearchProvider,
    PodcastContextEnricher,
    SearchResult,
    EnrichedContext
)


class TestMockSearchProvider:
    """Тесты для MockSearchProvider"""

    def test_mock_provider_availability(self):
        """Тест доступности mock провайдера"""
        provider = MockSearchProvider()
        assert provider.is_available()

    def test_mock_search_ai_topic(self):
        """Тест поиска по теме ИИ"""
        provider = MockSearchProvider()
        results = provider.search("искусственный интеллект", max_results=3)

        assert len(results) >= 1
        assert len(results) <= 3
        assert any("ИИ" in result.title or "интеллект" in result.title.lower() for result in results)
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.relevance_score > 0 for result in results)

    def test_mock_search_crypto_topic(self):
        """Тест поиска по теме криптовалют"""
        provider = MockSearchProvider()
        results = provider.search("криптовалюта", max_results=5)

        assert len(results) >= 1
        assert any("крипто" in result.title.lower() or "блокчейн" in result.title.lower() for result in results)

    def test_mock_search_unknown_topic(self):
        """Тест поиска по неизвестной теме"""
        provider = MockSearchProvider()
        results = provider.search("совершенно_неизвестная_тема_12345", max_results=3)

        # Должны вернуться общие результаты
        assert len(results) >= 1
        assert any("общая информация" in result.title.lower() or "тренды" in result.title.lower() for result in results)

    def test_mock_search_max_results_limit(self):
        """Тест ограничения количества результатов"""
        provider = MockSearchProvider()
        results = provider.search("искусственный интеллект", max_results=2)

        assert len(results) <= 2

    def test_search_result_properties(self):
        """Тест свойств результатов поиска"""
        provider = MockSearchProvider()
        results = provider.search("образование", max_results=1)

        assert len(results) >= 1
        result = results[0]

        assert hasattr(result, 'title')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'url')
        assert hasattr(result, 'relevance_score')
        assert hasattr(result, 'source')

        assert isinstance(result.title, str)
        assert isinstance(result.summary, str)
        assert isinstance(result.relevance_score, float)
        assert isinstance(result.source, str)
        assert len(result.title) > 0
        assert len(result.summary) > 0


class TestPodcastContextEnricher:
    """Тесты для PodcastContextEnricher"""

    def test_enricher_initialization(self):
        """Тест инициализации обогатителя контекста"""
        config = {
            'search': {
                'provider': 'mock',
                'max_results': 5,
                'timeout': 10
            }
        }
        enricher = PodcastContextEnricher(config)

        assert enricher.max_results == 5
        assert enricher.timeout == 10
        assert isinstance(enricher.search_provider, MockSearchProvider)
        assert enricher.search_provider.is_available()

    def test_context_enrichment(self):
        """Тест обогащения контекста"""
        config = {
            'search': {
                'provider': 'mock',
                'max_results': 3
            }
        }
        enricher = PodcastContextEnricher(config)

        context = enricher.enrich_context("искусственный интеллект")

        assert isinstance(context, EnrichedContext)
        assert context.topic == "искусственный интеллект"
        assert len(context.overview) > 0
        assert len(context.facts) >= 0
        assert len(context.sources) >= 0
        assert len(context.search_results) >= 0
        assert context.search_time >= 0
        assert context.search_provider == "mock"

    def test_enrichment_with_results(self):
        """Тест обогащения с результатами поиска"""
        config = {'search': {'provider': 'mock', 'max_results': 3}}
        enricher = PodcastContextEnricher(config)

        context = enricher.enrich_context("криптовалюта")

        # Должны быть факты из результатов поиска
        assert len(context.facts) > 0
        assert len(context.search_results) > 0

        # Факты должны быть из summaries результатов
        result_summaries = [r.summary for r in context.search_results]
        assert any(fact in result_summaries for fact in context.facts)

    def test_context_refresh(self):
        """Тест обновления контекста"""
        config = {'search': {'provider': 'mock'}}
        enricher = PodcastContextEnricher(config)

        original_context = enricher.enrich_context("образование")
        refreshed_context = enricher.refresh_context("образование", original_context)

        assert isinstance(refreshed_context, EnrichedContext)
        assert refreshed_context.topic == "образование"
        # Обновленный контекст может отличаться от оригинального

    def test_search_availability_check(self):
        """Тест проверки доступности поиска"""
        config = {'search': {'provider': 'mock'}}
        enricher = PodcastContextEnricher(config)

        assert enricher.is_search_enabled()

    def test_provider_info(self):
        """Тест получения информации о провайдере"""
        config = {
            'search': {
                'provider': 'mock',
                'max_results': 5,
                'timeout': 15
            }
        }
        enricher = PodcastContextEnricher(config)

        info = enricher.get_provider_info()

        assert 'provider' in info
        assert 'available' in info
        assert 'max_results' in info
        assert 'timeout' in info
        assert info['available'] is True
        assert info['max_results'] == 5
        assert info['timeout'] == 15

    def test_fallback_context(self):
        """Тест fallback контекста при ошибке поиска"""
        # Создаем конфигурацию с недоступным провайдером
        config = {'search': {'provider': 'nonexistent'}}

        try:
            enricher = PodcastContextEnricher(config)
        except ValueError:
            # Ожидаемое поведение для несуществующего провайдера
            pass

        # Тестируем с mock провайдером, но симулируем ошибку
        config = {'search': {'provider': 'mock'}}
        enricher = PodcastContextEnricher(config)

        # Симулируем недоступность провайдера
        enricher.search_provider.is_available = lambda: False

        context = enricher.enrich_context("тест")

        # Должен вернуться fallback контекст
        assert isinstance(context, EnrichedContext)
        assert context.topic == "тест"
        assert context.search_provider == "fallback"
        assert len(context.facts) > 0  # fallback должен содержать базовые факты


class TestEnrichedContext:
    """Тесты для EnrichedContext"""

    def test_enriched_context_creation(self):
        """Тест создания обогащенного контекста"""
        search_results = [
            SearchResult(
                title="Тест",
                summary="Тестовое резюме",
                url="http://test.com",
                relevance_score=0.9,
                source="test_source"
            )
        ]

        context = EnrichedContext(
            topic="Тестовая тема",
            overview="Тестовый обзор",
            facts=["Факт 1", "Факт 2"],
            sources=["source1", "source2"],
            search_results=search_results,
            search_time=1.5,
            search_provider="mock"
        )

        assert context.topic == "Тестовая тема"
        assert context.overview == "Тестовый обзор"
        assert context.facts == ["Факт 1", "Факт 2"]
        assert context.sources == ["source1", "source2"]
        assert len(context.search_results) == 1
        assert context.search_time == 1.5
        assert context.search_provider == "mock"

    def test_enriched_context_serialization(self):
        """Тест сериализации обогащенного контекста"""
        search_results = [
            SearchResult(
                title="Тест",
                summary="Тестовое резюме",
                relevance_score=0.8,
                source="test"
            )
        ]

        context = EnrichedContext(
            topic="Тест",
            overview="Обзор",
            facts=["Факт"],
            sources=["source"],
            search_results=search_results,
            search_time=1.0,
            search_provider="mock"
        )

        context_dict = context.to_dict()

        assert context_dict["topic"] == "Тест"
        assert context_dict["overview"] == "Обзор"
        assert context_dict["facts"] == ["Факт"]
        assert context_dict["sources"] == ["source"]
        assert len(context_dict["search_results"]) == 1
        assert context_dict["search_time"] == 1.0
        assert context_dict["search_provider"] == "mock"

        # Проверяем структуру результата поиска
        result_dict = context_dict["search_results"][0]
        assert result_dict["title"] == "Тест"
        assert result_dict["summary"] == "Тестовое резюме"
        assert result_dict["relevance_score"] == 0.8
        assert result_dict["source"] == "test"


class TestSearchResult:
    """Тесты для SearchResult"""

    def test_search_result_creation(self):
        """Тест создания результата поиска"""
        result = SearchResult(
            title="Тестовый заголовок",
            summary="Тестовое описание",
            url="https://example.com",
            relevance_score=0.95,
            source="test_source"
        )

        assert result.title == "Тестовый заголовок"
        assert result.summary == "Тестовое описание"
        assert result.url == "https://example.com"
        assert result.relevance_score == 0.95
        assert result.source == "test_source"

    def test_search_result_minimal(self):
        """Тест создания минимального результата поиска"""
        result = SearchResult(
            title="Минимальный результат",
            summary="Описание"
        )

        assert result.title == "Минимальный результат"
        assert result.summary == "Описание"
        assert result.url is None
        assert result.relevance_score == 0.0
        assert result.source == "unknown"