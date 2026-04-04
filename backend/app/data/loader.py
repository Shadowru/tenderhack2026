"""Загрузчик данных СТЕ и Контрактов в Elasticsearch и PostgreSQL.

Обрабатывает проблемы качества данных:
- Дубликаты id СТЕ (5 679 пар) → берём первый
- Дубликаты строк контрактов (767) → дедупликация
- NUL/\x02 байты (4 строки СТЕ) → удаление
- Табуляции в конце name (2 строки) → strip
- Непечатаемые символы в name контрактов (550) → очистка
- BOM в начале файла → пропуск
- Specifications — парсинг key:value из одного поля с кавычками
- Цены < 1 руб (246) → помечаем, не исключаем
- Даты в формате YYYY-MM-DD HH:MM:SS.mmm → парсим
"""
import csv
import re
import logging
import asyncio
from collections import defaultdict
from pathlib import Path
from datetime import datetime

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import asyncpg

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("/app/data")
STE_FILE = DATA_DIR / "СТЕ_20260403.csv"
CONTRACTS_FILE = DATA_DIR / "Контракты_20260403.csv"

# Regex для очистки мусорных символов
CTRL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def clean_text(text: str) -> str:
    """Убрать непечатаемые символы, лишние пробелы/табы."""
    text = CTRL_CHARS.sub('', text)
    text = text.strip().strip('\t')
    text = re.sub(r'\s+', ' ', text)
    return text


def parse_specifications(raw: str) -> str:
    """Парсинг спецификаций из формата 'key:value;key:value' в читаемый текст.

    Deduplicated: identical key:value pairs appear only once.
    Capped at 50 unique specs to avoid bloated index entries.
    """
    raw = raw.strip().strip('"')
    parts = raw.split(';')
    seen = set()
    specs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            key, _, val = part.partition(':')
            key = key.strip()
            val = val.strip()
            if val and val not in ('0', '0.00000', ''):
                canonical = f"{key}: {val}"
            else:
                continue
        else:
            canonical = part
        # Deduplicate
        key_lower = canonical.lower()
        if key_lower in seen:
            continue
        seen.add(key_lower)
        specs.append(canonical)
        if len(specs) >= 50:
            break
    return '; '.join(specs)


def parse_ste_line(line: str) -> dict | None:
    """Парсинг одной строки СТЕ. CSV со сложными кавычками — парсим вручную."""
    # Убираем BOM
    if line.startswith('\ufeff'):
        line = line[1:]

    line = line.rstrip('\r\n')
    if not line:
        return None

    # Формат: id;name;category;"spec1;spec2;spec3"
    # Первые 3 поля — простые, 4-е может быть в кавычках с ; внутри
    parts = line.split(';', 3)
    if len(parts) < 3:
        return None

    ste_id = clean_text(parts[0])
    name = clean_text(parts[1])
    category = clean_text(parts[2])
    # Normalize category: remove trailing dots/ellipsis
    category = category.rstrip('.').rstrip(' ').rstrip('.')
    specs_raw = parts[3] if len(parts) > 3 else ''

    if not ste_id or not name:
        return None

    # Валидация id
    if not ste_id.isdigit():
        return None

    specs = parse_specifications(specs_raw)

    return {
        'id': ste_id,
        'name': name,
        'category': category,
        'specifications': specs,
    }


def iter_ste(path: Path):
    """Итератор по файлу СТЕ с дедупликацией по id."""
    seen_ids = set()
    errors = 0

    with open(path, 'r', encoding='utf-8-sig') as f:
        for lineno, line in enumerate(f, 1):
            try:
                rec = parse_ste_line(line)
                if rec is None:
                    errors += 1
                    continue
                if rec['id'] in seen_ids:
                    continue
                seen_ids.add(rec['id'])
                yield rec
            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning("STE line %d error: %s", lineno, e)

    logger.info("STE parsed: %d unique, %d errors", len(seen_ids), errors)


