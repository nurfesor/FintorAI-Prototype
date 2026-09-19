# file: keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

def get_main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Ввести операцию", callback_data="manual_entry_start")
    kb.button(text="💡 Получить совет", callback_data="get_advice")
    kb.button(text="📊 Отчет", callback_data="get_report")
    kb.button(text="📜 История", callback_data="get_history")
    kb.adjust(2)
    return kb.as_markup()

def get_categories_keyboard(categories: List[str]):
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat, callback_data=f"fsm_cat_{cat}")
    kb.adjust(2)
    return kb.as_markup()

def get_groups_keyboard(groups: List[str]):
    kb = InlineKeyboardBuilder()
    for grp in groups:
        kb.button(text=grp, callback_data=f"fsm_grp_{grp}")
    kb.adjust(2)
    return kb.as_markup()

def get_subcategories_keyboard(subcats: List[str]):
    kb = InlineKeyboardBuilder()
    for sub in subcats:
        kb.button(text=sub, callback_data=f"fsm_sub_{sub}")
    kb.adjust(2)
    return kb.as_markup()

# ---