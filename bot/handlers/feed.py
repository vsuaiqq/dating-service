from aiogram import types, F
from aiogram.fsm.context import FSMContext
from typing import Callable

from utils.I18nTextFilter import I18nTextFilter
from utils.CustomRouter import CustomRouter
from utils.profile import is_profile_active
from keyboards.swipe import get_swipe_keyboard
from keyboards.main import get_main_keyboard
from keyboards.back import get_back_keyboard
from states.message import Message

router = CustomRouter()

async def send_next_recommendation(user_id: int, message: types.Message, state: FSMContext, _: Callable):
    recommendation_cache = router.recommendation_cache
    recsys_client = router.recsys_client
    profile_client = router.profile_client

    is_active = await is_profile_active(router.profile_client, message.from_user.id)
    
    recs = await recommendation_cache.get(user_id)
    if not recs:
        response = await recsys_client.get_recommendations(user_id, count=10)
        recs = response.get("recommendations", [])
        if not recs:
            await message.answer(_("no_more_recommendations"), reply_markup=get_main_keyboard(is_active, _))
            return
        await recommendation_cache.set(user_id, recs)

    while True:
        next_user_id = await recommendation_cache.pop_next(user_id)
        if not next_user_id:
            await message.answer(_("no_more_recommendations"), reply_markup=get_main_keyboard(is_active, _))
            return

        profile = await profile_client.get_profile_by_user_id(next_user_id)
        if profile and profile.get("is_active"):
            break

    text = f"{profile['name']}, {profile['age']}\n{profile.get('about', '')}"

    await state.update_data(current_profile_id=profile['user_id'])

    await message.answer(text, reply_markup=get_swipe_keyboard(_))

@router.message(F.text.in_(["👎", "👍", "❓"]))
async def handle_swipe_text(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    from_user_id = message.from_user.id

    if not to_user_id:
        await message.answer(_("no_profile_selected"))
        return

    action_emoji = message.text

    if action_emoji == "❓":
        await state.set_state(Message.waiting_for_question)
        await message.answer(_("enter_your_question"), reply_markup=get_back_keyboard(_))

        return

    action = "like" if action_emoji == "👍" else "dislike"
    await router.swipe_client.add_swipe(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        action=action
    )
    await message.answer(_("swipe_sent"))
    await send_next_recommendation(from_user_id, message, state, _)

@router.message(Message.waiting_for_question)
async def handle_question_input(message: types.Message, state: FSMContext, _: Callable):
    from_user_id = message.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    question_text = message.text

    await router.swipe_client.add_swipe(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        action="question",
        message=question_text
    )

    await state.clear()
    await message.answer(_("question_sent"))
    await send_next_recommendation(from_user_id, message, state, _)

@router.message(I18nTextFilter("feed_button"))
async def show_feed(message: types.Message, _: Callable, state: FSMContext):
    await state.clear()
    await send_next_recommendation(message.from_user.id, message, state, _)

@router.message(Message.waiting_for_question, I18nTextFilter("back_button"))
async def cancel_question_input(message: types.Message, state: FSMContext, _: Callable):
    await state.clear()
    data = await state.get_data()
    current_profile_id = data.get("current_profile_id")

    if not current_profile_id:
        await message.answer(_("no_profile_selected"))
        return

    profile = await router.profile_client.get_profile_by_user_id(current_profile_id)
    if not profile or not profile.get("is_active"):
        await message.answer(_("no_more_recommendations"))
        return

    text = f"{profile['name']}, {profile['age']}\n{profile.get('about', '')}"
    await message.answer(_("question_canceled"))
    await message.answer(text, reply_markup=get_swipe_keyboard(_))

@router.message(I18nTextFilter("back_button"))
async def back_to_main_menu(message: types.Message, state: FSMContext, _: Callable):
    is_active = await is_profile_active(router.profile_client, message.from_user.id)
    await state.clear()
    await message.answer(_("returned_to_main_menu"), reply_markup=get_main_keyboard(is_active, _))
