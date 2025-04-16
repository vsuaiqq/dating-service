from aiogram import Router, types, F
from typing import Callable
from keyboards.start import get_start_keyboard
from keyboards.main import get_main_keyboard
from keyboards.confirm_disable import get_confirm_disable_keyboard
from aiogram.types import InputMediaPhoto, InputMediaVideo
from utils.I18nTextFilter import I18nTextFilter

router = Router()

@router.message(I18nTextFilter("my_profile_button"))
async def show_my_profile(message: types.Message, _: Callable):    
    profile = await router.profile_repo.get_profile_by_user_id(message.from_user.id)
    if not profile:
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    
    media_list = await router.profile_repo.get_media_by_profile_id(profile["id"])
    
    profile_text = f"{profile['name']}, {profile['age']}, {profile['city']} - {profile['about']}"
    media_objects = []
    
    for i, media in enumerate(media_list):
        media_url = router.s3_uploader.generate_presigned_url(media["s3_key"])
        if media["type"] == "photo":
            media_obj = InputMediaPhoto(media=media_url, caption=profile_text if i == 0 else None)
        else:
            media_obj = InputMediaVideo(media=media_url, caption=profile_text if i == 0 else None)
        media_objects.append(media_obj)

    try:
        await message.answer(_("profile_preview"))
        await message.answer_media_group(media=media_objects)
        return True
    except Exception as e:
        await message.answer(_("preview_error") + f": {str(e)}", reply_markup=get_main_keyboard(_))
        return False

@router.message(I18nTextFilter("disable_profile_button"))
async def disable_profile_start(message: types.Message, _: Callable):
    await message.answer(
        _("confirm_disable_profile"),
        reply_markup=get_confirm_disable_keyboard(_)
    )

@router.message(I18nTextFilter("confirm_disable_profile_button"))
async def confirm_disable_profile(message: types.Message, _: Callable):
    success = await router.profile_repo.toggle_profile_active(message.from_user.id, False)
    if success:
        await message.answer(
            _("profile_disabled_success"),
            reply_markup=get_start_keyboard(_)
        )
    else:
        await message.answer(_("profile_disable_error"))

@router.message(I18nTextFilter("cancel_disable_profile_button"))
async def cancel_disable_profile(message: types.Message, _: Callable):
    await message.answer(
        _("profile_disable_canceled"),
        reply_markup=get_main_keyboard(_)
    )
