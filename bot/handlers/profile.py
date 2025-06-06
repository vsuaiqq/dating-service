from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from io import BytesIO
from typing import Optional, Callable

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
from utils.media import MAX_MEDIA_FILES, process_media_file
from utils.CustomRouter import CustomRouter
from utils.logger import logger
from models.api.profile.requests import SaveProfileRequest
from exceptions.rate_limit_error import RateLimitError

router = CustomRouter()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, _: Callable):
    try:
        profile = await router.profile_client.get_profile_by_user_id(message.from_user.id)
        if profile:
            await message.answer(_("greeting_start"), reply_markup=get_main_keyboard(profile.is_active, _))
        else:
            await message.answer(_("greeting_start"), reply_markup=get_start_keyboard(_))
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"))


@router.message(I18nTextFilter("start_button"))
async def text_start(message: types.Message, state: FSMContext, _: Callable):
    try:
        profile = await router.profile_client.get_profile_by_user_id(message.from_user.id)
        if profile:
            await message.answer(_("profile_already_exists"), reply_markup=get_main_keyboard(profile['is_active'], _))
        else:
            await message.answer(_("please_send_video_note_verification"))
            await state.set_state(ProfileStates.waiting_for_video_note)
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"))


@router.message(ProfileStates.waiting_for_video_note, F.video_note)
async def verify_video_note(message: types.Message, _: Callable):
    try:
        file = await message.bot.get_file(message.video_note.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        bytes_data = file_bytes.getvalue()

        if not bytes_data:
            await message.answer(_("video_verification_error_empty_file"))
            return

        if not file.file_id:
            await message.answer(_("empty_filename"))
            return


        await router.profile_client.verify_video(
            user_id=message.from_user.id,
            file_bytes=bytes_data,
            file_id=file.file_id
        )
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"))
    except ValueError as e:
        await message.answer(_("video_verification_error") + f": {str(e)}")
    except Exception as e:
        await message.answer(_("video_verification_error"))


@router.message(ProfileStates.waiting_for_video_note)
async def wrong_content_type(message: types.Message, _: Callable):
    await message.answer(_("please_send_video_note_only"))


@router.message(ProfileStates.age)
async def get_age(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("greeting_start"), reply_markup=get_start_keyboard(_))
        await state.clear()
        return

    try:
        age, error = ProfileValidator.validate_age(message.text, _)
        if error:
            await message.answer(error, reply_markup=get_back_keyboard(_))
            return

        await state.update_data(age=age)
        await message.answer(_("ask_gender"), reply_markup=get_gender_keyboard(_))
        await state.set_state(ProfileStates.gender)
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.gender)
async def get_gender(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_age"), reply_markup=get_back_keyboard(_))
        await state.set_state(ProfileStates.age)
        return

    try:
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
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.interesting_gender)
async def get_interesting_gender(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_gender"), reply_markup=get_gender_keyboard(_))
        await state.set_state(ProfileStates.gender)
        return

    try:
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
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.city, F.text | F.location)
async def get_city(message: types.Message, state: FSMContext, _: Callable):
    if message.text and message.text == _("back_button"):
        await message.answer(_("ask_interesting_gender"), reply_markup=get_interesting_gender_keyboard(_))
        await state.set_state(ProfileStates.interesting_gender)
        return

    try:
        update_data = {}
        error = None

        if message.location:
            coords, error = ProfileValidator.validate_location(message.location, _)
            if not error:
                update_data.update({
                    'latitude': message.location.latitude,
                    'longitude': message.location.longitude,
                    'city': None
                })
                await state.update_data(update_data)
                await message.answer(_("ask_name"), reply_markup=get_back_keyboard(_))
                await state.set_state(ProfileStates.name)
                return

        elif message.text:
            city, error = ProfileValidator.validate_city(message.text, _)
            if not error:
                update_data.update({
                    'city': city,
                    'latitude': None,
                    'longitude': None
                })
        else:
            error = _("invalid_input_type")

        if error:
            await message.answer(error)
            return

        await state.update_data(update_data)
        await message.answer(_("ask_name"), reply_markup=get_back_keyboard(_))
        await state.set_state(ProfileStates.name)
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.name)
async def get_name(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_city"))
        await state.set_state(ProfileStates.city)
        return

    try:
        name, error = ProfileValidator.validate_name(message.text, _)
        if error:
            await message.answer(error)
            return

        await state.update_data(name=name)
        await message.answer(_("ask_about"), reply_markup=get_skip_keyboard(_))
        await state.set_state(ProfileStates.about)
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.about)
async def get_about(message: types.Message, state: FSMContext, _: Callable):
    if message.text == _("back_button"):
        await message.answer(_("ask_name"))
        await state.set_state(ProfileStates.name)
        return

    try:
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
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"), reply_markup=get_back_keyboard(_))
        return False
    except Exception as e:
        await message.answer(_("unexpected_error"))


