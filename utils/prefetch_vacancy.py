from db import Vacancy, get_vacancy_by_id, get_employers_types
from utils.regex import parse_tags
import re


class VacancyWithValidation:
    """
    - Это dataclass для хранения данных сырой вакансии перед передачей их в БД через Vacancy.add,
    он нужен для валидации ряда полей и более удобного хранения.
    - В классе Vacancy валидации нет, т.к. он нужен для вакансий с hh.ru, которые всегда правильно отформатированы,
    а валидация нужна для случаев, когда данные вакансии получены откуда-то кроме самого hh.ru.
    - Это не обычный dataclass, и даже не обычный класс с методом __init__ т.к. и то, и другое
    плохо работает работает с асинхронными функциями, которые приходится вызывать при валидации полей
    """

    name: str
    hh_id: int
    employer_name: str
    employer_type_id: int
    experience_id: int
    salary: dict or None
    description: str
    tags: list

    @classmethod
    async def add(
        cls,
        hh_id: str,
        name: str,
        employer_name: str,
        employer_type_id: str,
        experience_id: str,
        salary: str,
        description: str,
        from_admin: bool,
    ):
        """Валидирует поля вакансии типа VacancyWithValidation -> преобразуется в Vacancy ->
        -> загружается в БД через Vacancy.add()"""

        self = VacancyWithValidation()

        hh_id: int = await self.validate_hh_id(hh_id)
        employer_type_id: int = await self.validate_employer_type(employer_type_id)
        experience_id: int = self.validate_experience_type(experience_id)
        salary: dict or None = self.validate_salary(salary)

        name: str = name
        employer_name: str = employer_name
        description: str = description
        tags: list = parse_tags(description=description)
        self.validate_tags(tags)
        from_admin: bool = from_admin

        validated_vacancy = Vacancy(
            hh_id=hh_id,
            name=name,
            employer_name=employer_name,
            employer_type_id=employer_type_id,
            experience_id=experience_id,
            salary=salary,
            description=description,
            tags=tags,
            from_admin=from_admin,
        )

        await validated_vacancy.add()
        return validated_vacancy

    @staticmethod
    async def validate_hh_id(hh_id: str) -> int:
        if len(hh_id.split()) > 1 or not hh_id.isdigit():
            raise ValueError(
                "❌ Первой строкой должно идти id вакансии одним числом и ничего больше"
            )

        elif len(hh_id) > 10:
            raise ValueError("❌ Слишком длинный id вакансии")

        elif await get_vacancy_by_id(int(hh_id)):
            raise ValueError(
                "❌ Этот hh_id занят. Выберите другой (лучше короче 8 символов)"
            )

        else:
            return int(hh_id)

    @staticmethod
    async def validate_employer_type(employer_type: str) -> int:
        try:
            employer_type = int(employer_type)
            employers_types = await get_employers_types()
            return employers_types[employer_type]

        except:
            if type(employer_type) == str:
                employers_types = await get_employers_types(reverse=True)
                return employers_types[employer_type.capitalize()]

            else:
                raise ValueError(
                    '❌ Неправильный тип работодателя: нужно "Консалтинг" или "Инхаус"'
                )

    @staticmethod
    def validate_experience_type(experience: str) -> int:
        if experience.strip() == "0":
            return 1

        elif re.search(r"1\s*[-|—]\s*3", experience, re.I | re.M | re.S):
            return 2

        else:
            raise ValueError('❌ Неправильно указан опыт работы: нужно "0" или "1-3"')

    @staticmethod
    def validate_salary(salary: str) -> dict or None:
        if re.search(r"\d+\s*[-|—]\s*\d+", salary, re.I | re.M | re.S):
            salary: list = re.split(r"[-|—]", salary.strip(), re.I | re.M | re.S)
            return {"from": int(salary[0]), "to": int(salary[1])}

        elif re.findall(r"[От|от]\s*\d+", salary, re.I | re.M | re.S):
            return {"from": int(re.split(r"[От|от]\s*", int(salary.strip())[-1]))}

        elif re.search(r"[До|до]\s*\d+", salary, re.I | re.M | re.S):
            return {"to": int(re.split(r"[До|до]\s*", int(salary.strip())[-1]))}

        elif re.search(
            r"((Нет|Без)\s*[Зз](п|арплаты))|[Нн]ет\s*данных|[Нн]еизвестно",
            salary,
            re.I | re.M | re.S,
        ):
            return None

        else:
            raise ValueError(
                '❌ Неправильно указана зарплата: нужно в формате "От 100" или "До 100" или "100-200"'
            )

    @staticmethod
    def validate_tags(tags: list):
        if not tags:
            raise ValueError(
                "❌ Пожалуйста, перепишите описание вакансии: я не могу найти отсылки ни к одной отрасли права"
            )


async def prefetch_vacancy(
    vacancy_text: str, from_admin: bool = False
) -> VacancyWithValidation:
    """Делит текст вакансии на 7 значений: hh_id, name, employer_name, employer_type,
    experience, salary и description (!) именно в таком порядке (!)"""
    vacancy_text = re.sub(r"\s*/vacancy\s*\n", r"", vacancy_text)
    vacancy_text_split: list = re.split(r"\s*\n\s*", vacancy_text, maxsplit=7)

    validated_vacancy = await VacancyWithValidation.add(
        hh_id=vacancy_text_split[0],
        name=vacancy_text_split[1],
        employer_name=vacancy_text_split[2],
        employer_type_id=vacancy_text_split[3],
        experience_id=vacancy_text_split[4],
        salary=vacancy_text_split[5],
        description=vacancy_text_split[6],
        from_admin=from_admin,
    )

    return validated_vacancy
