from db import Vacancy
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData


class KB:
    """При multiselect=True создаёт Inline-клавиатуру, поддерживающую множественный выбор:
    - одна кнопка = один вариант
    - если кнопка выбрана (её button_name передано в множестве data в функцию get_kb),
    то перед ней появляется check_symbol
    - выбор можно отменить, повторно нажав на кнопку -- тогда check_symbol пропадет
    - после выбора всех вариантов нужно нажать кнопку "Сохранить"

    Примечания:
    - названия кнопок будут даваться по очереди, итерируясь по списку button_names
    - встроенный конструктор CallbackData создаёт cb только с одним параметром button_id,
    означающим индекс названия кнопки (button_name) в списке button_names. button_id нужно использовать,
    чтобы получить название кнопки из списка button_names там, где нужно
    - чтобы обращаться к cb экземпляра этого класса, можно вызывать его напрямую: example_kb.cb
    """

    # добавить save_button_callback + дописать, что нужно указывать callback, используемые в следующем state'е вашей FSM, если это не последний state
    def __init__(
        self,
        button_names: list,
        cb_name: str,
        multiselect: bool = False,
        save_button_cb_name: str = None,
        check_symbol: str = "✓",
    ):
        self.button_names = button_names
        self.cb = CallbackData(cb_name, "button_id")
        self.multiselect = multiselect

        if self.multiselect:
            try:
                self.save_button_cb = CallbackData(save_button_cb_name)
            except:
                raise ValueError(
                    """If multiselect is True, you must specify save_button_cb_name 
                                 to have smooth transition between FSM states"""
                )

        self.check_symbol = check_symbol

    def make_button(
        self, button_name: str, button_id: int, checked: bool = False
    ) -> InlineKeyboardButton:
        button_name = "✓" + button_name if checked else button_name

        return InlineKeyboardButton(
            text=button_name, callback_data=self.cb.new(button_id=str(button_id))
        )

    def get_kb(self, data: list = []) -> InlineKeyboardMarkup:
        if not self.multiselect or (self.multiselect and not data):
            kb = InlineKeyboardMarkup()
            for index in range(len(self.button_names)):
                button_name = self.button_names[index]
                kb.add(self.make_button(button_name=button_name, button_id=index))

        if self.multiselect and data:
            kb = InlineKeyboardMarkup()
            for index in range(len(self.button_names)):
                button_name = self.button_names[index]
                if button_name in data:
                    kb.add(
                        self.make_button(
                            button_name=button_name, button_id=index, checked=True
                        )
                    )
                else:
                    kb.add(self.make_button(button_name=button_name, button_id=index))

            kb.add(
                InlineKeyboardButton(
                    text="💾 Сохранить", callback_data=self.save_button_cb.new()
                )
            )

        return kb


all_experience_types = ["Меньше 1 года", "1-3 года"]
experience_kb = KB(button_names=all_experience_types, cb_name="experience_cb")

all_salary_types = ["От 15 000", "От 30 000", "От 50 000", "От 70 000", "От 100 000"]
salary_kb = KB(button_names=all_salary_types, cb_name="salary_cb")

all_tags = [
    "Корпоративное право",
    "Разрешение споров",
    "Гражданское право",
    "Интеллектуальная собственность",
    "Персональные данные",
]
tags_kb = KB(
    button_names=all_tags,
    multiselect=True,
    cb_name="tags_cb",
    save_button_cb_name="save_tags",
)

# добавить сюда новые типы через соответствующую функцию из БД, если они появятся
all_desired_employer_types = ["Консалтинг", "Инхаус"]
desired_employer_types_kb = KB(
    button_names=all_desired_employer_types,
    multiselect=True,
    cb_name="desired_employer_types_cb",
    save_button_cb_name="save_desired_employer_types_ids",
)

resolve_review_kb = KB(button_names=["Разрешить"], cb_name="resolve_review_cb")

desc_cb = CallbackData("desc", "description")


def vacancy_kb_show_desc(vacancy: Vacancy) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Показать описание",
                    callback_data=desc_cb.new(description="show"),
                )
            ]
        ]
    )

    if vacancy.url:
        kb.add(InlineKeyboardButton(text="Подробнее", url=vacancy.url))

    return kb


def vacancy_kb_hide_desc(vacancy: Vacancy) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Скрыть описание",
                    callback_data=desc_cb.new(description="hide"),
                )
            ]
        ]
    )

    if vacancy.url:
        kb.add(InlineKeyboardButton(text="Подробнее", url=vacancy.url))

    return kb
