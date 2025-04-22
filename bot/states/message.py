from aiogram.fsm.state import State, StatesGroup

class Message(StatesGroup):
    waiting_for_question = State()
