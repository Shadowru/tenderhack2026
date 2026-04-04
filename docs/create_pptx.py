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
    """Add consistent header bar to slide — projector-friendly bold style."""
    add_rect(slide, 0, 0, W, Inches(0.12), RED)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(1), Inches(0.5),
             f"{number:02d}", font_size=18, color=RED, bold=True)
    add_text(slide, Inches(1.4), Inches(0.22), Inches(10), Inches(0.6),
             title, font_size=30, color=DARK, bold=True)
    # Thick line under header
    add_rect(slide, Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.04), RGBColor(0xE0, 0xE0, 0xE0))


def add_stat_card(slide, left, top, value, label, accent=RED):
    card = add_rounded_rect(slide, left, top, Inches(2.4), Inches(1.5), WHITE, RGBColor(0xD0, 0xD0, 0xD0))
    # Thick accent top bar
    add_rect(slide, left + Inches(0.02), top + Inches(0.02), Inches(2.36), Inches(0.1), accent)
    add_text(slide, left + Inches(0.3), top + Inches(0.3), Inches(1.8), Inches(0.6),
             value, font_size=36, color=DARK, bold=True, alignment=PP_ALIGN.CENTER)
    add_text(slide, left + Inches(0.2), top + Inches(0.95), Inches(2.0), Inches(0.4),
             label, font_size=13, color=GRAY, bold=True, alignment=PP_ALIGN.CENTER)


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

# Grid-based BPMN: 4 swimlanes, steps placed on explicit grid
# Lane tops and heights
L1_TOP = Inches(1.0)   # User
L2_TOP = Inches(2.5)   # Backend
L3_TOP = Inches(4.0)   # Elasticsearch
L4_TOP = Inches(5.5)   # Redis/PG
LANE_H = Inches(1.3)
STEP_H = Inches(0.6)
STEP_W = Inches(1.4)
GAP = Inches(0.15)  # gap between steps

# Column X positions (left edges)
C1 = Inches(1.8)   # col 1
C2 = Inches(3.5)   # col 2
C3 = Inches(5.2)   # col 3 (gateway)
C4 = Inches(6.4)   # col 4
C5 = Inches(8.1)   # col 5
C6 = Inches(9.8)   # col 6
C7 = Inches(11.5)  # col 7 (end)

# Lane label width
LBL_W = Inches(1.1)

# Draw swimlanes
lanes = [
    ("Пользователь", L1_TOP, RGBColor(0xE3, 0xF2, 0xFD)),
    ("Backend (FastAPI)", L2_TOP, RGBColor(0xFB, 0xE9, 0xE7)),
    ("Elasticsearch", L3_TOP, RGBColor(0xE8, 0xF5, 0xE9)),
    ("Redis / PostgreSQL", L4_TOP, RGBColor(0xFE, 0xF3, 0xE2)),
]
for name, top, bg in lanes:
    add_rect(slide, Inches(0.4), top, Inches(12.5), LANE_H, bg, RGBColor(0xD0, 0xD0, 0xD0))
    add_text(slide, Inches(0.45), top + Inches(0.02), LBL_W, Inches(0.25),
             name, font_size=8, color=DARK, bold=True)

# Step midpoints (vertical center of each lane)
def lane_mid(lane_top):
    return lane_top + (LANE_H - STEP_H) / 2

M1 = lane_mid(L1_TOP)
M2 = lane_mid(L2_TOP)
M3 = lane_mid(L3_TOP)
M4 = lane_mid(L4_TOP)

# Helper: step center X/Y for arrow endpoints
def cx(left):
    return left + STEP_W / 2

def right_edge(left):
    return left + STEP_W

def bot_edge(top):
    return top + STEP_H

# Helpers
def bpmn_step(s, left, top, text, fill=WHITE, w=STEP_W):
    shape = add_rounded_rect(s, left, top, w, STEP_H, fill, RGBColor(0xBB, 0xBB, 0xBB))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = text
    tf.paragraphs[0].font.size = Pt(8)
    tf.paragraphs[0].font.color.rgb = DARK
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return shape

def bpmn_event(s, left, top, color, thick=False):
    d = Inches(0.4)
    shape = s.shapes.add_shape(MSO_SHAPE.OVAL, left, top + (STEP_H - d) / 2, d, d)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if thick:
        shape.line.color.rgb = color
        shape.line.width = Pt(3)
    else:
        shape.line.fill.background()
    return shape

def bpmn_gw(s, left, top, text):
    d = Inches(0.55)
    shape = s.shapes.add_shape(MSO_SHAPE.DIAMOND, left, top + (STEP_H - d) / 2, d, d)
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

def arrow(s, x1, y1, x2, y2):
    c = s.shapes.add_connector(1, x1, y1, x2, y2)
    c.line.color.rgb = RGBColor(0x88, 0x88, 0x88)
    c.line.width = Pt(1.5)

# ---- Place steps ----

