from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from io import BytesIO
from typing import Optional, Literal, Union, Callable
from keyboards.start import get_start_keyboard
from keyboards.main import get_main_keyboard
from keyboards.back import get_back_keyboard
from keyboards.skip import get_skip_keyboard
from keyboards.gender import get_gender_keyboard, get_interesting_gender_keyboard
from keyboards.profile_creation_confirm import get_profile_creation_confirm_keyboard
from keyboards.media_finish import get_media_finish_keyboard
from states.profile import ProfileStates
from aiogram.types import ContentType, InputMediaPhoto, InputMediaVideo
from utils.ProfileValidator import ProfileValidator
from utils.I18nTextFilter import I18nTextFilter

router = Router()

MAX_MEDIA_FILES = 3

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, _: Callable):
    profile = await router.profile_repo.get_profile_by_user_id(message.from_user.id)
    if profile:
        await message.answer(_("greeting_start"), reply_markup=get_main_keyboard(_))
    else:
        await message.answer(_("greeting_start"), reply_markup=get_start_keyboard(_))

@router.message(I18nTextFilter("start_button"))
async def text_start(message: types.Message, state: FSMContext, _: Callable):
    await message.answer(_("ask_age"), reply_markup=get_back_keyboard(_))
    await state.set_state(ProfileStates.age)

@router.message(ProfileStates.age)
async def get_age(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("greeting_start"), reply_markup=get_start_keyboard(_))
        await state.clear()
        return

    age, error = ProfileValidator.validate_age(message.text, _)
    if error:
        await message.answer(error, reply_markup=get_back_keyboard(_))
        return
        
    await state.update_data(age=age)
    await message.answer(_("ask_gender"), reply_markup=get_gender_keyboard(_))
    await state.set_state(ProfileStates.gender)

@router.message(ProfileStates.gender)
async def get_gender(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_age"), reply_markup=get_back_keyboard(_))
        await state.set_state(ProfileStates.age)
        return
        
    gender_map = {
        _("gender_male_button"): "male",
        _("gender_female_button"): "female"
    }
    
    if message.text not in gender_map:
        await message.answer(_("invalid_gender_error"), reply_markup=get_gender_keyboard(_))
        return
        
    await state.update_data(gender=gender_map[message.text])
    await message.answer(_("ask_interesting_gender"), reply_markup=get_interesting_gender_keyboard(_))
    await state.set_state(ProfileStates.interesting_gender)

@router.message(ProfileStates.interesting_gender)
async def get_interesting_gender(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_gender"), reply_markup=get_gender_keyboard(_))
        await state.set_state(ProfileStates.gender)
        return
        
    gender_map = {
        _("gender_male_button"): "male",
        _("gender_female_button"): "female",
        _("gender_any_button"): "any"
    }
    
    if message.text not in gender_map:
        await message.answer(_("invalid_gender_error"), reply_markup=get_interesting_gender_keyboard(_))
        return
        
    await state.update_data(interesting_gender=gender_map[message.text])
    await message.answer(_("ask_city"), reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_("back_button"))]],
        resize_keyboard=True
    ))
    await state.set_state(ProfileStates.city)

