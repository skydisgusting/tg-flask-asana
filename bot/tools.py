from sqlalchemy import select, update
import requests
import secrets
import json
from db import User


async def get_asana_auth(user_id, session_maker):
    async with session_maker() as session:
        async with session.begin():
            row = await session.execute(select(User.asana_auth).where(User.user_id == user_id))

            row = row.one_or_none()
            print("row", row)

            if row[0] is None:
                return False
            else:
                return True


async def insert_new_token(user_id, token, session_maker):
    async with session_maker() as session:
        async with session.begin():
            if await session.execute(update(User).where(User.user_id == user_id).values(asana_auth=token)):
                await session.merge(User)
                return True
            else:
                return False


async def get_auth_url(user_id):
    oauth2_state = secrets.token_urlsafe(16)

    headers = {'Content-Type': 'application/json'}
    data = {
        "oauth2_state": oauth2_state,
        "user_id": user_id
    }

    response = requests.get(
        'https://71f2-5-16-97-185.ngrok-free.app/authorize/asana',
        headers=headers,
        data=json.dumps(data)
    )

    return response.text
