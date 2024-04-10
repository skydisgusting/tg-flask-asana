from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
import tools


def main_menu() -> InlineKeyboardMarkup:
    start_menu = InlineKeyboardBuilder()
    start_menu.button(text="Тест проектов", callback_data="get_projects")
    start_menu.adjust(3, 2)
    return start_menu.as_markup()


async def asana_auth(user_id) -> InlineKeyboardMarkup:
    auth_menu = InlineKeyboardBuilder()
    url = await tools.get_auth_url(user_id=user_id)
    auth_menu.button(text="Авторизоваться", url=url, callback_data="wait_for_token")
    auth_menu.adjust(3, 2)

    return auth_menu.as_markup()
