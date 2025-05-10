from aiogram import types
from aiogram.fsm.context import FSMContext
from typing import Literal, Union
from config import MAX_MEDIA_FILES

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
