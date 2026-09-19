# file: states.py
from aiogram.fsm.state import State, StatesGroup

class TransactionFSM(StatesGroup):
    choosing_category = State()
    choosing_group = State()
    choosing_subcategory = State()
    entering_amount = State()
    entering_description = State()

# ---