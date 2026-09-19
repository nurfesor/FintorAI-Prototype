import asyncio
import logging
import re
from datetime import date

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from database import init_db, add_transaction_db, get_last_transactions_db
from keyboards.inline import (
    get_categories_keyboard,
    get_groups_keyboard,
    get_main_keyboard,
    get_subcategories_keyboard,
)
from middlewares.error_handler import ErrorHandlerMiddleware
from services.google_sheets import SheetsService
from services.openai_client import OpenAIService, Transaction
from states import TransactionFSM

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
dp = Dispatcher()
dp.update.outer_middleware(ErrorHandlerMiddleware())

# --- Service Initialization ---
sheets = SheetsService(str(config.google_credentials_json), config.spreadsheet_id)
openai = OpenAIService(config.openai_api_key.get_secret_value())

# --- Constants ---
NETWORK_TIMEOUT = 25.0
HELP_TEXT = (
    "Привет! Я Fintor AI, ваш финансовый ментор.\n\n"
    "✍️ <b>Добавление операции:</b>\n"
    "Просто напишите: <code>кофе 350</code> или <code>зарплата 50000</code>.\n\n"
    "💡 <b>Финансовый совет:</b>\n"
    "Используйте команду <code>/ask ваш вопрос</code>.\n\n"
    "📊 <b>Отчет:</b>\n"
    "Нажмите кнопку «Отчет» или введите /report.\n\n"
    "📜 <b>История:</b>\n"
    "Команда /history покажет последние 5 операций."
)

# --- UTILITY FUNCTIONS ---
async def process_new_transaction(trans: Transaction, message: types.Message):
    if not message.from_user: return
    
    add_transaction_db(user_id=message.from_user.id, trans_data=trans.model_dump())
    
    sheet_row = [
        trans.transaction_date.isoformat(), trans.category, trans.group,
        trans.subcategory, trans.amount, trans.description or "",
    ]
    await sheets.append_operation(sheet_row)
    
    await message.answer(
        "✅ <b>Операция добавлена:</b>\n"
        f" • Категория: {trans.category}\n"
        f" • Группа: {trans.group}\n"
        f" • Подкатегория: {trans.subcategory}\n"
        f" • Сумма: {trans.amount:.2f}"
    )

def robust_regex_parser(text: str) -> Transaction | None:
    pattern = re.compile(r"^\s*(?P<desc>.+?)\s+(?P<amt>[\d]+(?:[.,][\d]{1,2})?)\s*$", re.UNICODE)
    match = pattern.match(text)
    if not match: return None
    
    data = match.groupdict()
    try:
        amount = float(data['amt'].replace(",", "."))
    except (ValueError, TypeError):
        return None
        
    return Transaction(
        category="Быстрая запись",
        group="Regex",
        subcategory=data['desc'].strip().capitalize(),
        amount=amount,
    )

# --- COMMAND HANDLERS ---
@dp.message(Command("start", "help"))
async def cmd_start_help(msg: types.Message):
    await msg.answer(HELP_TEXT, reply_markup=get_main_keyboard())

@dp.message(Command("report"))
async def cmd_report(msg: types.Message):
    url = await sheets.get_report_sheet_url()
    await msg.answer(f"📊 Ваш финансовый отчет:\n{url}")

@dp.message(Command("history"))
async def cmd_history(msg: types.Message):
    if not msg.from_user: return
    
    transactions = get_last_transactions_db(user_id=msg.from_user.id, limit=5)
    if not transactions:
        return await msg.answer("📜 Ваша история операций пока пуста.")
    
    response_lines = ["📜 <b>Последние 5 операций:</b>\n"]
    for tx in transactions:
        date_str = tx.transaction_date.strftime('%d.%m.%Y')
        response_lines.append(f" • <code>{date_str}</code>: {tx.subcategory} - <b>{tx.amount:.2f} ₽</b>")
    await msg.answer("\n".join(response_lines))

@dp.message(Command("ask"))
async def cmd_ask(msg: types.Message, command: CommandObject):
    if not command.args: return await msg.answer("Пожалуйста, задайте вопрос после /ask")
    
    thinking_msg = await msg.answer("⌛ Думаю…")
    try:
        advice = await asyncio.wait_for(openai.get_financial_advice(command.args), timeout=NETWORK_TIMEOUT)
        await thinking_msg.edit_text(advice)
    except asyncio.TimeoutError:
        await thinking_msg.edit_text("😕 Сервер не отвечает, попробуйте позже.")