def parse_contract_line(line: str) -> dict | None:
    """Парсинг строки контракта."""
    if line.startswith('\ufeff'):
        line = line[1:]
    line = line.rstrip('\r\n')
    if not line:
        return None

    # CSV с кавычками — используем csv reader
    try:
        reader = csv.reader([line], delimiter=';', quotechar='"')
        parts = next(reader)
    except Exception:
        return None

    if len(parts) < 11:
        return None

    name = clean_text(parts[0])
    contract_id = parts[1].strip()
    ste_id = parts[2].strip()
    date_str = parts[3].strip()
    price_str = parts[4].strip()
    buyer_inn = parts[5].strip()
    buyer_name = clean_text(parts[6])
    buyer_region = clean_text(parts[7])
    supplier_inn = parts[8].strip()
    supplier_name = clean_text(parts[9])
    supplier_region = clean_text(parts[10]) if len(parts) > 10 else ''

    # Валидация
    if not ste_id.isdigit():
        return None

    try:
        price = float(price_str)
    except (ValueError, TypeError):
        price = 0.0

    try:
        dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        dt = None

    return {
        'contract_id': contract_id,
        'ste_id': ste_id,
        'name': name,
        'date': dt,
        'price': price,
        'buyer_inn': buyer_inn,
        'buyer_name': buyer_name,
        'buyer_region': buyer_region,
        'supplier_inn': supplier_inn,
        'supplier_name': supplier_name,
        'supplier_region': supplier_region,
    }


def iter_contracts(path: Path):
    """Итератор по контрактам с дедупликацией полных дублей."""
    seen = set()
    errors = 0

    with open(path, 'r', encoding='utf-8-sig') as f:
        for lineno, line in enumerate(f, 1):
            try:
                rec = parse_contract_line(line)
                if rec is None:
                    errors += 1
                    continue
                # Дедуп по (contract_id, ste_id)
                key = (rec['contract_id'], rec['ste_id'])
                if key in seen:
                    continue
                seen.add(key)
                yield rec
            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning("Contract line %d error: %s", lineno, e)

    logger.info("Contracts parsed: %d unique, %d errors", len(seen), errors)


async def compute_popularity(contracts_path: Path) -> tuple[dict[str, dict], dict[str, dict[str, int]]]:
    """Подсчитать популярность СТЕ, статистику по заказчикам и профили покупателей.

    Returns:
        ste_stats: ste_id → {count, total_price, popularity, buyer_count}
        buyer_ste_counts: buyer_inn → {ste_id: count}
    """
    logger.info("Computing popularity from contracts...")

    ste_stats: dict[str, dict] = {}  # ste_id → {count, total_price, buyers}
    # buyer_inn → {ste_id: purchase_count} для cold-start персонализации
    buyer_ste_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for rec in iter_contracts(contracts_path):
        sid = rec['ste_id']
        buyer = rec['buyer_inn']

        if sid not in ste_stats:
            ste_stats[sid] = {'count': 0, 'total_price': 0.0, 'buyers': set()}
        ste_stats[sid]['count'] += 1
        ste_stats[sid]['total_price'] += rec['price']
        ste_stats[sid]['buyers'].add(buyer)

        if buyer:
            buyer_ste_counts[buyer][sid] += 1

    # Нормализация popularity в [0, 100]
    max_count = max((s['count'] for s in ste_stats.values()), default=1)
    for sid, s in ste_stats.items():
        s['popularity'] = (s['count'] / max_count) * 100
        s['buyer_count'] = len(s['buyers'])
        del s['buyers']  # экономим память

    logger.info("Popularity computed for %d STE items, %d buyers", len(ste_stats), len(buyer_ste_counts))
    return ste_stats, dict(buyer_ste_counts)


