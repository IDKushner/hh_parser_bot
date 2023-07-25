from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    experience = State()
    salary = State()
    tags = State()
    desired_employer_types = State()