async def save_profile(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    media_list = data.get("media", [])

    try:
        await router.profile_client.save_profile(
            message.from_user.id,
            SaveProfileRequest(**{
                'name': data["name"],
                'gender': data["gender"],
                'city': data["city"],
                'age': int(data["age"]),
                'interesting_gender': data["interesting_gender"],
                'about': data["about"],
                'latitude': data["latitude"],
                'longitude': data["longitude"]
            })
        )

        if media_list:
            for media in media_list:
                try:
                    file = await message.bot.get_file(media['file_id'])
                    file_bytes = await message.bot.download_file(file.file_path)
                    if not file_bytes:
                        continue

                    byte_data = BytesIO(file_bytes.read())
                    extension = ".jpg" if media['type'] == "photo" else ".mp4"
                    filename = f"{message.from_user.id}_{file.file_id}{extension}"
                    await router.media_client.upload_file(
                        message.from_user.id,
                        media['type'],
                        byte_data,
                        filename
                    )
                except Exception as e:
                    logger.error(f"Failed to upload media: {str(e)}")
                    continue

        return True
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"), reply_markup=get_back_keyboard(_))
        return False
    except Exception as e:
        await message.answer(_("save_error") + f": {str(e)}", reply_markup=get_back_keyboard(_))
        return False


async def show_profile(message: types.Message, state: FSMContext, _: Callable):
    data = await state.get_data()
    media_list = data.get("media", [])

    if not media_list:
        await message.answer(_("no_media_error"), reply_markup=get_back_keyboard(_))
        return False

    try:
        if data['city'] is None:
            profile_text = f"{data['name']}, {data['age']} - {data['about']} {_('active_status')}"
        else:
            profile_text = f"{data['name']}, {data['age']}, {data['city']} - {data['about']} {_('active_status')}"

        media_objects = []

        for i, media in enumerate(media_list):
            if media['type'] == "photo":
                media_obj = InputMediaPhoto(media=media['file_id'], caption=profile_text if i == 0 else None)
            else:
                media_obj = InputMediaVideo(media=media['file_id'], caption=profile_text if i == 0 else None)
            media_objects.append(media_obj)

        await message.answer(_("profile_preview"))
        await message.answer_media_group(media=media_objects)
        return True
    except RateLimitError:
        await message.answer(_("rate_limit_error_try_later"), reply_markup=get_back_keyboard(_))
        return False
    except Exception as e:
        await message.answer(_("preview_error") + f": {str(e)}", reply_markup=get_back_keyboard(_))
        return False


@router.message(ProfileStates.media, F.media_group_id)
async def handle_media_group(message: types.Message, state: FSMContext, _: Callable,
                             album: Optional[list[types.Message]] = None):
    try:
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
                _("media_added").format(now=new_count, total=MAX_MEDIA_FILES, remainder=MAX_MEDIA_FILES - new_count),
                reply_markup=get_media_finish_keyboard(_)
            )
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.media, F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}))
async def handle_single_media(message: types.Message, state: FSMContext, _: Callable):
    try:
        await handle_media_group(message, state, _)
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.media, I18nTextFilter("finish_media_button"))
async def finish_media_upload(message: types.Message, state: FSMContext, _: Callable):
    try:
        data = await state.get_data()

        if not data.get("media"):
            await message.answer(_("no_media_error"), reply_markup=get_back_keyboard(_))
            return

        preview_success = await show_profile(message, state, _)

        if preview_success:
            await message.answer(_("confirm_profile"), reply_markup=get_profile_creation_confirm_keyboard(_))
    except Exception as e:
        await message.answer(_("unexpected_error"))


@router.message(ProfileStates.media, I18nTextFilter("save_profile_button"))
async def confirm_profile(message: types.Message, state: FSMContext, _: Callable):
    try:
        saved_successfully = await save_profile(message, state, _)

        if saved_successfully:
            await message.answer(_("profile_saved"), reply_markup=get_main_keyboard(True, _))
            await state.clear()
        else:
            await message.answer(_("save_error"), reply_markup=get_back_keyboard(_))
    except Exception as e:
        await message.answer(_("unexpected_error"))