@router.message(ProfileStates.city)
async def get_city(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_interesting_gender"), reply_markup=get_interesting_gender_keyboard(_))
        await state.set_state(ProfileStates.interesting_gender)
        return
        
    city, error = ProfileValidator.validate_city(message.text, _)
    if error:
        await message.answer(error)
        return
        
    await state.update_data(city=city)
    await message.answer(_("ask_name"), reply_markup=get_back_keyboard(_))
    await state.set_state(ProfileStates.name)

@router.message(ProfileStates.name)
async def get_name(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_city"))
        await state.set_state(ProfileStates.city)
        return
        
    name, error = ProfileValidator.validate_name(message.text, _)
    if error:
        await message.answer(error)
        return
        
    await state.update_data(name=name)
    await message.answer(_("ask_about"), reply_markup=get_skip_keyboard(_))
    await state.set_state(ProfileStates.about)

@router.message(ProfileStates.about)
async def get_about(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_name"))
        await state.set_state(ProfileStates.name)
        return
    
    if message.text == _("skip_button"):
        await state.update_data(about="")
        await message.answer(_("ask_media"), reply_markup=get_back_keyboard(_))
        await state.set_state(ProfileStates.media)
        return
        
    about, error = ProfileValidator.validate_about(message.text, _)
    if error:
        await message.answer(error)
        return
        
    await state.update_data(about=about)
    await message.answer(_("ask_media"), reply_markup=get_back_keyboard(_))
    await state.set_state(ProfileStates.media)

async def process_media_file(message: types.Message, file: Union[types.PhotoSize, types.Video], file_type: Literal["photo", "video"], state: FSMContext) -> bool:
    data = await state.get_data()
    media_list = data.get("media", [])
    
    if len(media_list) >= MAX_MEDIA_FILES:
        return False

    media_list.append({
        'file_id': file.file_id,
        'type': file_type,
        'file_size': file.file_size,
        'duration': getattr(file, 'duration', None)
    })
    
    await state.update_data(media=media_list)
    return True

async def save_profile(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    media_list = data.get("media", [])
    
    try:
        profile_id = await router.profile_repo.save_profile(
            user_id=message.from_user.id,
            name=data["name"],
            gender=data["gender"],
            city=data["city"],
            age=int(data["age"]),
            interesting_gender=data["interesting_gender"],
            about=data["about"]
        )
        
        if media_list:
            saved_media = []
            for media in media_list:
                file = await message.bot.get_file(media['file_id'])
                file_bytes = await message.bot.download_file(file.file_path)
                byte_data = BytesIO(file_bytes.read())
                
                extension = ".jpg" if media['type'] == "photo" else ".mp4"
                filename = f"{message.from_user.id}_{file.file_id}{extension}"
                s3_key = await router.s3_uploader.upload_file(byte_data, filename)
                
                saved_media.append((media['type'], s3_key))
            
            await router.profile_repo.save_media(profile_id, saved_media)
        
        return True
    except Exception as e:
        await message.answer(_("save_error") + f": {str(e)}", reply_markup=get_back_keyboard(_))
        return False

async def show_profile(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    media_list = data.get("media", [])
    
    if not media_list:
        await message.answer(_("no_media_error"), reply_markup=get_back_keyboard(_))
        return False

    profile_text = f"{data['name']}, {data['age']}, {data['city']} - {data['about']}"
    media_objects = []
    
    for i, media in enumerate(media_list):
        if media['type'] == "photo":
            media_obj = InputMediaPhoto(media=media['file_id'], caption=profile_text if i == 0 else None)
        else:
            media_obj = InputMediaVideo(media=media['file_id'], caption=profile_text if i == 0 else None)
        media_objects.append(media_obj)

    try:
        await message.answer(_("profile_preview"))
        await message.answer_media_group(media=media_objects)
        return True
    except Exception as e:
        await message.answer(_("preview_error") + f": {str(e)}", reply_markup=get_back_keyboard(_))
        return False

@router.message(ProfileStates.media, F.media_group_id)
async def handle_media_group(message: types.Message, state: FSMContext, _: Callable, album: Optional[list[types.Message]] = None):
    is_valid, error = ProfileValidator.validate_media(message, _)
    if not is_valid:
        await message.answer(error, reply_markup=get_back_keyboard(_))
        return

    data = await state.get_data()
    current_count = len(data.get("media", []))
    
    if current_count >= MAX_MEDIA_FILES:
        await message.answer(_("max_media_reached").format(MAX_MEDIA_FILES))
        await show_profile(message, state, _)
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
        await show_profile(message, state, _)
    else:
        await message.answer(
            _("media_added").format(added=added_count, total=new_count, max=MAX_MEDIA_FILES),
            reply_markup=get_media_finish_keyboard(_)
        )

@router.message(ProfileStates.media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def handle_single_media(message: types.Message, state: FSMContext, _: Callable):
    await handle_media_group(message, state, _)

@router.message(ProfileStates.media, I18nTextFilter("finish_media_button"))
async def finish_media_upload(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    
    if not data.get("media"):
        await message.answer(_("no_media_error"), reply_markup=get_back_keyboard(_))
        return
    
    preview_success = await show_profile(message, state, _)
    
    if preview_success:
        await message.answer(_("confirm_profile"), reply_markup=get_profile_creation_confirm_keyboard(_))

@router.message(ProfileStates.media, I18nTextFilter("save_profile_button"))
async def confirm_profile(message: types.Message, state: FSMContext, _: Callable):    
    saved_successfully = await save_profile(message, state, _)
    
    if saved_successfully:
        await message.answer(_("profile_saved"), reply_markup=get_main_keyboard(_))
        await state.clear()
    else:
        await message.answer(_("save_error"), reply_markup=get_back_keyboard(_))
