from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    name = State()
    gender = State()
    city = State()
    age = State()
    interesting_gender = State()
    about = State()
    media = State()
    latitude = State()
    longitude = State()