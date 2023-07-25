import re

EMPLOYER_TYPE_REGEX = r"Консалт|Юридическ.{1,3}фирм|Юридическ.{1,3}компан|\
    |Юридич.{1,3}услуг|Адвокат"

CORPORATE_TAGS_RAW = [
    r"Корпоративн.{0,4}прав",
    r"Устав",
    r"Реорганизац",
    r"Ликвидац",
    r"Учредительн.{0,4}документ",
    r"Собран.{0,5}участник",
    r"Решен.{0,4}.единственн.{0,4}участник",
    r"Корпоративн.{0,4}процедур",
    r"[\s,]+СД[\s,]+",
    r"[\s,]+ОСУ[\s,]+",
    r"Инвестиц",
    r"Финансирован",
    r"Корпоративн.{0,4}договор",
    r"Заем",
    r"Займ",
    r"Кредит",
    r"Лизинг",
    r"[(Учрежден.{0,4})|(Регистрац.{0,4})]компан",
    r"Венчур",
    r"Совместн.{0,4}предприят",
    r"[\s,]+АО[\s,]+",
    r"Акци.{0,4}",
    r"ООО",
    r"Обществ.{0,6}ограниченн.{0,4}ответственност",
    r"Хозяйственн.{0,4}обществ",
    r"IPO",
    r"Преимущественн.{0,4}прав",
    r"Облигац",
]

CORPORATE_TAGS_REGEX = r"|".join(CORPORATE_TAGS_RAW)

IP_TAGS_RAW = [
    r"Интеллектуальн.{0,4}собственност",
    r"Авторск.{0,4}прав",
    r"Патент",
    r"Исключительн.{0,4}прав",
    r"Авторск.{0,5}заказ",
    r"Результат.{0,4}интеллектуальн.{0,4}деятельност",
    r"Лицензион",
    r"Служебн.{0,4}произведен",
    r"Программ.{0,4}для{0,1}ЭВМ",
]

IP_TAGS_REGEX = r"|".join(IP_TAGS_RAW)

DP_TAGS_RAW = [r"Персональн{0,4}данн"]

DP_TAGS_REGEX = r"|".join(DP_TAGS_RAW)

DR_TAGS_RAW = [
    r"[\s,]+Иск",
    r"Отзыв",
    r"Претензи",
    r"Доказательств",
    r"Ходатайств",
    r"Жалоб",
    r"Возражен",
    r"Процессуальн.{0,4}документ",
    r"[(Арбитражн.{0,4})|(Третейск.{0,4})]суд",
    r"Суд.{0,4}общ.{0,4}юрисдикц",
    r"Судебн.{0,4}приказ",
    r"Судебн.{0,4}разбирательств",
    r"Пристав",
    r"Делопроизводств",
    r"Разрешен{0,4}спор",
    r"[\s,]+Упрощ[её]н",
    r"[(Гражданск.{0,4})|(Арбитражн.{0,4})|(Административн.{0,4})]процесс",
    r"Банкротств",
    r"Кредитор",
    r"Арбитражн.{0,4}управляющ",
    r"Конкурсн.{0,4}производств",
    r"Субсидиарн.{0,4}ответственност",
    r"Наблюден",
    r"Санаци",
    r"Финансов.{0,4}оздоровлен",
    r"Плат[её]жеспособн",
    r"Внешн.{0,4}управлен",
    r"Апелляционн",
    r"Кассационн",
    r"Надзорн",
    r"Оспариван",
    r"Недействительн",
    r"Ничтожн",
    r"Реституци",
    r"Взыскани",
    r"Арест",
]

DR_TAGS_REGEX = r"|".join(DR_TAGS_RAW)

CIVIL_TAGS_RAW = [
    r"Оказан.{0,4}услуг",
    r"Поставк",
    r"Подряд",
    r"Купл.{0,4}продаж",
    r"Протокол.{0,4}разноглас",
    r"Расторжен.{0,4}договор",
    r"Изменен.{0,4}договор",
    r"Уступк",
    r"Дополнительн.{0,4}соглашен",
]

CIVIL_TAGS_REGEX = r"|".join(CIVIL_TAGS_RAW)

LABOUR_TAGS_REGEX = []  # добавить при необходимости

BANKING_TAGS_REGEX = []  # добавить при необходимости


def parse_tags(description: str, found_tags: list = []) -> list or None:
    pattern = r"|".join(
        [
            CORPORATE_TAGS_REGEX,
            IP_TAGS_REGEX,
            DP_TAGS_REGEX,
            DR_TAGS_REGEX,
            CIVIL_TAGS_REGEX,
        ]
    )

    found_tags.extend(
        re.findall(pattern=pattern, string=description, flags=re.I | re.M | re.S)
    )

    found_tags_as_str = " ".join(found_tags)

    parsed_tags = []

    if re.search(CORPORATE_TAGS_REGEX, found_tags_as_str, re.I | re.M | re.S):
        parsed_tags.append("Корпоративное право")

    if re.search(IP_TAGS_REGEX, found_tags_as_str, re.I | re.M | re.S):
        parsed_tags.append("Интеллектуальная собственность")

    if re.search(DP_TAGS_REGEX, found_tags_as_str, re.I | re.M | re.S):
        parsed_tags.append("Персональные данные")

    if re.search(DR_TAGS_REGEX, found_tags_as_str, re.I | re.M | re.S):
        parsed_tags.append("Разрешение споров")

    if re.search(CIVIL_TAGS_REGEX, found_tags_as_str, re.I | re.M | re.S):
        parsed_tags.append("Гражданское право")

    if not parsed_tags:
        return None
    else:
        return parsed_tags
