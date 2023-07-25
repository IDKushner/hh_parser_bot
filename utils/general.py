from aiogram import types
import functools
import re
from typing import Union

from db import User, Vacancy, get_user_by_id
from SETTINGS import SUPERUSER_TELEGRAM_IDS as STID


def strong(text: str):
    return f"<strong>{text}</strong>"


def get_message_text(vacancy: Vacancy, show_desc: bool = False) -> str:
    text: list[str] = [
        f"{strong(vacancy.name)} | {vacancy.employer_name}",
        f'{strong("Отрасли")}: {", ".join([tag for tag in vacancy.tags])}',
    ]

    if vacancy.salary:
        fr: int = vacancy.salary.get("from")
        to: int = vacancy.salary.get("to")
        if fr and not to:
            text.append(f"💵 От {fr}")
        elif not fr and to:
            text.append(f"💵 До {to}")
        elif fr and to:
            text.append(f"💵 {fr} - {to}")

    if show_desc:
        if len(vacancy.description) <= 3900:
            text.append(f"{vacancy.description}")
        else:
            text.append(f"{vacancy.description[:3901]} ...")

    text.append(f"\nID: {vacancy.hh_id}")

    if vacancy.from_admin:
        text = ["👑 Вакансия не из HH 👑\n"] + text

    return "\n".join(text)


def edit_description(description: Union[str, None]) -> str:
    if description == None:
        return None

    description = re.sub(
        pattern=r"(?P<w1>Требования|Условия)", repl=r"\n\n\g<w1>", string=description
    )
    description = re.sub(pattern=r"<li>", repl="\n   • ", string=description)
    description = re.sub(
        pattern=r"<p>|<br\s{0,1}/{0,1}>", repl="\n", string=description
    )
    description = re.sub(
        pattern=r"</{0,1}ul{0,1}>|</{0,1}ol{0,1}>|</li>|</\s{0,1}br>|</p>|&quot;",
        repl="",
        string=description,
    )

    return description


def prefetch_data(
    data: dict, element_name: str, element_value: Union[int, str, bool]
) -> dict:
    if not data.get(element_name):
        data[element_name]: list = [element_value]
    else:
        if element_value not in data[element_name]:
            data[element_name].append(element_value)
        else:
            data[element_name].remove(element_value)

    return data


def admin_only(superadmin: bool = False):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(message: types.Message):
            if superadmin and message.from_user.id in STID:
                await func(message)

            elif not superadmin:
                user: User = await get_user_by_id(message.from_user.id)
                if user.is_admin == True:
                    await func(message)

        return wrapper

    return decorator
