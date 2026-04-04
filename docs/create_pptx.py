"""Generate a modern business presentation for TenderHack 2026."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Brand colors
RED = RGBColor(0xE5, 0x39, 0x35)
RED_DARK = RGBColor(0xC6, 0x28, 0x28)
BLUE = RGBColor(0x19, 0x76, 0xD2)
DARK = RGBColor(0x33, 0x40, 0x59)
GRAY = RGBColor(0x66, 0x66, 0x66)
LIGHT_GRAY = RGBColor(0x99, 0x99, 0x99)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
ACCENT_GREEN = RGBColor(0x43, 0xA0, 0x47)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

W = prs.slide_width
H = prs.slide_height


def add_bg(slide, color=WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, left, top, width, height, text, font_size=18, color=DARK, bold=False, alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = alignment
    return txBox


def add_multiline(slide, left, top, width, height, lines, font_size=16, color=DARK, spacing=1.2):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, (text, is_bold, line_color) in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = line_color or color
        p.font.bold = is_bold
        p.space_after = Pt(font_size * (spacing - 1) * 2)
    return txBox


def slide_header(slide, number, title):
    """Add consistent header bar to slide."""
    add_rect(slide, 0, 0, W, Inches(0.08), RED)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(1), Inches(0.4),
             f"{number:02d}", font_size=14, color=RED, bold=True)
    add_text(slide, Inches(1.3), Inches(0.25), Inches(10), Inches(0.5),
             title, font_size=24, color=DARK, bold=True)
    # Subtle line under header
    add_rect(slide, Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.02), RGBColor(0xE0, 0xE0, 0xE0))


def add_stat_card(slide, left, top, value, label, accent=RED):
    card = add_rounded_rect(slide, left, top, Inches(2.4), Inches(1.4), WHITE, RGBColor(0xE0, 0xE0, 0xE0))
    # Accent top bar
    add_rect(slide, left + Inches(0.02), top + Inches(0.02), Inches(2.36), Inches(0.06), accent)
    add_text(slide, left + Inches(0.3), top + Inches(0.25), Inches(1.8), Inches(0.6),
             value, font_size=32, color=DARK, bold=True, alignment=PP_ALIGN.CENTER)
    add_text(slide, left + Inches(0.2), top + Inches(0.85), Inches(2.0), Inches(0.4),
             label, font_size=11, color=GRAY, alignment=PP_ALIGN.CENTER)


# ================================================================
# SLIDE 1: Title
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide, DARK)
add_rect(slide, 0, Inches(0), W, Inches(0.12), RED)

add_text(slide, Inches(1.5), Inches(1.5), Inches(10), Inches(1),
         "ПЕРСОНАЛИЗИРОВАННЫЙ", font_size=44, color=WHITE, bold=True)
add_text(slide, Inches(1.5), Inches(2.2), Inches(10), Inches(1),
         "УМНЫЙ ПОИСК ПРОДУКЦИИ", font_size=44, color=RED, bold=True)

add_text(slide, Inches(1.5), Inches(3.5), Inches(10), Inches(0.6),
         "Портал поставщиков — zakupki.mos.ru", font_size=20, color=LIGHT_GRAY)

add_rect(slide, Inches(1.5), Inches(4.5), Inches(3), Inches(0.04), RED)

add_text(slide, Inches(1.5), Inches(5.0), Inches(10), Inches(0.5),
         "TenderHack 2026", font_size=18, color=LIGHT_GRAY)
add_text(slide, Inches(1.5), Inches(5.5), Inches(10), Inches(0.5),
         "tenderhack.extra.moscow", font_size=16, color=BLUE)

# ================================================================
# SLIDE 2: Problem
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 1, "ПРОБЛЕМА")

add_text(slide, Inches(0.8), Inches(1.2), Inches(11), Inches(0.6),
         "537 000 товаров. 4 190 организаций. Одна поисковая строка.",
         font_size=22, color=DARK, bold=True)

# Three scenario cards
scenarios = [
    ("Больница", "Ищет «бумага»", "Нужна бумага для ЭКГ,\nтермобумага, офисная", RGBColor(0xE3, 0xF2, 0xFD)),
    ("Школа", "Ищет «бумага»", "Нужны бланки для грамот,\nсертификат-бумага", RGBColor(0xFB, 0xE9, 0xE7)),
    ("Колледж", "Ищет «бумага»", "Нужна одноразовая посуда\nиз ламинированной бумаги", RGBColor(0xE8, 0xF5, 0xE9)),
]

for i, (who, query, need, bg) in enumerate(scenarios):
    left = Inches(0.8 + i * 4.0)
    card = add_rounded_rect(slide, left, Inches(2.2), Inches(3.6), Inches(2.5), bg, RGBColor(0xE0, 0xE0, 0xE0))
    add_text(slide, left + Inches(0.3), Inches(2.4), Inches(3.0), Inches(0.4),
             who, font_size=20, color=DARK, bold=True)
    add_text(slide, left + Inches(0.3), Inches(2.85), Inches(3.0), Inches(0.3),
             query, font_size=14, color=GRAY)
    add_text(slide, left + Inches(0.3), Inches(3.4), Inches(3.0), Inches(1.0),
             need, font_size=13, color=DARK)

# Arrow + result
add_text(slide, Inches(0.8), Inches(5.2), Inches(11), Inches(0.5),
         "Сегодня: все получают одинаковый результат — SvetoCopy A4",
         font_size=16, color=RED, bold=True)

add_text(slide, Inches(0.8), Inches(5.8), Inches(11), Inches(0.5),
         "Наша задача: каждый видит то, что нужно именно ему",
         font_size=18, color=ACCENT_GREEN, bold=True)

# ================================================================
# SLIDE 3: Solution — 4 levels
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 2, "РЕШЕНИЕ — 4 УРОВНЯ ИНТЕЛЛЕКТА")

levels = [
    ("01", "Морфологический\nпоиск", "Русская морфология\nSubject extraction\n«ручка» ≠ «тачка с ручкой»", BLUE),
    ("02", "Опечатки\nи синонимы", "490K словарь\nEN→RU раскладка\n123 правила синонимов", RGBColor(0x7B, 0x1F, 0xA2)),
    ("03", "Персонализация", "Cold start из 2M контрактов\n4 190 профилей организаций\nDynamic re-ranking", RED),
    ("04", "AI-расширение\n(RAG)", "Qwen 2.5 7B (Ollama)\nES категории → LLM\nНечёткие запросы", ACCENT_GREEN),
]

for i, (num, title, desc, color) in enumerate(levels):
    left = Inches(0.6 + i * 3.1)
    top = Inches(1.3)
    # Number circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, left + Inches(0.9), top, Inches(0.7), Inches(0.7))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = num
    tf.paragraphs[0].font.size = Pt(18)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    add_text(slide, left + Inches(0.1), top + Inches(0.9), Inches(2.5), Inches(0.8),
             title, font_size=16, color=DARK, bold=True, alignment=PP_ALIGN.CENTER)

    # Description card
    card = add_rounded_rect(slide, left, top + Inches(1.7), Inches(2.8), Inches(2.0), BG_GRAY)
    add_text(slide, left + Inches(0.2), top + Inches(1.9), Inches(2.4), Inches(1.6),
             desc, font_size=12, color=GRAY)

# Bottom stat
add_text(slide, Inches(0.8), Inches(5.8), Inches(11), Inches(0.5),
         "Качество поиска: 93% — релевантный результат в топ-5 (134 тестовых запроса)",
         font_size=16, color=DARK, bold=True)

# ================================================================
# SLIDE 4: BPMN Process Flow
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 3, "ПРОЦЕСС ОБРАБОТКИ ЗАПРОСА (BPMN)")

# BPMN flow — horizontal process with swimlanes
lanes = [
    ("Пользователь", Inches(1.0), RGBColor(0xE3, 0xF2, 0xFD)),
    ("Backend", Inches(2.6), RGBColor(0xFB, 0xE9, 0xE7)),
    ("Elasticsearch", Inches(4.2), RGBColor(0xE8, 0xF5, 0xE9)),
    ("Redis / PG", Inches(5.8), RGBColor(0xFE, 0xF3, 0xE2)),
]

# Draw swimlanes
for name, top, bg in lanes:
    add_rect(slide, Inches(0.6), top, Inches(12.0), Inches(1.4), bg, RGBColor(0xD0, 0xD0, 0xD0))
    add_text(slide, Inches(0.7), top + Inches(0.05), Inches(1.3), Inches(0.3),
             name, font_size=9, color=DARK, bold=True)

# Process steps as rounded rects with arrows
def bpmn_step(slide, left, top, width, text, color=DARK, fill=WHITE, is_start=False, is_end=False):
    if is_start:
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, Inches(0.45), Inches(0.45))
        shape.fill.solid()
        shape.fill.fore_color.rgb = ACCENT_GREEN
        shape.line.fill.background()
        return shape
    if is_end:
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, Inches(0.45), Inches(0.45))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RED
        shape.line.color.rgb = RED_DARK
        shape.line.width = Pt(3)
        return shape

    shape = add_rounded_rect(slide, left, top, width, Inches(0.55), fill, RGBColor(0xBB, 0xBB, 0xBB))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = text
    tf.paragraphs[0].font.size = Pt(8)
    tf.paragraphs[0].font.color.rgb = color
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return shape

# Diamond (gateway)
def bpmn_gateway(slide, left, top, text):
    shape = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, left, top, Inches(0.6), Inches(0.6))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xFF, 0xF9, 0xC4)
    shape.line.color.rgb = RGBColor(0xF9, 0xA8, 0x25)
    shape.line.width = Pt(1.5)
    tf = shape.text_frame
    tf.paragraphs[0].text = text
    tf.paragraphs[0].font.size = Pt(7)
    tf.paragraphs[0].font.color.rgb = DARK
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return shape

# Arrow connector
def bpmn_arrow(slide, x1, y1, x2, y2):
    connector = slide.shapes.add_connector(1, x1, y1, x2, y2)  # straight
    connector.line.color.rgb = RGBColor(0x99, 0x99, 0x99)
    connector.line.width = Pt(1.5)

# Row 1 — User lane
bpmn_step(slide, Inches(2.0), Inches(1.35), 0, "", is_start=True)
bpmn_step(slide, Inches(2.8), Inches(1.25), Inches(1.3), "Ввод запроса")
bpmn_arrow(slide, Inches(2.45), Inches(1.55), Inches(2.8), Inches(1.55))

# Row 2 — Backend lane
bpmn_step(slide, Inches(2.8), Inches(2.85), Inches(1.1), "Нормализация\nраскладка")
bpmn_step(slide, Inches(4.1), Inches(2.85), Inches(1.1), "Spell check\n490K словарь")
bpmn_gateway(slide, Inches(5.45), Inches(2.75), "≤6\nсимв?")
bpmn_step(slide, Inches(6.3), Inches(2.65), Inches(1.2), "Prefix\nsubject.raw")
bpmn_step(slide, Inches(6.3), Inches(3.25), Inches(1.2), "Multi-match\n4 стратегии")
bpmn_step(slide, Inches(7.8), Inches(2.85), Inches(1.2), "Function\nscore")
bpmn_step(slide, Inches(9.2), Inches(2.85), Inches(1.1), "RAG\nLLM (Ollama)")
bpmn_step(slide, Inches(10.5), Inches(2.85), Inches(1.1), "Формирование\nответа")

# Row 3 — ES lane
bpmn_step(slide, Inches(7.8), Inches(4.45), Inches(1.2), "BM25 + fuzzy\n+ synonyms")
bpmn_step(slide, Inches(9.2), Inches(4.45), Inches(1.1), "Category\naggregation")
bpmn_step(slide, Inches(10.5), Inches(4.45), Inches(1.1), "Filtered\nsearch")

# Row 4 — Redis/PG lane
bpmn_step(slide, Inches(4.1), Inches(6.05), Inches(1.1), "Cold start\nPG → Redis")
bpmn_step(slide, Inches(5.5), Inches(6.05), Inches(1.1), "Product\nboosts")
bpmn_step(slide, Inches(6.9), Inches(6.05), Inches(1.1), "Category\nboosts")
bpmn_step(slide, Inches(10.5), Inches(6.05), Inches(1.1), "Track event\nlog")

# End
bpmn_step(slide, Inches(11.85), Inches(1.35), 0, "", is_end=True)

# Vertical arrows (lane crossings)
bpmn_arrow(slide, Inches(3.35), Inches(1.8), Inches(3.35), Inches(2.85))
bpmn_arrow(slide, Inches(8.4), Inches(3.4), Inches(8.4), Inches(4.45))
bpmn_arrow(slide, Inches(5.5), Inches(3.4), Inches(5.5), Inches(6.05))
bpmn_arrow(slide, Inches(11.05), Inches(3.4), Inches(11.05), Inches(5.8))
bpmn_arrow(slide, Inches(11.05), Inches(1.55), Inches(11.85), Inches(1.55))

# Horizontal arrows
for x1, x2, y in [
    (4.1, 4.1, 1.55), (3.9, 4.1, 3.1), (5.2, 5.45, 3.1),
    (6.05, 6.3, 2.9), (6.05, 6.3, 3.5), (7.5, 7.8, 3.1),
    (9.0, 9.2, 3.1), (10.3, 10.5, 3.1), (10.3, 10.5, 4.7),
    (9.0, 9.2, 4.7), (8.0, 8.4, 6.3), (6.0, 6.3, 6.3),
]:
    bpmn_arrow(slide, Inches(x1), Inches(y), Inches(x2), Inches(y))

# ================================================================
# SLIDE 5: Personalization Demo
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 4, "ПЕРСОНАЛИЗАЦИЯ В ДЕЙСТВИИ")

add_text(slide, Inches(0.8), Inches(1.1), Inches(11), Inches(0.5),
         'Один запрос «бумага» — три разных результата:',
         font_size=18, color=DARK, bold=True)

demos = [
    ("Школа", "5003021368", ["Дизайн-бумага Металлик", "Сертификат-бумага Attache", "Бумага для творчества"], "Бланки для грамот\nи сертификатов", RGBColor(0xE3, 0xF2, 0xFD), BLUE),
    ("Колледж", "7716237684", ["Тарелка из ламинированной бумаги", "Стакан бумажный одноразовый", "Ролик подачи бумаги"], "Столовая + расходники\nдля принтеров", RGBColor(0xFB, 0xE9, 0xE7), RED),
    ("Больница", "7734091519", ["SvetoCopy Classic А4", "SvetoCopy (А4, 80 г/кв.м)", "ОФИСМАГ СТАНДАРТ А4"], "Стандартная\nофисная бумага", RGBColor(0xE8, 0xF5, 0xE9), ACCENT_GREEN),
]

for i, (who, inn, results, why, bg, accent) in enumerate(demos):
    left = Inches(0.6 + i * 4.1)
    top = Inches(1.8)

    card = add_rounded_rect(slide, left, top, Inches(3.8), Inches(4.2), bg, accent)

    add_text(slide, left + Inches(0.3), top + Inches(0.2), Inches(3.2), Inches(0.4),
             who, font_size=20, color=accent, bold=True)
    add_text(slide, left + Inches(0.3), top + Inches(0.6), Inches(3.2), Inches(0.3),
             f"ИНН: {inn}", font_size=10, color=GRAY)

    add_text(slide, left + Inches(0.3), top + Inches(1.0), Inches(3.2), Inches(0.3),
             "Результаты:", font_size=11, color=DARK, bold=True)

    for j, r in enumerate(results):
        add_text(slide, left + Inches(0.3), top + Inches(1.35 + j * 0.4), Inches(3.2), Inches(0.35),
                 f"  {j+1}. {r}", font_size=11, color=DARK)

    add_rect(slide, left + Inches(0.3), top + Inches(2.8), Inches(3.2), Inches(0.02), accent)

    add_text(slide, left + Inches(0.3), top + Inches(3.0), Inches(3.2), Inches(0.3),
             "Почему:", font_size=11, color=accent, bold=True)
    add_text(slide, left + Inches(0.3), top + Inches(3.3), Inches(3.2), Inches(0.7),
             why, font_size=11, color=GRAY)

# Bottom
add_text(slide, Inches(0.8), Inches(6.4), Inches(11), Inches(0.4),
         "Персонализация подсказок тоже работает — автокомплит учитывает профиль организации",
         font_size=13, color=GRAY)

# ================================================================
# SLIDE 6: Key Metrics
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 5, "КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ")

# Stat cards — top row
add_stat_card(slide, Inches(0.6), Inches(1.2), "537 314", "Товаров проиндексировано", RED)
add_stat_card(slide, Inches(3.3), Inches(1.2), "2 009 457", "Контрактов проанализировано", BLUE)
add_stat_card(slide, Inches(6.0), Inches(1.2), "4 190", "Организаций с профилями", ACCENT_GREEN)
add_stat_card(slide, Inches(8.7), Inches(1.2), "490 204", "Терминов в словаре", RGBColor(0x7B, 0x1F, 0xA2))
add_stat_card(slide, Inches(11.4), Inches(1.2), "93%", "Качество поиска (топ-5)", RED)

# Metrics table
add_text(slide, Inches(0.8), Inches(3.1), Inches(5), Inches(0.4),
         "Метрики качества поиска", font_size=18, color=DARK, bold=True)

metrics = [
    ("MRR", "Позиция первого релевантного", "> 0.5"),
    ("Precision@10", "Доля полезных в топ-10", "> 40%"),
    ("CTR", "Клики / поисковые запросы", "> 30%"),
    ("Session Success", "Сессий с кликом", "> 50%"),
    ("Bounce Rate", "Быстрый возврат с карточки", "< 30%"),
    ("Personalization Lift", "Улучшение CTR при персонализации", "> 10%"),
]

for i, (name, desc, target) in enumerate(metrics):
    y = Inches(3.6 + i * 0.5)
    bg_c = BG_GRAY if i % 2 == 0 else WHITE
    add_rect(slide, Inches(0.8), y, Inches(11.5), Inches(0.45), bg_c)
    add_text(slide, Inches(1.0), y + Inches(0.05), Inches(2.5), Inches(0.35),
             name, font_size=12, color=DARK, bold=True)
    add_text(slide, Inches(3.5), y + Inches(0.05), Inches(6.0), Inches(0.35),
             desc, font_size=12, color=GRAY)
    add_text(slide, Inches(10.0), y + Inches(0.05), Inches(2.0), Inches(0.35),
             target, font_size=12, color=ACCENT_GREEN, bold=True, alignment=PP_ALIGN.RIGHT)

# ================================================================
# SLIDE 7: Architecture
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 6, "АРХИТЕКТУРА СИСТЕМЫ")

# Service boxes
services = [
    ("React SPA\nNginx", Inches(1.0), Inches(1.5), BLUE, "Frontend\nUI, карточки, корзина"),
    ("FastAPI\nPython 3.12", Inches(4.5), Inches(1.5), RED, "Backend\nAPI, персонализация"),
    ("Elasticsearch\n8.17", Inches(1.0), Inches(3.8), ACCENT_GREEN, "537K docs\nBM25, fuzzy, synonyms"),
    ("Redis 7", Inches(4.5), Inches(3.8), RGBColor(0xDC, 0x38, 0x2D), "Profiles, cache\nevents, cart"),
    ("PostgreSQL\n16", Inches(8.0), Inches(3.8), BLUE, "2M contracts\nmetrics, sessions"),
    ("Ollama\nQwen 2.5 7B", Inches(8.0), Inches(1.5), RGBColor(0x7B, 0x1F, 0xA2), "AI expansion\nRAG-поиск"),
]

for title, left, top, color, desc in services:
    card = add_rounded_rect(slide, left, top, Inches(2.8), Inches(1.6), WHITE, color)
    # Color bar on left
    add_rect(slide, left + Inches(0.02), top + Inches(0.1), Inches(0.08), Inches(1.4), color)

    add_text(slide, left + Inches(0.3), top + Inches(0.15), Inches(2.3), Inches(0.6),
             title, font_size=13, color=DARK, bold=True)
    add_text(slide, left + Inches(0.3), top + Inches(0.8), Inches(2.3), Inches(0.6),
             desc, font_size=10, color=GRAY)

# Caddy + SonarQube
add_text(slide, Inches(1.0), Inches(5.8), Inches(11), Inches(0.4),
         "Caddy (HTTPS, reverse proxy)  |  SonarQube (Quality Gate: OK)  |  Docker Compose  |  32 CPU, 125GB RAM",
         font_size=13, color=GRAY, alignment=PP_ALIGN.CENTER)

# Arrows between services
bpmn_arrow(slide, Inches(3.8), Inches(2.3), Inches(4.5), Inches(2.3))
bpmn_arrow(slide, Inches(5.9), Inches(3.1), Inches(5.9), Inches(3.8))
bpmn_arrow(slide, Inches(2.4), Inches(3.1), Inches(2.4), Inches(3.8))
bpmn_arrow(slide, Inches(7.3), Inches(2.3), Inches(8.0), Inches(2.3))
bpmn_arrow(slide, Inches(7.3), Inches(4.6), Inches(8.0), Inches(4.6))

# ================================================================
# SLIDE 8: Innovation highlights
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 7, "КЛЮЧЕВЫЕ ИННОВАЦИИ")

innovations = [
    ("Subject Extraction", "Морфоанализ pymorphy3 выделяет ПРЕДМЕТ товара из названия. «Ручка» ≠ «тачка с ручкой». Падежи, сокращения, предлоги — всё учтено.", RED),
    ("Двухрежимный поиск", "Short (≤6 символов): prefix по subject.raw. Full: 4 параллельных стратегии (fuzzy + phrase×2 + AND). Оптимальная обработка каждого типа запроса.", BLUE),
    ("Cold Start", "4 190 организаций получают персонализацию с первого визита. 2M контрактов → предагрегированные buyer_category_weights → Redis за O(1).", ACCENT_GREEN),
    ("RAG через Ollama", "LLM (Qwen 2.5 7B) + реальные категории из ES индекса. «Медицинские перчатки» → нитриловые, хирургические, латексные. Не галлюцинирует.", RGBColor(0x7B, 0x1F, 0xA2)),
    ("Bounce Rate Tracking", "Открытие карточки < 3 сек → негативный сигнал quick_return. 5 типов событий с весами (view 2.0, click 3.0, cart 5.0). Temporal decay 0.95/день.", RGBColor(0xF5, 0x70, 0x0C)),
]

for i, (title, desc, color) in enumerate(innovations):
    top = Inches(1.2 + i * 1.15)
    # Number badge
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top + Inches(0.05), Inches(0.45), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.paragraphs[0].text = str(i + 1)
    tf.paragraphs[0].font.size = Pt(14)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    add_text(slide, Inches(1.5), top, Inches(2.5), Inches(0.35),
             title, font_size=15, color=DARK, bold=True)
    add_text(slide, Inches(4.2), top, Inches(8.5), Inches(0.9),
             desc, font_size=12, color=GRAY)

# ================================================================
# SLIDE 9: Thank you / CTA
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, DARK)
add_rect(slide, 0, 0, W, Inches(0.12), RED)

add_text(slide, Inches(1.5), Inches(1.5), Inches(10), Inches(0.8),
         "СПАСИБО", font_size=48, color=WHITE, bold=True)

add_rect(slide, Inches(1.5), Inches(2.6), Inches(3), Inches(0.04), RED)

# Links
links = [
    ("Демо:", "tenderhack.extra.moscow"),
    ("SonarQube:", "tenderhack.extra.moscow/sonar/"),
    ("GitHub:", "github.com/Shadowru/tenderhack2026"),
]

for i, (label, url) in enumerate(links):
    y = Inches(3.2 + i * 0.55)
    add_text(slide, Inches(1.5), y, Inches(2), Inches(0.4),
             label, font_size=16, color=LIGHT_GRAY)
    add_text(slide, Inches(3.5), y, Inches(8), Inches(0.4),
             url, font_size=16, color=BLUE, bold=True)

# Stats row at bottom
bottom_stats = [
    ("537K товаров", Inches(1.5)),
    ("2M контрактов", Inches(4.0)),
    ("4190 профилей", Inches(6.5)),
    ("93% качество", Inches(9.0)),
    ("30мс ответ", Inches(11.0)),
]

for text, left in bottom_stats:
    add_text(slide, left, Inches(5.5), Inches(2.5), Inches(0.4),
             text, font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

add_text(slide, Inches(1.5), Inches(6.3), Inches(10), Inches(0.4),
         "TenderHack 2026", font_size=14, color=LIGHT_GRAY)

# Save
output = "/home/zenith/tenderhack/docs/TenderHack2026_Presentation.pptx"
prs.save(output)
print(f"Created {output}")
