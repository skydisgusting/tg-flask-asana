from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from typing import Optional

storage = MemoryStorage()


class AsanaAuth(StatesGroup):
    token = State()
