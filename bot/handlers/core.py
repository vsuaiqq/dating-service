from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from typing import Callable, Optional
from io import BytesIO
from keyboards.start import get_start_keyboard
from keyboards.main import get_main_keyboard
from keyboards.confirm_disable import get_confirm_disable_keyboard
from keyboards.edit_profile import get_edit_profile_keyboard
from keyboards.back import get_back_keyboard
from keyboards.gender import get_gender_keyboard, get_interesting_gender_keyboard
from keyboards.media_finish import get_media_finish_keyboard
from aiogram.types import InputMediaPhoto, InputMediaVideo, ReplyKeyboardRemove
from utils.I18nTextFilter import I18nTextFilter
from utils.ProfileValidator import ProfileValidator
from utils.media import MAX_MEDIA_FILES, process_media_file
from states.edit_profile import EditProfileStates
from aiogram.types import ContentType

router = Router()

async def check_is_profile_exists(user_id: int):
    return (await router.profile_client.get_profile_by_user_id(user_id)) is not None
    
@router.message(I18nTextFilter("my_profile_button"))
async def show_my_profile(message: types.Message, _: Callable):    
    profile = await router.profile_client.get_profile_by_user_id(message.from_user.id)
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    
    media_list = await router.profile_client.get_media_by_profile_id(profile["id"])
    
    profile_text = f"{profile['name']}, {profile['age']}, {profile['city']} - {profile['about']} {_('active_status') if profile['is_active'] else _('inactive_status')}"
    media_objects = []
    
    for i, media in enumerate(media_list):
        media_url = await router.s3_client.get_presigned_url(media["s3_key"])
        if media["type"] == "photo":
            media_obj = InputMediaPhoto(media=media_url['url'], caption=profile_text if i == 0 else None)
        else:
            media_obj = InputMediaVideo(media=media_url['url'], caption=profile_text if i == 0 else None)
        media_objects.append(media_obj)

    try:
        await message.answer(_("profile_preview"))
        await message.answer_media_group(media=media_objects)
        return True
    except Exception as e:
        await message.answer(_("preview_error") + f": {str(e)}", reply_markup=get_main_keyboard(profile['is_active'], _))
        return False

