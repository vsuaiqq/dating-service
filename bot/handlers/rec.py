import json
from typing import List, Dict, Optional
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from typing import Callable
from states.recommendations import RecommendationStates
from utils.I18nTextFilter import I18nTextFilter
from keyboards.main import get_main_keyboard
from keyboards.start import get_start_keyboard

router = Router()

RECOMMENDATIONS_CACHE_PREFIX = "user_recs:"
CACHE_EXPIRE_SECONDS = 3600  # 1 час
BATCH_SIZE = 50  # Количество рекомендаций для загрузки

async def check_is_profile_exists(user_id: int) -> bool:
    """Проверяет существование профиля через profile_client"""
    try:
        profile = await router.profile_client.get_profile_by_user_id(user_id)
        return profile is not None and profile.get('is_active', False)
    except Exception:
        return False

async def get_cached_recommendations(user_id: int, redis) -> Optional[List[Dict]]:
    """Получение рекомендаций из кэша Redis"""
    key = f"{RECOMMENDATIONS_CACHE_PREFIX}{user_id}"
    cached_data = await redis.get(key)
    if cached_data:
        return json.loads(cached_data)
    return None

async def set_recommendations_cache(user_id: int, recommendations: List[Dict], redis):
    """Сохранение рекомендаций в кэш Redis"""
    key = f"{RECOMMENDATIONS_CACHE_PREFIX}{user_id}"
    await redis.set(key, json.dumps(recommendations), ex=CACHE_EXPIRE_SECONDS)

async def clear_recommendations_cache(user_id: int, redis):
    """Очистка кэша рекомендаций"""
    key = f"{RECOMMENDATIONS_CACHE_PREFIX}{user_id}"
    await redis.delete(key)

@router.message(I18nTextFilter("view_recommendations_button"))
async def start_recommendations(
    message: types.Message,
    state: FSMContext,
    _: Callable
):
    """Начало просмотра рекомендаций"""
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return

    cached_recs = await get_cached_recommendations(message.from_user.id, router.redis)
    
    if cached_recs:
        await state.update_data(
            recommendations=cached_recs,
            current_index=0,
            from_cache=True
        )
        await message.answer(_("loading_from_cache"))
    else:
        recommendations = await router.recsys.get_hybrid_recommendations(
            message.from_user.id,
            count=BATCH_SIZE
        )
        
        if not recommendations:
            await message.answer(_("no_recommendations_found"))
            return
        
        await set_recommendations_cache(message.from_user.id, recommendations, router.redis)
        
        await state.update_data(
            recommendations=recommendations,
            current_index=0,
            from_cache=False
        )
    
    await show_recommendation(message, state, _)

async def show_recommendation(
    message: types.Message,
    state: FSMContext,
    _: Callable
):
    """Отображение текущей рекомендации"""
    data = await state.get_data()
    recommendations = data.get("recommendations", [])
    current_index = data.get("current_index", 0)
    
    # Проверяем, осталось ли мало рекомендаций и были ли они из кэша
    if current_index >= len(recommendations):
        if data.get("from_cache"):
            # Если кэш закончился, загружаем новые рекомендации
            new_recommendations = await router.recsys.get_hybrid_recommendations(
                message.from_user.id,
                count=BATCH_SIZE
            )
            
            if new_recommendations:
                await set_recommendations_cache(message.from_user.id, new_recommendations, router.redis)
                await state.update_data(
                    recommendations=new_recommendations,
                    current_index=0,
                    from_cache=False
                )
                return await show_recommendation(message, state, _)
        
        await message.answer(_("no_more_recommendations"))
        await clear_recommendations_cache(message.from_user.id, router.redis)
        await state.clear()
        return
    
    profile = recommendations[current_index]
    
    profile_text = _("recommendation_profile").format(
        name=profile["name"],
        age=profile["age"],
        city=profile["city"],
        about=profile["about"]
    )
    
    media_group = []
    for i, photo_url in enumerate(profile.get("photos", [])[:3]):
        if i == 0:
            media_group.append(InputMediaPhoto(
                media=photo_url,
                caption=profile_text
            ))
        else:
            media_group.append(InputMediaPhoto(media=photo_url))
    
    actions_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("like_button"),
                callback_data=f"rec_action:like:{profile['user_id']}"
            ),
            InlineKeyboardButton(
                text=_("dislike_button"),
                callback_data=f"rec_action:dislike:{profile['user_id']}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("skip_button"),
                callback_data="rec_action:skip"
            )
        ]
    ])
    
    try:
        if media_group:
            await message.answer_media_group(media=media_group)
        await message.answer(
            _("what_to_do_with_profile"),
            reply_markup=actions_kb
        )
        await state.set_state(RecommendationStates.viewing)
    except Exception as e:
        await message.answer(_("error_showing_recommendation"))
        await state.clear()

@router.callback_query(
    RecommendationStates.viewing,
    F.data.startswith("rec_action:")
)
async def handle_recommendation_action(
    callback: types.CallbackQuery,
    state: FSMContext,
    _: Callable
):
    """Обработка действий с рекомендацией"""
    action_type, *payload = callback.data.split(":")[1:]
    
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    recommendations = data.get("recommendations", [])
    
    if action_type in ("like", "dislike"):
        target_user_id = int(payload[0])
        
        await router.profile_client.record_swipe(
            from_user_id=callback.from_user.id,
            to_user_id=target_user_id,
            action=action_type
        )
        
        if action_type == "like":
            is_match = await router.profile_client.check_match(
                callback.from_user.id,
                target_user_id
            )
            
            if is_match:
                await callback.message.answer(_("match_found"))
                await clear_recommendations_cache(callback.from_user.id, router.redis)
    
    new_index = current_index + 1
    await state.update_data(current_index=new_index)
    
    await callback.message.delete()
    
    await show_recommendation(callback.message, state, _)

@router.message(
    RecommendationStates.viewing,
    I18nTextFilter("stop_recommendations_button")
)
async def stop_recommendations(
    message: types.Message,
    state: FSMContext,
    _: Callable
):
    """Прекращение просмотра рекомендаций"""
    data = await state.get_data()
    recommendations = data.get("recommendations", [])
    current_index = data.get("current_index", 0)
    
    # Если остались не просмотренные рекомендации, сохраняем их в кэш
    if current_index < len(recommendations):
        remaining_recommendations = recommendations[current_index:]
        await set_recommendations_cache(message.from_user.id, remaining_recommendations, router.redis)
    
    profile = await router.profile_client.get_profile_by_user_id(message.from_user.id)
    await message.answer(
        _("recommendations_stopped"),
        reply_markup=get_main_keyboard(profile['is_active'], _)
    )
    await state.clear()