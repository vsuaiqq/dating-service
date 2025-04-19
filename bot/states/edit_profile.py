from aiogram.fsm.state import State, StatesGroup

class EditProfileStates(StatesGroup):
    field = State()
    name = State()
    gender = State()
    city = State()
    age = State()
    interesting_gender = State()
    about = State()
    media = State()
