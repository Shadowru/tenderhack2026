"""Поисковый движок: гибридный поиск (BM25 + vector) с персонализацией."""
import logging
from typing import Any

from elasticsearch import AsyncElasticsearch

from app.config import settings

logger = logging.getLogger(__name__)

ES_SETTINGS = {
    "analysis": {
        "filter": {
            "russian_stop": {"type": "stop", "stopwords": "_russian_"},
            "russian_stemmer": {"type": "stemmer", "language": "russian"},
            "synonym_filter": {
                "type": "synonym",
                "synonyms_path": "synonyms.txt",
                "updateable": True,
            },
        },
        "analyzer": {
            "russian_custom": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "russian_stop",
                    "russian_stemmer",
                ],
            },
            "russian_with_synonyms": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "synonym_filter",
                    "russian_stop",
                    "russian_stemmer",
                ],
            },
        },
    }
}

ES_MAPPINGS = {
    "properties": {
        "id": {"type": "keyword"},
        "name": {
            "type": "text",
            "analyzer": "russian_custom",
            "search_analyzer": "russian_with_synonyms",
            "fields": {
                "exact": {"type": "keyword"},
                "ngram": {
                    "type": "text",
                    "analyzer": "standard",
                },
            },
        },
        "description": {
            "type": "text",
            "analyzer": "russian_custom",
            "search_analyzer": "russian_with_synonyms",
        },
        "category": {
            "type": "text",
            "analyzer": "russian_custom",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "category_code": {"type": "keyword"},
        "unit": {"type": "keyword"},
        "subject": {
            "type": "text",
            "analyzer": "russian_custom",
            "search_analyzer": "russian_with_synonyms",
            "fields": {
                "raw": {
                    "type": "text",
                    "analyzer": "standard",
                },
                "exact": {"type": "keyword"},
            },
        },
        "specifications": {
            "type": "text",
            "analyzer": "russian_custom",
        },
        "embedding": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine",
        },
        # Глобальная популярность для базового ранжирования
        "popularity": {"type": "float"},
        "purchase_count": {"type": "integer"},
    }
}


