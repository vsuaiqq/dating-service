from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_video_note = State()
    name = State()
    gender = State()
    city = State()
    age = State()
    interesting_gender = State()
    about = State()
    media = State()
    latitude = State()
    longitude = State()