# Lane 1: User
start = bpmn_event(slide, C1, M1, ACCENT_GREEN)
s_input = bpmn_step(slide, C2, M1, "Ввод запроса\nв строку поиска")
end = bpmn_event(slide, C7, M1, RED, thick=True)

# Lane 2: Backend
s_norm  = bpmn_step(slide, C1, M2, "Нормализация\nEN→RU раскладка")
s_spell = bpmn_step(slide, C2, M2, "Spell check\n490K словарь")
gw      = bpmn_gw(slide, C3 + Inches(0.4), M2, "≤6?")
s_pfx   = bpmn_step(slide, C4, M2 - Inches(0.35), "Prefix поиск\nsubject.raw", w=STEP_W)
s_full  = bpmn_step(slide, C4, M2 + Inches(0.35), "Multi-match\n4 стратегии", w=STEP_W)
s_func  = bpmn_step(slide, C5, M2, "Function score\n+ бусты")
s_rag   = bpmn_step(slide, C6, M2, "RAG\nLLM (Ollama)")

# Lane 3: Elasticsearch
s_bm25  = bpmn_step(slide, C4, M3, "BM25 + fuzzy\nsynonyms")
s_agg   = bpmn_step(slide, C5, M3, "Aggregation\nкатегорий")
s_filt  = bpmn_step(slide, C6, M3, "Filtered\nsearch")

# Lane 4: Redis/PG
s_cold  = bpmn_step(slide, C1, M4, "Cold start\nPG → Redis")
s_prod  = bpmn_step(slide, C2, M4, "Product\nboosts")
s_cat   = bpmn_step(slide, C3, M4, "Category\nboosts")
s_track = bpmn_step(slide, C6, M4, "Track events\nlog + session")

# ---- Arrows (strictly grid-aligned) ----

# Lane 1 horizontal
arrow(slide, C1 + Inches(0.4), M1 + STEP_H/2, C2, M1 + STEP_H/2)                 # start → input
arrow(slide, right_edge(C6), M2 + STEP_H/2, C7, M1 + STEP_H/2)                    # rag → end (goes up)

# Lane 1 → Lane 2 vertical
arrow(slide, cx(C2), bot_edge(M1), cx(C2), M2)                                      # input → spell (down)
arrow(slide, cx(C1), bot_edge(M1), cx(C1), M2)                                      # also norm

# Lane 2 horizontal
arrow(slide, right_edge(C1), M2 + STEP_H/2, C2, M2 + STEP_H/2)                    # norm → spell
arrow(slide, right_edge(C2), M2 + STEP_H/2, C3 + Inches(0.4), M2 + STEP_H/2)     # spell → gateway
arrow(slide, C3 + Inches(0.95), M2 + STEP_H/2 - Inches(0.15), C4, M2 - Inches(0.35) + STEP_H/2)  # gw → prefix
arrow(slide, C3 + Inches(0.95), M2 + STEP_H/2 + Inches(0.15), C4, M2 + Inches(0.35) + STEP_H/2)  # gw → full
arrow(slide, right_edge(C4), M2 - Inches(0.35) + STEP_H/2, C5, M2 + STEP_H/2)    # prefix → func
arrow(slide, right_edge(C4), M2 + Inches(0.35) + STEP_H/2, C5, M2 + STEP_H/2)    # full → func
arrow(slide, right_edge(C5), M2 + STEP_H/2, C6, M2 + STEP_H/2)                    # func → rag

# Lane 2 → Lane 3 vertical
arrow(slide, cx(C4), bot_edge(M2 + Inches(0.35)), cx(C4), M3)                       # full → bm25
arrow(slide, cx(C5), bot_edge(M2), cx(C5), M3)                                       # func → agg
arrow(slide, cx(C6), bot_edge(M2), cx(C6), M3)                                       # rag → filtered

# Lane 3 horizontal
arrow(slide, right_edge(C4), M3 + STEP_H/2, C5, M3 + STEP_H/2)                    # bm25 → agg
arrow(slide, right_edge(C5), M3 + STEP_H/2, C6, M3 + STEP_H/2)                    # agg → filtered

# Lane 2 → Lane 4 vertical
arrow(slide, cx(C1), bot_edge(M2), cx(C1), M4)                                       # norm → cold start
arrow(slide, cx(C6), bot_edge(M2), cx(C6), M4)                                       # rag → track

# Lane 4 horizontal
arrow(slide, right_edge(C1), M4 + STEP_H/2, C2, M4 + STEP_H/2)                    # cold → prod
arrow(slide, right_edge(C2), M4 + STEP_H/2, C3, M4 + STEP_H/2)                    # prod → cat

# Labels for gateway branches
add_text(slide, C3 + Inches(0.55), M2 - Inches(0.55), Inches(0.5), Inches(0.2),
         "Да", font_size=7, color=ACCENT_GREEN, bold=True)
