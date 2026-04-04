"""Исправление опечаток и нормализация запросов."""
import re

import pymorphy3
from rapidfuzz import fuzz, process

morph = pymorphy3.MorphAnalyzer()

# Раскладка клавиатуры EN→RU (частая ошибка: набрали на английской раскладке)
EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,.`"
    'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>~',
    "йцукенгшщзхъфывапролджэячсмитьбюё"
    "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ",
)


def fix_keyboard_layout(text: str) -> str | None:
    """Если текст похож на русский, набранный в EN раскладке — конвертировать."""
    if re.match(r"^[a-zA-Z\[\];',.\s`{}:\"<>~]+$", text):
        return text.translate(EN_TO_RU)
    return None


def normalize_query(query: str) -> str:
    """Базовая нормализация запроса."""
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query.lower()


def lemmatize(text: str) -> list[str]:
    """Лемматизация текста через pymorphy3."""
    words = re.findall(r"[а-яёa-z0-9]+", text.lower())
    return [morph.parse(w)[0].normal_form for w in words]


# Предлоги и служебные слова, после которых идут зависимые существительные
_PREPOSITIONS = frozenset({
    'с', 'со', 'в', 'во', 'на', 'к', 'ко', 'по', 'для', 'из', 'от', 'до',
    'за', 'при', 'без', 'под', 'над', 'об', 'о', 'про', 'через', 'между',
})


def extract_subject(name: str) -> str:
    """Извлечь главное существительное (subject) из названия товара.

    Логика: в названиях товаров subject — это существительное в именительном
    падеже (nomn), обычно стоящее первым. Слова после предлогов или в косвенных
    падежах — зависимые атрибуты.

    Примеры:
      "Ручка шариковая синяя"       → "ручка"
      "Тачка с ручкой"              → "тачка"
      "Бумага для офисной техники"   → "бумага"
      "Картридж лазерный для HP"     → "картридж"
      "Набор реагентов"              → "набор реагентов"
    """
    # Находим слова с позициями, чтобы проверять сокращения (точка после слова)
    tokens = re.finditer(r"[а-яёА-ЯЁa-zA-Z0-9]+", name)
    word_list = []
    for m in tokens:
        w = m.group()
        end_pos = m.end()
        # Проверяем, является ли сокращением (точка сразу после слова)
        is_abbrev = end_pos < len(name) and name[end_pos] == '.'
        word_list.append((w, is_abbrev))

    if not word_list:
        return name

    subjects = []
    after_prep = False
    after_brand = False  # после латиницы (бренд/модель) — стоп

    for w, is_abbrev in word_list:
        wl = w.lower()

        # Пропускаем одиночные/двойные буквы (единицы: г, мг, мл, л, шт)
        # и чистые числа
        if len(wl) <= 2:
            continue
        if re.match(r'^[0-9]+$', w):
            continue

        # Сокращения (руч., бл., табл.) — не subject
        if is_abbrev and len(wl) <= 5:
            continue

        # Латиница — бренд/модель. Берём первый рядом с subject, потом стоп.
        if re.match(r'^[a-zA-Z]+$', w):
            if not after_prep and subjects and len(w) >= 2 and not after_brand:
                subjects.append(w)
                after_brand = True
            continue

        if wl in _PREPOSITIONS:
            after_prep = True
            continue

        # После бренда — маловероятно что будет ещё subject
        if after_brand:
            continue

        # Check all parses — first may be wrong for ambiguous words
        # e.g. "треска" → first parse: gent от "треск", but also nomn "треска" (fish)
        parses = morph.parse(wl)
        parsed = parses[0]
        pos = parsed.tag.POS
        case = parsed.tag.case

        # Look for nominative interpretation among all parses
        best_nomn = None
        for p in parses:
            if p.tag.POS == 'NOUN' and p.tag.case == 'nomn':
                best_nomn = p
                break

        if after_prep:
            continue

        if pos == 'NOUN':
            if case in ('nomn', None):
                subjects.append(parsed.normal_form)
            elif best_nomn:
                # Ambiguous word: first parse not nomn but alternative is
                # e.g. "треска" → "треск"(gent) vs "треска"(nomn) → prefer nomn
                subjects.append(best_nomn.normal_form)
            elif case == 'gent' and subjects:
                subjects.append(parsed.normal_form)
        elif pos in ('ADJF', 'PRTF'):
            continue
        elif pos is None:
            if not subjects and len(wl) >= 3:
                subjects.append(w)

    if not subjects:
        for w, _ in word_list:
            if len(w) >= 3 and re.match(r'[а-яёА-ЯЁ]', w):
                subjects.append(morph.parse(w.lower())[0].normal_form)
                break

    return ' '.join(subjects[:3]) if subjects else name.split(',')[0].split('(')[0].strip()


class SpellChecker:
    """Проверка опечаток через fuzzy-matching по словарю известных товаров."""

    def __init__(self):
        self.dictionary: list[str] = []

    def load_dictionary(self, terms: list[str]):
        """Загрузить словарь терминов (названия товаров, категории)."""
        self.dictionary = list({t for t in terms if len(t) >= 4})

    def correct(self, query: str, threshold: int = 65) -> str | None:
        """Вернуть исправленный запрос или None если всё ок."""
        if not self.dictionary:
            return None
        result = process.extractOne(query, self.dictionary, scorer=fuzz.WRatio)
        if result and result[1] >= threshold and result[0].lower() != query.lower():
            return result[0]
        return None


spell_checker = SpellChecker()