@router.message(I18nTextFilter("disable_profile_button"))
async def disable_profile_start(message: types.Message, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    await message.answer(
        _("confirm_disable_profile"),
        reply_markup=get_confirm_disable_keyboard(_)
    )

@router.message(I18nTextFilter("confirm_disable_profile_button"))
async def confirm_disable_profile(message: types.Message, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    try:
        await router.profile_client.toggle_active(message.from_user.id, False)
        await message.answer(
            _("profile_disabled_success"),
            reply_markup=get_main_keyboard(False, _)
        )
    except Exception as e:
        await message.answer(_("profile_disable_error"))

@router.message(I18nTextFilter("cancel_disable_profile_button"))
async def cancel_disable_profile(message: types.Message, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    await message.answer(
        _("profile_disable_canceled"),
        reply_markup=get_main_keyboard(True, _)
    )

@router.message(I18nTextFilter("enable_profile_button"))
async def enable_profile(message: types.Message, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    try:
        await router.profile_client.toggle_active(message.from_user.id, True)
        await message.answer(
            _("profile_enabled_success"),
            reply_markup=get_main_keyboard(True, _)
        )
    except Exception as e:
        await message.answer(_("profile_enable_error"))

@router.message(I18nTextFilter("edit_profile_button"))
async def start_edit_profile(message: types.Message, state: FSMContext, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
    await state.set_state(EditProfileStates.field)

@router.message(EditProfileStates.field, F.text)
async def choose_field_to_edit(message: types.Message, state: FSMContext, _: Callable):
    text = message.text
    if text == _("back_button"):
        is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
        await message.answer(_("back_to_main_menu"), reply_markup=get_main_keyboard(is_active, _))
        await state.clear()
        return
    elif text == _("edit_name_button"):
        await message.answer(_("enter_new_name"), reply_markup=get_back_keyboard(_))
        await state.set_state(EditProfileStates.name)
    elif text == _("edit_age_button"):
        await message.answer(_("enter_new_age"), reply_markup=get_back_keyboard(_))
        await state.set_state(EditProfileStates.age)
    elif text == _("edit_city_button"):
        await message.answer(_("enter_new_city"), reply_markup=get_back_keyboard(_))
        await state.set_state(EditProfileStates.city)
    elif text == _("edit_about_button"):
        await message.answer(_("enter_new_about"), reply_markup=get_back_keyboard(_))
        await state.set_state(EditProfileStates.about)
    elif text == _("edit_gender_button"):
        await message.answer(_("enter_new_gender"), reply_markup=get_gender_keyboard(_))
        await state.set_state(EditProfileStates.gender)
    elif text == _("edit_interesting_gender_button"):
        await message.answer(_("enter_new_interesting_gender"), reply_markup=get_interesting_gender_keyboard(_))
        await state.set_state(EditProfileStates.interesting_gender)
    elif text == _("edit_media_button"):
        await message.answer(_("send_new_media"), reply_markup=get_back_keyboard(_))
        await state.set_state(EditProfileStates.media)
    else:
        await message.answer(_("invalid_choice"), reply_markup=get_edit_profile_keyboard(_))

@router.message(EditProfileStates.name, F.text)
async def update_name(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return
    
    name, error = ProfileValidator.validate_name(message.text, _)
    if error:
        await message.answer(error)
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "name", name)
    await message.answer(_("name_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.age, F.text)
async def update_age(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return
    
    age, error = ProfileValidator.validate_age(message.text, _)
    if error:
        await message.answer(error, reply_markup=get_back_keyboard(_))
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "age", age)
    await message.answer(_("age_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.city, F.text)
async def update_city(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return

    city, error = ProfileValidator.validate_city(message.text, _)
    if error:
        await message.answer(error)
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "city", city)
    await message.answer(_("city_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.about, F.text)
async def update_about(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return
    
    about, error = ProfileValidator.validate_about(message.text, _)
    if error:
        await message.answer(error)
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "about", about)
    await message.answer(_("about_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.gender, F.text)
async def update_city(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return

    gender_map = {
        _("gender_male_button"): "male",
        _("gender_female_button"): "female"
    }
    
    if message.text not in gender_map:
        await message.answer(_("invalid_gender_error"), reply_markup=get_gender_keyboard(_))
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "gender", gender_map[message.text])
    await message.answer(_("gender_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.interesting_gender, F.text)
async def update_city(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
        await state.set_state(EditProfileStates.field)
        return

    gender_map = {
        _("gender_male_button"): "male",
        _("gender_female_button"): "female",
        _("gender_any_button"): "any"
    }
    
    if message.text not in gender_map:
        await message.answer(_("invalid_gender_error"), reply_markup=get_interesting_gender_keyboard(_))
        return
    
    is_active = (await router.profile_client.get_profile_by_user_id(message.from_user.id))['is_active']
    
    await router.profile_client.update_field(message.from_user.id, "gender", gender_map[message.text])
    await message.answer(_("gender_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

# медиа измена

@router.message(EditProfileStates.media, F.media_group_id)
async def handle_media_group(message: types.Message, state: FSMContext, _: Callable, album: Optional[list[types.Message]] = None):
    is_valid, error = ProfileValidator.validate_media(message, _)
    if not is_valid:
        await message.answer(error, reply_markup=get_back_keyboard(_))
        return

    data = await state.get_data()
    current_count = len(data.get("media", []))
    
    if current_count >= MAX_MEDIA_FILES:
        await message.answer(_("max_media_reached").format(MAX_MEDIA_FILES))
        await finish_media_upload(message, state, _)
        return

    messages_to_process = album or [message]
    added_count = 0
    
    for msg in messages_to_process:
        if current_count + added_count >= MAX_MEDIA_FILES:
            break
            
        if msg.photo:
            file = msg.photo[-1]
            success = await process_media_file(msg, file, "photo", state)
        elif msg.video:
            file = msg.video
            success = await process_media_file(msg, file, "video", state)
        else:
            continue
            
        if success:
            added_count += 1

    data = await state.get_data()
    new_count = len(data.get("media", []))
    
    if new_count >= MAX_MEDIA_FILES:
        await message.answer(_("max_media_reached").format(MAX_MEDIA_FILES))
        await finish_media_upload(message, state, _)
    else:
        await message.answer(
            _("media_added").format(now=new_count, total=MAX_MEDIA_FILES, remainder=MAX_MEDIA_FILES-new_count),
            reply_markup=get_media_finish_keyboard(_)
        )

@router.message(EditProfileStates.media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def handle_single_media(message: types.Message, state: FSMContext, _: Callable):
    await handle_media_group(message, state, _)

@router.message(EditProfileStates.media, I18nTextFilter("finish_media_button"))
async def finish_media_upload(message: types.Message, state: FSMContext, _: Callable):
    profile = await router.profile_client.get_profile_by_user_id(message.from_user.id)
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    
    is_active = profile['is_active']

    media_list = await router.profile_client.get_media_by_profile_id(profile['id'])
    for media in media_list:
        await router.s3_client.delete_file(media['s3_key'])

    await router.profile_client.delete_media(profile['id'])

    data = await state.get_data()
    new_media_list = data.get("media", [])

    saved_media = []
    for media in new_media_list:
        file = await message.bot.get_file(media['file_id'])
        file_bytes = await message.bot.download_file(file.file_path)
        byte_data = BytesIO(file_bytes.read())
        
        extension = ".jpg" if media['type'] == "photo" else ".mp4"
        filename = f"{message.from_user.id}_{file.file_id}{extension}"
        s3_key = await router.s3_client.upload_file(byte_data, filename)
        
        saved_media.append({
            'type': media['type'],
            's3_key': s3_key['key']
        })
    
    await router.profile_client.save_media(profile['id'], saved_media)

    await message.answer(_("media_updated"), reply_markup=get_main_keyboard(is_active, _))
    await state.clear()

@router.message(EditProfileStates.media, I18nTextFilter("back_button"))
async def media_back_button_handler(message: types.Message, state: FSMContext, _: Callable):
    if not await check_is_profile_exists(message.from_user.id):
        await message.answer(_("no_profile_error"), reply_markup=get_start_keyboard(_))
        return
    await message.answer(_("choose_field_to_edit"), reply_markup=get_edit_profile_keyboard(_))
    await state.clear()
    await state.set_state(EditProfileStates.field)
