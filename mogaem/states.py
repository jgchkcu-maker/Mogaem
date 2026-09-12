from aiogram.fsm.state import State, StatesGroup


class ProfileForm(StatesGroup):
    name = State()
    age = State()
    gender = State()
    city = State()
    bio = State()
    photos = State()
    search_gender = State()