# --- MAIN TRANSACTION PARSING LOGIC ---
@dp.message(F.text, ~F.text.startswith('/'))
async def process_transaction_text(msg: types.Message):
    if not (msg.text and msg.from_user): return

    if transaction := robust_regex_parser(msg.text):
        return await process_new_transaction(transaction, msg)

    processing_msg = await msg.answer("Распознаю сложный запрос… 🤖")
    try:
        ref_text = await asyncio.wait_for(sheets.get_reference_text(), timeout=NETWORK_TIMEOUT)
        gpt_transaction = await asyncio.wait_for(openai.parse_transaction(msg.text, ref_text), timeout=NETWORK_TIMEOUT)
        
        await processing_msg.delete()
        if gpt_transaction:
            await process_new_transaction(gpt_transaction, msg)
        else:
            kb = InlineKeyboardBuilder().button(text="✍️ Ввести вручную", callback_data="manual_entry_start")
            await msg.answer("Не удалось распознать. Хотите ввести по шагам?", reply_markup=kb.as_markup())
    except asyncio.TimeoutError:
        await processing_msg.edit_text("😕 Сервер не отвечает, попробуйте позже.")

# --- FSM FOR MANUAL ENTRY ---
@dp.callback_query(F.data == "manual_entry_start")
async def fsm_start(cb: types.CallbackQuery, state: FSMContext):
    if not cb.message: return await cb.answer()
    
    await state.clear()
    refs = await sheets.get_reference_data()
    await state.update_data(reference_data=refs)
    
    cats = sorted({r[0] for r in refs if r})
    await cb.message.edit_text("<b>Шаг 1/5:</b> Выберите категорию", reply_markup=get_categories_keyboard(cats))
    await state.set_state(TransactionFSM.choosing_category)
    await cb.answer()

@dp.callback_query(TransactionFSM.choosing_category, F.data.startswith("fsm_cat_"))
async def fsm_cat(cb: types.CallbackQuery, state: FSMContext):
    if not (cb.data and cb.message): return await cb.answer()

    category = cb.data.removeprefix("fsm_cat_")
    await state.update_data(category=category)
    
    fsm_data = await state.get_data()
    refs = fsm_data.get("reference_data", [])
    
    groups = sorted({r[1] for r in refs if len(r) > 1 and r[0] == category})
    await cb.message.edit_text(f"✅ Категория: <b>{category}</b>\n<b>Шаг 2/5:</b> Выберите группу", reply_markup=get_groups_keyboard(groups))
    await state.set_state(TransactionFSM.choosing_group)
    await cb.answer()

@dp.callback_query(TransactionFSM.choosing_group, F.data.startswith("fsm_grp_"))
async def fsm_grp(cb: types.CallbackQuery, state: FSMContext):
    if not (cb.data and cb.message): return await cb.answer()

    group = cb.data.removeprefix("fsm_grp_")
    await state.update_data(group=group)
    
    fsm_data = await state.get_data()
    refs = fsm_data.get("reference_data", [])
    category = fsm_data.get("category")
    
    subcats = sorted({r[2] for r in refs if len(r) > 2 and r[0] == category and r[1] == group})
    await cb.message.edit_text(f"✅ Группа: <b>{group}</b>\n<b>Шаг 3/5:</b> Выберите подкатегорию", reply_markup=get_subcategories_keyboard(subcats))
    await state.set_state(TransactionFSM.choosing_subcategory)
    await cb.answer()

@dp.callback_query(TransactionFSM.choosing_subcategory, F.data.startswith("fsm_sub_"))
async def fsm_sub(cb: types.CallbackQuery, state: FSMContext):
    if not (cb.data and cb.message): return await cb.answer()

    subcategory = cb.data.removeprefix("fsm_sub_")
    await state.update_data(subcategory=subcategory)
    
    fsm_data = await state.get_data()
    await cb.message.edit_text(f"✅ Подкатегория: <b>{subcategory}</b>\n<b>Шаг 4/5:</b> Введите сумму")
    await state.set_state(TransactionFSM.entering_amount)
    await cb.answer()

@dp.message(TransactionFSM.entering_amount, F.text)
async def fsm_amount(msg: types.Message, state: FSMContext):
    if not msg.text: return
    try:
        amount = float(msg.text.replace(",", "."))
    except (ValueError, TypeError):
        return await msg.answer("Сумма должна быть числом. Попробуйте ещё раз.")
    
    await state.update_data(amount=amount)
    await msg.answer("<b>Шаг 5/5:</b> Введите краткое описание (или `-`)")
    await state.set_state(TransactionFSM.entering_description)

@dp.message(TransactionFSM.entering_description, F.text)
async def fsm_desc(msg: types.Message, state: FSMContext):
    if not (msg.text and msg.from_user): return
    
    description = "" if msg.text.strip() == "-" else msg.text
    data = await state.get_data()
    await state.clear()

    trans = Transaction(
        category=data.get("category", "N/A"), group=data.get("group", "N/A"),
        subcategory=data.get("subcategory", "N/A"), amount=data.get("amount", 0.0),
        description=description,
    )
    await process_new_transaction(trans, msg)

# --- BOT STARTUP ---
async def on_startup(bot: Bot):
    logging.info("Bot starting...")
    init_db()
    logging.info("Database initialized.")
    await sheets.load_reference_data()
    logging.info("Reference data cache warmed up.")

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
