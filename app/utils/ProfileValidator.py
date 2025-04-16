from aiogram import types
from typing import Tuple, Optional, Callable

class ProfileValidator:
    MIN_AGE = 12
    MAX_AGE = 100
    MAX_VIDEO_DURATION_SEC = 15
    MAX_FILE_SIZE_MB = 10
    MAX_ABOUT_LENGTH = 500
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 50
    MIN_CITY_LENGTH = 2
    MAX_CITY_LENGTH = 50

    @classmethod
    def validate_age(cls, age_str: str, _: Callable) -> Tuple[Optional[int], Optional[str]]:
        try:
            age = int(age_str)
            if not cls.MIN_AGE <= age <= cls.MAX_AGE:
                return None, _("age_range_error").format(
                    min=cls.MIN_AGE, 
                    max=cls.MAX_AGE
                )
            return age, None
        except ValueError:
            return None, _("age_numeric_error")

    @classmethod
    def validate_name(cls, name: str, _: Callable) -> Tuple[Optional[str], Optional[str]]:
        name = name.strip()

        if len(name) < cls.MIN_NAME_LENGTH:
            return None, _("name_min_error").format(
                min=cls.MIN_NAME_LENGTH
            )
        if len(name) > cls.MAX_NAME_LENGTH:
            return None, _("name_max_error").format(
                max=cls.MAX_NAME_LENGTH
            )
        
        return name, None

    @classmethod
    def validate_city(cls, city: str, _: Callable) -> Tuple[Optional[str], Optional[str]]:
        city = city.strip()

        if len(city) < cls.MIN_CITY_LENGTH:
            return None, _("city_min_error").format(
                min=cls.MIN_CITY_LENGTH
            )
        if len(city) > cls.MAX_CITY_LENGTH:
            return None, _("city_max_error").format(
                max=cls.MAX_CITY_LENGTH
            )
        
        return city, None

    @classmethod
    def validate_about(cls, about: str, _: Callable) -> Tuple[Optional[str], Optional[str]]:
        about = about.strip()

        if len(about) > cls.MAX_ABOUT_LENGTH:
            return None, _("about_max_error").format(
                max=cls.MAX_ABOUT_LENGTH
            )
        
        return about, None

    @classmethod
    def validate_media(cls, message: types.Message, _: Callable) -> Tuple[bool, Optional[str]]:
        if message.video and message.video.duration > cls.MAX_VIDEO_DURATION_SEC:
            return False, _("video_duration_error").format(
                max=cls.MAX_VIDEO_DURATION_SEC
            )
            
        file = message.video or (message.photo[-1] if message.photo else None)
        if not file:
            return False, _("media_type_error")
            
        if file.file_size > cls.MAX_FILE_SIZE_MB * 1024 * 1024:
            return False, _("file_size_error").format(
                max=cls.MAX_FILE_SIZE_MB
            )
            
        return True, None