class SearchEngine:
    def __init__(self, es: AsyncElasticsearch):
        self.es = es

    async def ensure_index(self):
        """Создать индекс если не существует."""
        exists = await self.es.indices.exists(index=settings.es_index)
        if not exists:
            await self.es.indices.create(
                index=settings.es_index,
                body={"settings": ES_SETTINGS, "mappings": ES_MAPPINGS},
            )
            logger.info("Created index %s", settings.es_index)

    async def search(
        self,
        query: str,
        user_boosts: dict[str, float] | None = None,
        category_boosts: dict[str, float] | None = None,
        size: int = 20,
        offset: int = 0,
        category_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Гибридный поиск: BM25 + function_score с персонализацией.

        user_boosts: {product_id: boost_weight} — персональные веса по товарам.
        category_boosts: {category: boost_weight} — персональные веса по категориям.
        """
        must = []
        filter_clauses = []

        words = query.strip().split()
        is_short = len(words) == 1 and len(words[0]) <= 6

        if is_short:
            # Короткий/незавершённый запрос → prefix + fuzzy только по subject
            must.append({
                "bool": {
                    "should": [
                        # Prefix по subject.raw (без стемминга)
                        {
                            "match_phrase_prefix": {
                                "subject.raw": {
                                    "query": query,
                                    "boost": 20,
                                }
                            }
                        },
                        # Fuzzy по subject.raw: "Ркч" → "ручка"
                        {
                            "match": {
                                "subject.raw": {
                                    "query": query,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 0,
                                    "boost": 8,
                                }
                            }
                        },
                        # Fuzzy по стеммированному subject
                        {
                            "match": {
                                "subject": {
                                    "query": query,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 0,
                                    "boost": 6,
                                }
                            }
                        },
                        # Категория
                        {
                            "match_phrase_prefix": {
                                "category": {
                                    "query": query,
                                    "boost": 3,
                                }
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            })
        else:
            # Полный запрос → bool should с двумя стратегиями
            must.append({
                "bool": {
                    "should": [
                        # Strategy 1: best_fields с fuzzy — ловит опечатки
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "subject^5",
                                    "subject.raw^4",
                                    "name^3",
                                    "name.ngram^1",
                                    "category^2",
                                    "description^1.5",
                                    "specifications",
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "prefix_length": 1,
                                "minimum_should_match": "70%",
                            }
                        },
                        # Strategy 2: phrase match — бустит точные фразы
                        # "туалетная бумага" ↔ "бумага туалетная"
                        {
                            "match_phrase": {
                                "name": {
                                    "query": query,
                                    "boost": 12,
                                    "slop": 3,
                                }
                            }
                        },
                        # Strategy 3: tight phrase match on name (slop=1)
                        # "100 листов" matches "100 листов" but not "500 листов"
                        {
                            "match_phrase": {
                                "name": {
                                    "query": query,
                                    "boost": 20,
                                    "slop": 1,
                                }
                            }
                        },
                        # Strategy 4: all words must match in name (AND) — high boost
                        {
                            "match": {
                                "name": {
                                    "query": query,
                                    "operator": "and",
                                    "boost": 15,
                                }
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            })

        # Буст: subject из одного слова, совпадающего с запросом → точнее чем составной
        from app.search.spelling import morph
        import re as _re
        query_lemmas = set()
        for w in _re.findall(r'[а-яёa-z]+', query.lower()):
            if len(w) >= 3:
                query_lemmas.add(morph.parse(w)[0].normal_form)

        should = []
        if not is_short:
            # Точное совпадение subject с любой леммой запроса
            for lemma in query_lemmas:
                should.append({
                    "term": {
                        "subject.exact": {
                            "value": lemma,
                            "boost": 15,
                        }
                    }
                })
            # Fuzzy match по subject.exact (для опечаток: "карндаш" → "карандаш")
            first_word = query.lower().split()[0] if query.strip() else query
            if len(first_word) >= 4:
                should.append({
                    "fuzzy": {
                        "subject.exact": {
                            "value": first_word,
                            "fuzziness": "AUTO",
                            "prefix_length": 1,
                            "boost": 12,
                        }
                    }
                })
            # Менее строгий match по subject.raw
            should.append({
                "match": {
                    "subject.raw": {
                        "query": query,
                        "boost": 5,
                    }
                }
            })

        if category_filter:
            filter_clauses.append({"term": {"category.keyword": category_filter}})

        # Function score для персонализации
        functions = [
            # Популярность — мягкий буст, не должен доминировать
            {
                "field_value_factor": {
                    "field": "popularity",
                    "factor": 0.5,
                    "modifier": "log2p",
                    "missing": 1,
                }
            },
        ]

        # Персональные бусты по конкретным товарам
        if user_boosts:
            for product_id, weight in list(user_boosts.items())[:50]:
                functions.append({
                    "filter": {"term": {"id": product_id}},
                    "weight": weight,
                })

        # Персональные бусты по категориям — топ-5, fuzzy match по тексту категории
        if category_boosts:
            sorted_cats = sorted(category_boosts.items(), key=lambda x: x[1], reverse=True)
            for category, weight in sorted_cats[:5]:
                functions.append({
                    "filter": {
                        "bool": {
                            "should": [
                                # Точное совпадение — максимальный буст
                                {"term": {"category.keyword": category}},
                                # Текстовое пересечение слов — мягкий буст для смежных категорий
                                {"match": {"category": {"query": category, "minimum_should_match": "75%"}}},
                            ]
                        }
                    },
                    "weight": weight,
                })

        body = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": must,
                            "should": should,
                            "filter": filter_clauses,
                        }
                    },
                    "functions": functions,
                    "score_mode": "sum",
                    "boost_mode": "multiply",
                }
            },
            "from": offset,
            "size": size,
            "highlight": {
                "fields": {
                    "name": {"number_of_fragments": 1},
                    "description": {"number_of_fragments": 2, "fragment_size": 150},
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
            "aggs": {
                "categories": {
                    "terms": {"field": "category.keyword", "size": 20}
                }
            },
        }

        result = await self.es.search(index=settings.es_index, body=body)
        return self._format_response(result, query, user_boosts, category_boosts)

    async def suggest(
        self,
        query: str,
        size: int = 7,
        category_boosts: dict[str, float] | None = None,
    ) -> list[str]:
        """Персонализированный автокомплит."""
        base_query = {
            "multi_match": {
                "query": query,
                "fields": ["subject^4", "name^3", "name.ngram^2", "category"],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "prefix_length": 1,
            }
        }

        if category_boosts:
            functions = []
            sorted_cats = sorted(category_boosts.items(), key=lambda x: x[1], reverse=True)
            for cat, weight in sorted_cats[:5]:
                # Stronger boosts for suggest — amplify the [1.0, 1.05] range
                amplified = 1.0 + (weight - 1.0) * 30  # [1.0, 1.05] → [1.0, 2.5]
                functions.append({
                    "filter": {
                        "bool": {
                            "should": [
                                {"term": {"category.keyword": cat}},
                                {"match": {"category": {"query": cat, "minimum_should_match": "75%"}}},
                            ]
                        }
                    },
                    "weight": amplified,
                })
            query_body = {
                "function_score": {
                    "query": base_query,
                    "functions": functions,
                    "score_mode": "sum",
                    "boost_mode": "multiply",
                }
            }
        else:
            query_body = base_query

        body = {
            "query": query_body,
            "size": size * 4,
            "_source": ["name", "category"],
            "collapse": {"field": "category.keyword"},
        }
        result = await self.es.search(index=settings.es_index, body=body)
        seen = set()
        suggestions = []
        for hit in result["hits"]["hits"]:
            name = hit["_source"]["name"]
            # Truncate long names for cleaner suggestions
            if len(name) > 80:
                name = name[:77] + "..."
            if name not in seen:
                seen.add(name)
                suggestions.append(name)
                if len(suggestions) >= size:
                    break
        return suggestions

    def _format_response(
        self,
        result: dict,
        query: str,
        user_boosts: dict | None = None,
        category_boosts: dict | None = None,
    ) -> dict:
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
        categories = [
            {"name": b["key"], "count": b["doc_count"]}
            for b in result.get("aggregations", {}).get("categories", {}).get("buckets", [])
        ]

        boosted_ids = set(user_boosts.keys()) if user_boosts else set()
        boosted_cats = set(category_boosts.keys()) if category_boosts else set()
        query_lower = query.lower()
        query_words = set(query_lower.split())

        items = []
        for hit in hits:
            source = hit["_source"]
            reasons = self._build_reasons(
                source, query_lower, query_words, boosted_ids, boosted_cats
            )
            item = {
                "id": source.get("id"),
                "name": source.get("name"),
                "description": source.get("description"),
                "category": source.get("category"),
                "category_code": source.get("category_code"),
                "unit": source.get("unit"),
                "specifications": source.get("specifications"),
                "popularity": source.get("popularity", 0),
                "purchase_count": source.get("purchase_count", 0),
                "score": hit["_score"],
                "highlight": hit.get("highlight", {}),
                "reasons": reasons,
            }
            items.append(item)
        return {
            "query": query,
            "total": total,
            "items": items,
            "categories": categories,
        }

    def _build_reasons(
        self,
        source: dict,
        query: str,
        query_words: set,
        boosted_ids: set,
        boosted_cats: set,
    ) -> list[dict]:
        """Построить причины ранжирования из данных документа (без explain)."""
        reasons = []
        name = (source.get("name") or "").lower()
        subject = (source.get("subject") or "").lower()
        category = (source.get("category") or "").lower()
        specs = (source.get("specifications") or "").lower()

        # Subject match — главный фактор
        if any(w in subject for w in query_words) or query in subject:
            reasons.append({
                "type": "text_match",
                "label": "Основной предмет совпадает с запросом",
                "score": None,
            })
        elif subject and any(subject.startswith(q[:3]) for q in query_words if len(q) >= 3):
            reasons.append({
                "type": "text_match",
                "label": "Предмет товара похож на запрос",
                "score": None,
            })

        # Name match
        if any(w in name for w in query_words) or query in name:
            reasons.append({
                "type": "text_match",
                "label": "Совпадение в названии",
                "score": None,
            })

        # Category match
        if any(w in category for w in query_words):
            reasons.append({
                "type": "text_match",
                "label": "Совпадение в категории",
                "score": None,
            })

        # Specs match
        if any(w in specs for w in query_words if len(w) >= 4):
            reasons.append({
                "type": "text_match",
                "label": "Совпадение в характеристиках",
                "score": None,
            })

        # Popularity
        count = source.get("purchase_count", 0)
        if count > 0:
            reasons.append({
                "type": "popularity",
                "label": f"Востребованность: {count} закупок",
                "score": None,
            })

        # Product-level personalization
        doc_id = source.get("id", "")
        if doc_id in boosted_ids:
            reasons.append({
                "type": "personalization",
                "label": "Релевантно вашей истории закупок",
                "score": None,
            })

        # Category-level personalization
        raw_category = source.get("category", "")
        if raw_category and raw_category in boosted_cats:
            reasons.append({
                "type": "personalization",
                "label": "Совпадает с вашими предпочитаемыми категориями",
                "score": None,
            })

        return reasons
