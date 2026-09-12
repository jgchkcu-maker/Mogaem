from aiogram.fsm.state import State, StatesGroup


class ProfileForm(StatesGroup):
    ready = State()
    age = State()
    gender = State()
    search_gender = State()
    city = State()
    name = State()
    bio = State()
    photos = State()
    preview = State()
