from aiogram import Router, types
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import async_sessionmaker
from dotenv import load_dotenv, find_dotenv
import keyboards as kb
import tools
from middlewares.register_check import RegisterCheck
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

load_dotenv(find_dotenv())
router = Router()
router.message.middleware(RegisterCheck())


@router.message(Command("start"))
async def cmd_start(message: types.Message, session_maker: async_sessionmaker):
    user_id = message.from_user.id
    get_asana_auth = await tools.get_asana_auth(user_id=user_id, session_maker=session_maker)

    if get_asana_auth is True:
        await message.answer("Привет 👋🏻\n\n Выбери опцию:",
                             reply_markup=kb.main_menu())
    else:
        await message.answer("Подключите свой Asana аккаунт!",
                             reply_markup=await kb.asana_auth(user_id=user_id))
