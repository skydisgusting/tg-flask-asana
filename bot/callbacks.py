from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv, find_dotenv

import threading

load_dotenv(find_dotenv())
router = Router()


class CreateWebhookThread(threading.Thread):
    def __init__(self, project):
        super().__init__()

        self.project = project

    def run(self):
        # ПРИ ВЫЗОВЕ ПОТОКА ВЫПОЛНЯЕТСЯ
        pass


@router.callback_query()
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.from_user.id)

    if call.data == "wait_for_token":
        await call.answer()

        token = None


    # if call.data == "profile":
    #     await call.answer()
    #
    #     user_id = data['user_id']
    #     username = data['username']
    #     first_name = data['first_name']
    #     second_name = data['second_name']
    #     role = data['role']
    #
    #     await call.message.edit_text(f'Ваш профиль:'
    #                                  f'\n\nID: {user_id}'
    #                                  f'\nЮзернейм: {username}'
    #                                  f'\nИмя: {first_name}'
    #                                  f'\nФамилия: {second_name}'
    #                                  f'\nРоль: {role}',
    #                                  reply_markup=kb.go_back_menu)
