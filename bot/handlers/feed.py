from aiogram import types, F
from aiogram.fsm.context import FSMContext
from typing import Callable
from aiogram.types import ContentType, InputMediaPhoto, InputMediaVideo

from utils.I18nTextFilter import I18nTextFilter
from utils.CustomRouter import CustomRouter
from utils.profile import is_profile_active
from utils.logger import logger
from keyboards.swipe import get_swipe_keyboard
from keyboards.main import get_main_keyboard
from keyboards.back import get_back_keyboard
from states.message import Message
from models.api.swipe.requests import AddSwipeRequest
from exceptions.rate_limit_error import RateLimitError

router = CustomRouter()

async def send_next_recommendation(user_id: int, message: types.Message, state: FSMContext, _: Callable):
    recsys_client = router.recsys_client
    profile_client = router.profile_client
    media_client = router.media_client

    try:
        is_active = await is_profile_active(profile_client, message.from_user.id)

        try:
            response = await recsys_client.get_recommendations(user_id)
        except RateLimitError:
            await message.answer(_("rate_limit_error_try_later"))
            return
        except Exception as e:
            await message.answer(_("recommendations_load_error"))
            return

        recs = response.recommendations if response else []

        if not recs:
            await message.answer(_("no_more_recommendations"), reply_markup=get_main_keyboard(is_active, _))
            return

        while True:
            if not recs:
                await message.answer(_("no_more_recommendations"), reply_markup=get_main_keyboard(is_active, _))
                return

            recommendation = recs.pop()
            next_user_id = recommendation.user_id
            distance = recommendation.distance

            try:
                profile = await profile_client.get_profile_by_user_id(next_user_id)
                if profile and profile.is_active:
                    break
            except RateLimitError:
                await message.answer(_("rate_limit_error_try_later"))
                return
            except Exception:
                continue

        if not profile:
            await message.answer(_("no_more_recommendations"), reply_markup=get_main_keyboard(is_active, _))
            return

        if distance < 1:
            distance_str = f"{int(distance * 1000)} {_('kilometers_away')}"
        else:
            distance_str = f"{round(distance, 1)} {_('meters_away')}"

        text = (
            f"{profile.name}, {profile.age}\n"
            f"{distance_str}\n\n"
            f"{profile.about or ''}"
        )

        media_objects = []
        try:
            presigned_media_resp = await media_client.get_presigned_urls(next_user_id)
            presigned_media = presigned_media_resp.presigned_media

            for i, media in enumerate(presigned_media):
                if media.type.value == "photo":
                    media_obj = InputMediaPhoto(media=media.url, caption=text if i == 0 else None)
                else:
                    media_obj = InputMediaVideo(media=media.url, caption=text if i == 0 else None)
                media_objects.append(media_obj)
        except RateLimitError:
            await message.answer(_("rate_limit_error_try_later"))
            return
        except Exception:
            pass

        await state.update_data(current_profile_id=profile.user_id)

        if media_objects:
            try:
                await message.answer_media_group(media=media_objects)
                await message.answer(_("swipe_prompt"), reply_markup=get_swipe_keyboard(_))
            except Exception:
                await message.answer(text, reply_markup=get_swipe_keyboard(_))
        else:
            await message.answer(text, reply_markup=get_swipe_keyboard(_))

    except Exception as e:
        await message.answer(_("unexpected_error"))
        logger.info(f"Error in send_next_recommendation: {str(e)}")
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"), reply_markup=get_back_keyboard(_))

@router.message(F.text.in_(["👎", "👍", "❓"]))
async def handle_swipe_text(message: types.Message, state: FSMContext, _: Callable):
    try:
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

        swipe_request = AddSwipeRequest(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            action="like" if action_emoji == "👍" else "dislike"
        )

        try:
            await router.swipe_client.add_swipe(
                user_id=message.from_user.id,
                username=message.from_user.username,
                swipe_data=swipe_request  # Правильная передача объекта
            )
        except RateLimitError:
            await message.answer(_("rate_limit_error_try_later"))
            return
        except Exception as e:
            logger.error(f"Swipe error: {str(e)}", exc_info=True)
            await message.answer(_("swipe_send_error"))
            return

        await message.answer(_("swipe_sent"))
        await send_next_recommendation(from_user_id, message, state, _)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        await message.answer(_("unexpected_error"))
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"), reply_markup=get_back_keyboard(_))

@router.message(Message.waiting_for_question)
async def handle_question_input(message: types.Message, state: FSMContext, _: Callable):
    from_user_id = message.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    question_text = message.text

    swipe_request = AddSwipeRequest(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        action="question",
        message=question_text
    )

    await router.swipe_client.add_swipe(
        user_id=message.from_user.id,
        username=message.from_user.username,
        swipe_data=swipe_request
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
