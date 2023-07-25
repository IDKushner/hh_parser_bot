import aiohttp
import asyncio
import re

from db import Vacancy, get_employers_types
from utils.regex import EMPLOYER_TYPE_REGEX, parse_tags
from utils.general import edit_description

BASE_URL = "https://api.hh.ru"


params = {
    "text": "Юрист",
    "search_field": ["name", "description"],
    "experience": ["noExperience", "between1And3"],
    "employment": ["full", "part", "probation"],
    "area": "1",  # Только Москва (для примера)
    "professional_role": "146",  # 146 = Юрист; есть ещё 145 = Юрисконсульт, но передать можно только одну
    "label": "not_from_agency",
    "per_page": "100",
    "period": "1",  # Подборка за 1 день (за сутки)
    "order_by": "salary_desc",  # по убыванию дохода
}


# async def dictionaries():
#     async with aiohttp.ClientSession(BASE_URL) as session:
#         async with session.get('/dictionaries') as resp:
#             t = await resp.json()
#             print(t['vacancy_label'])


# async def areas():
#     async with aiohttp.ClientSession(BASE_URL) as session:
#         async with session.get('/areas/1') as resp:
#             t = await resp.json()
#             print(t)


# async def other():
#     async with aiohttp.ClientSession(BASE_URL) as session:
#         async with session.get('/professional_roles') as resp:
#             t = await resp.json()
#             # for item in t['categories']:
#             #     print(item['name'])
#             print(t['categories'][-2])


def shorten_vacancy(vacancy: dict) -> dict:
    short_vacancy = {
        "hh_id": int(vacancy["id"]),
        "name": vacancy["name"],
        "alternate_url": vacancy["alternate_url"],
        "employer": {
            "id": vacancy["employer"]["id"],
            "name": vacancy["employer"]["name"],
            "url": vacancy["employer"]["url"],
            "alternate_url": vacancy["employer"]["alternate_url"],
        },
        "experience": vacancy["experience"]["id"],
    }

    salary = vacancy.get("salary")
    if salary:
        short_vacancy["salary"] = {
            "from": vacancy["salary"].get("from"),
            "to": vacancy["salary"].get("to"),
        }
    else:
        short_vacancy["salary"] = None

    address = vacancy.get("address")
    if address:
        short_vacancy[
            "address"
        ] = f"г. {vacancy['address']['city']}, ул. {vacancy['address']['street']}, д. {vacancy['address']['building']}"

        metro_stations = vacancy["address"].get("metro_stations")
        if metro_stations:
            short_vacancy["metro_stations"] = [
                station["station_name"]
                for station in vacancy["address"]["metro_stations"]
            ]
        else:
            short_vacancy["metro_stations"] = None

    else:
        short_vacancy["address"] = None

    return short_vacancy


async def add_description(session: aiohttp.ClientSession, short_vacancy: dict) -> dict:
    async with session.get(f'/vacancies/{short_vacancy["hh_id"]}') as resp:
        resp = await resp.json()
        short_vacancy["description"] = edit_description(resp.get("description"))

        return short_vacancy


async def add_employer_type(
    session: aiohttp.ClientSession, short_vacancy: dict, employers_types_as_dict: dict
) -> dict:
    async with session.get(f'/employers/{short_vacancy["employer"]["id"]}') as resp:
        resp = await resp.json()
        employer_description = resp.get("description")

        if employer_description:
            # employers_types_as_dict = await get_employers_types(reverse=True)

            if re.search(EMPLOYER_TYPE_REGEX, employer_description, re.I | re.M | re.S):
                short_vacancy["employer_type_id"] = employers_types_as_dict[
                    "Консалтинг"
                ]
            else:
                short_vacancy["employer_type_id"] = employers_types_as_dict["Инхаус"]
        else:
            # если описания работодателя (description по адресу, который мы запрашиваем) нет в принципе,
            # то он считается инхаусом т.к. консалтинг в 99% случаев более организованный и заполняет описание о себе
            # сделал так, чтобы не просить юзеров при регистрации выбирать, показывать ли им
            # вакансии без описания работодателя
            short_vacancy["employer_type_id"] = employers_types_as_dict["Инхаус"]

        return short_vacancy


async def add_tags(session: aiohttp.ClientSession, short_vacancy: dict) -> dict:
    async with session.get(f'/vacancies/{short_vacancy["hh_id"]}') as resp:
        resp = await resp.json()
        raw_key_skills = resp.get("key_skills")
        key_skills = [skill["name"] for skill in raw_key_skills if raw_key_skills]

    found_tags = []

    if raw_key_skills:
        found_tags.extend(key_skills)

    short_vacancy["tags"] = parse_tags(
        found_tags=found_tags, description=short_vacancy["description"]
    )

    return short_vacancy


async def parse_vacancies():
    async with aiohttp.ClientSession(BASE_URL) as session:
        async with session.get("/vacancies", params=params) as resp:
            resp = await resp.json()
            for vacancy in resp["items"]:
                short_vacancy = shorten_vacancy(vacancy)
                short_vacancy = await add_description(session, short_vacancy)

                # вакансии без описания не обрабатываются
                if not short_vacancy["description"]:
                    continue

                employers_types_as_dict = await get_employers_types(reverse=True)
                additions = [
                    add_tags(session, short_vacancy),
                    add_employer_type(session, short_vacancy, employers_types_as_dict),
                ]
                await asyncio.gather(*additions)

                # вакансии, на которые не удалось найти теги, не обрабатываются
                if not short_vacancy["tags"]:
                    continue

                new_vacancy = Vacancy(
                    hh_id=short_vacancy["hh_id"],
                    name=short_vacancy["name"],
                    url=short_vacancy.get("alternate_url"),
                    employer_name=short_vacancy["employer"]["name"],
                    employer_type_id=short_vacancy.get("employer_type_id"),
                    experience_id=1
                    if short_vacancy["experience"] == "noExperience"
                    else 2,  # поменять, если добавятся новые виды опыта
                    salary=short_vacancy.get("salary"),
                    address=short_vacancy.get("address"),
                    metro_stations=short_vacancy.get("metro_stations"),
                    description=short_vacancy["description"],
                    tags=short_vacancy["tags"],
                )

                await new_vacancy.add()