async def index_ste(
    es: AsyncElasticsearch,
    ste_path: Path,
    popularity: dict,
) -> tuple[int, dict[str, str], list[str]]:
    """Индексация СТЕ в Elasticsearch.

    Returns:
        total: количество проиндексированных документов
        ste_category_map: ste_id → category (для вычисления профилей покупателей)
        spell_terms: список уникальных имён и категорий для словаря spell checker
    """
    logger.info("Indexing STE into Elasticsearch...")

    batch = []
    total = 0
    ste_category_map: dict[str, str] = {}
    spell_terms_set: set[str] = set()

    async def flush(actions):
        if actions:
            success, errors = await async_bulk(es, actions, raise_on_error=False)
            if errors:
                logger.warning("Bulk errors: %d", len(errors))
            return success
        return 0

    from app.search.spelling import extract_subject

    for rec in iter_ste(ste_path):
        stats = popularity.get(rec['id'], {})
        subject = extract_subject(rec['name'])
        doc = {
            '_index': settings.es_index,
            '_id': rec['id'],
            '_source': {
                'id': rec['id'],
                'name': rec['name'],
                'subject': subject,
                'category': rec['category'],
                'specifications': rec['specifications'],
                'popularity': stats.get('popularity', 0.0),
                'purchase_count': stats.get('count', 0),
            },
        }
        batch.append(doc)
        total += 1

        # Collect for ste_id → category lookup and spell checker
        if rec['category']:
            ste_category_map[rec['id']] = rec['category']
        spell_terms_set.add(rec['name'])
        if rec['category']:
            spell_terms_set.add(rec['category'])

        if len(batch) >= 2000:
            await flush(batch)
            batch = []
            if total % 50000 == 0:
                logger.info("  indexed %d STE...", total)

    await flush(batch)
    logger.info("STE indexing complete: %d documents", total)
    return total, ste_category_map, list(spell_terms_set)


async def compute_buyer_category_weights(
    buyer_ste_counts: dict[str, dict[str, int]],
    ste_category_map: dict[str, str],
) -> dict[str, dict[str, float]]:
    """Вычислить категорийные веса для каждого покупателя.

    buyer_inn → {category: normalized_weight in [0,1]}
    """
    logger.info("Computing buyer category weights...")
    buyer_cat_weights: dict[str, dict[str, float]] = {}

    for buyer_inn, ste_counts in buyer_ste_counts.items():
        cat_counts: dict[str, int] = defaultdict(int)
        for ste_id, cnt in ste_counts.items():
            cat = ste_category_map.get(ste_id)
            if cat:
                cat_counts[cat] += cnt

        if not cat_counts:
            continue

        max_cnt = max(cat_counts.values())
        buyer_cat_weights[buyer_inn] = {
            cat: cnt / max_cnt
            for cat, cnt in cat_counts.items()
        }

    logger.info("Buyer category weights computed for %d buyers", len(buyer_cat_weights))
    return buyer_cat_weights


async def save_buyer_category_weights(
    buyer_cat_weights: dict[str, dict[str, float]],
):
    """Сохранить веса категорий покупателей в PostgreSQL."""
    logger.info("Saving buyer category weights to PostgreSQL...")

    conn = await asyncpg.connect(
        user=settings.pg_user, password=settings.pg_password,
        database=settings.pg_database, host=settings.pg_host,
    )

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS buyer_category_weights (
                buyer_inn VARCHAR(12) NOT NULL,
                category TEXT NOT NULL,
                weight FLOAT NOT NULL,
                PRIMARY KEY (buyer_inn, category)
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_bcw_buyer ON buyer_category_weights(buyer_inn)"
        )
        # Clear and reload
        await conn.execute("TRUNCATE TABLE buyer_category_weights")

        batch = []
        total = 0
        for buyer_inn, cat_weights in buyer_cat_weights.items():
            for category, weight in cat_weights.items():
                batch.append((buyer_inn, category, weight))
                total += 1
                if len(batch) >= 5000:
                    await conn.executemany(
                        "INSERT INTO buyer_category_weights (buyer_inn, category, weight) "
                        "VALUES ($1, $2, $3)",
                        batch,
                    )
                    batch = []

        if batch:
            await conn.executemany(
                "INSERT INTO buyer_category_weights (buyer_inn, category, weight) "
                "VALUES ($1, $2, $3)",
                batch,
            )

        logger.info("Buyer category weights saved: %d rows for %d buyers", total, len(buyer_cat_weights))
    finally:
        await conn.close()


