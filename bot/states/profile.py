from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_video_note = State()
    video_verified = State()
    video_rejected = State()
    name = State()
    gender = State()
    city = State()
    age = State()
    interesting_gender = State()
    about = State()
    media = State()
    latitude = State()
    longitude = State()