add_text(slide, C3 + Inches(0.55), M2 + Inches(0.7), Inches(0.5), Inches(0.2),
         "Нет", font_size=7, color=RED, bold=True)

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
arrow(slide, Inches(3.8), Inches(2.3), Inches(4.5), Inches(2.3))
arrow(slide, Inches(5.9), Inches(3.1), Inches(5.9), Inches(3.8))
arrow(slide, Inches(2.4), Inches(3.1), Inches(2.4), Inches(3.8))
arrow(slide, Inches(7.3), Inches(2.3), Inches(8.0), Inches(2.3))
arrow(slide, Inches(7.3), Inches(4.6), Inches(8.0), Inches(4.6))

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
# SLIDE 9: Ranking Signals — Positive & Negative
# ================================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
slide_header(slide, 8, "СИГНАЛЫ РАНЖИРОВАНИЯ")

# Two columns: positive (green) and negative (red)
add_text(slide, Inches(0.8), Inches(1.2), Inches(5.5), Inches(0.5),
         "ПОЗИТИВНЫЕ (повышают позицию)", font_size=20, color=ACCENT_GREEN, bold=True)
add_rect(slide, Inches(0.8), Inches(1.7), Inches(5.5), Inches(0.05), ACCENT_GREEN)

positives = [
    ("Совпадение с предметом товара", "Subject extraction: поиск «ручка» → товары где ручка = предмет", "x5"),
    ("Точная фраза в названии", "match_phrase slop:1 — «100 листов» выше «500 листов»", "x20"),
    ("История закупок организации", "Cold start из контрактов: школа → бланки, больница → офисная", "x1.05"),
    ("Добавлен в корзину / избранное", "Event cart (вес 5.0) → мгновенный product boost", "x2.0"),
    ("Просмотр карточки > 3 сек", "Event view (вес 2.0) — заинтересовался, не bounce", "x1.5"),
    ("Популярность (кол-во контрактов)", "log2p(popularity) — мягкий множитель", "x1-3"),
]

for i, (signal, desc, boost) in enumerate(positives):
    y = Inches(1.95 + i * 0.7)
    add_rect(slide, Inches(0.8), y, Inches(5.5), Inches(0.6), BG_GRAY if i % 2 == 0 else WHITE)
    add_text(slide, Inches(1.0), y + Inches(0.05), Inches(3.5), Inches(0.25),
             signal, font_size=13, color=DARK, bold=True)
    add_text(slide, Inches(1.0), y + Inches(0.3), Inches(4.0), Inches(0.25),
             desc, font_size=10, color=GRAY)
    add_text(slide, Inches(5.2), y + Inches(0.1), Inches(1.0), Inches(0.35),
             boost, font_size=14, color=ACCENT_GREEN, bold=True, alignment=PP_ALIGN.RIGHT)

# Negative column
add_text(slide, Inches(7.0), Inches(1.2), Inches(5.5), Inches(0.5),
         "НЕГАТИВНЫЕ (понижают / исключают)", font_size=20, color=RED, bold=True)
add_rect(slide, Inches(7.0), Inches(1.7), Inches(5.5), Inches(0.05), RED)

negatives = [
    ("Отрицание в запросе", "«не маслянных», «без латексных», «кроме» → must_not", "Исключ."),
    ("Bounce (< 3 сек на карточке)", "Event quick_return — закрыл карточку быстро", "-сигнал"),
    ("Слово — атрибут, не предмет", "«тачка с ручкой» → subject=тачка, ручка не предмет", "x0"),
    ("Temporal decay", "DECAY_FACTOR = 0.95 на каждый день давности события", "×0.95/д"),
    ("Историческая vs live-данные", "Контракты из PG дисконтируются ×0.7", "×0.7"),
]

for i, (signal, desc, effect) in enumerate(negatives):
    y = Inches(1.95 + i * 0.7)
    add_rect(slide, Inches(7.0), y, Inches(5.5), Inches(0.6), RGBColor(0xFE, 0xF0, 0xEF) if i % 2 == 0 else WHITE)
    add_text(slide, Inches(7.2), y + Inches(0.05), Inches(3.5), Inches(0.25),
             signal, font_size=13, color=DARK, bold=True)
    add_text(slide, Inches(7.2), y + Inches(0.3), Inches(4.0), Inches(0.25),
             desc, font_size=10, color=GRAY)
    add_text(slide, Inches(11.2), y + Inches(0.1), Inches(1.2), Inches(0.35),
             effect, font_size=14, color=RED, bold=True, alignment=PP_ALIGN.RIGHT)

# Bottom note
add_text(slide, Inches(0.8), Inches(6.4), Inches(12), Inches(0.4),
         "Формула: Score = BM25(strategies) x Popularity(log2p) x ProductBoost(1-2) x CategoryBoost(1-1.05) + SubjectExact(+15) + SubjectFuzzy(+12)",
         font_size=12, color=GRAY, bold=True, alignment=PP_ALIGN.CENTER)

# ================================================================
# SLIDE 10: Thank you / CTA
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