async def load_contracts_to_pg(contracts_path: Path):
    """Загрузить контракты в PostgreSQL для персонализации."""
    logger.info("Loading contracts into PostgreSQL...")

    conn = await asyncpg.connect(
        user=settings.pg_user, password=settings.pg_password,
        database=settings.pg_database, host=settings.pg_host,
    )

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                contract_id VARCHAR(32),
                ste_id VARCHAR(32) NOT NULL,
                name TEXT,
                contract_date TIMESTAMP,
                price NUMERIC(15,2),
                buyer_inn VARCHAR(12) NOT NULL,
                buyer_name TEXT,
                buyer_region VARCHAR(100),
                supplier_inn VARCHAR(12),
                supplier_name TEXT,
                supplier_region VARCHAR(100)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_contracts_ste ON contracts(ste_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_contracts_buyer ON contracts(buyer_inn)")

        # Clear existing data before reload
        await conn.execute("DELETE FROM contracts")
        logger.info("Cleared existing contracts table")

        batch = []
        total = 0

        for rec in iter_contracts(contracts_path):
            batch.append((
                rec['contract_id'], rec['ste_id'], rec['name'],
                rec['date'], rec['price'],
                rec['buyer_inn'], rec['buyer_name'], rec['buyer_region'],
                rec['supplier_inn'], rec['supplier_name'], rec['supplier_region'],
            ))
            total += 1

            if len(batch) >= 5000:
                await conn.executemany("""
                    INSERT INTO contracts (contract_id, ste_id, name, contract_date, price,
                        buyer_inn, buyer_name, buyer_region, supplier_inn, supplier_name, supplier_region)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                """, batch)
                batch = []
                if total % 100000 == 0:
                    logger.info("  loaded %d contracts...", total)

        if batch:
            await conn.executemany("""
                INSERT INTO contracts (contract_id, ste_id, name, contract_date, price,
                    buyer_inn, buyer_name, buyer_region, supplier_inn, supplier_name, supplier_region)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            """, batch)

        logger.info("Contracts loaded: %d rows", total)
        return total
    finally:
        await conn.close()


async def run_full_load():
    """Полный цикл загрузки данных."""
    es = AsyncElasticsearch(settings.elasticsearch_url)

    try:
        # 1. Популярность из контрактов + профили покупателей
        popularity, buyer_ste_counts = await compute_popularity(CONTRACTS_FILE)

        # 2. Пересоздаём индекс
        if await es.indices.exists(index=settings.es_index):
            await es.indices.delete(index=settings.es_index)
            logger.info("Deleted old index %s", settings.es_index)

        from app.search.engine import ES_SETTINGS, ES_MAPPINGS
        await es.indices.create(
            index=settings.es_index,
            body={"settings": ES_SETTINGS, "mappings": ES_MAPPINGS},
        )
        logger.info("Created fresh index %s", settings.es_index)

        # 3. Индексация СТЕ — получаем карту категорий и термины для spell checker
        ste_count, ste_category_map, spell_terms = await index_ste(es, STE_FILE, popularity)

        # 4. Загрузить словарь spell checker из собранных терминов
        from app.search.spelling import spell_checker
        spell_checker.load_dictionary(spell_terms)
        logger.info(
            "Spell checker dictionary loaded: %d terms", len(spell_checker.dictionary)
        )

        # 5. Вычислить и сохранить веса категорий покупателей
        buyer_cat_weights = await compute_buyer_category_weights(buyer_ste_counts, ste_category_map)
        await save_buyer_category_weights(buyer_cat_weights)

        # 6. Контракты в PG
        contract_count = await load_contracts_to_pg(CONTRACTS_FILE)

        # 7. Refresh ES index
        await es.indices.refresh(index=settings.es_index)

        logger.info("=== LOAD COMPLETE ===")
        logger.info("  STE indexed: %d", ste_count)
        logger.info("  Contracts loaded: %d", contract_count)
        logger.info("  Popularity entries: %d", len(popularity))
        logger.info("  Buyer profiles: %d", len(buyer_cat_weights))
        logger.info("  Spell terms: %d", len(spell_terms))

    finally:
        await es.close()


if __name__ == '__main__':
    asyncio.run(run_full_load())
