from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union, Literal

class SaveProfileRequest(BaseModel):
    name: str = Field(..., description="Имя пользователя")
    gender: str = Field(..., description="Пол пользователя")
    city: Optional[str] = Field(None, description="Город пользователя")
    latitude: Optional[float] = Field(None, description="Широта (если город не указан)")
    longitude: Optional[float] = Field(None, description="Долгота (если город не указан)")
    age: int = Field(..., description="Возраст пользователя")
    interesting_gender: str = Field(..., description="Интересующий пол")
    about: str = Field(..., description="Описание пользователя")

    @model_validator(mode="after")
    def check_location(self) -> 'SaveProfileRequest':
        if not self.city and (self.latitude is None or self.longitude is None):
            raise ValueError("Укажите либо город, либо координаты (широту и долготу).")
        return self

    class Config:
        schema_extra = {
            "example": {
                "name": "Ирина",
                "gender": "female",
                "city": "Москва",
                "latitude": None,
                "longitude": None,
                "age": 28,
                "interesting_gender": "male",
                "about": "Люблю путешествовать и читать."
            }
        }

class ToggleActiveRequest(BaseModel):
    is_active: bool = Field(..., description="Флаг активности профиля (вкл/выкл)")

    class Config:
        schema_extra = {
            "example": {
                "is_active": True
            }
        }

class Coordinates(BaseModel):
    latitude: float = Field(..., description="Широта")
    longitude: float = Field(..., description="Долгота")

    class Config:
        schema_extra = {
            "example": {
                "latitude": 55.7558,
                "longitude": 37.6173
            }
        }

class UpdateFieldRequest(BaseModel):
    field_name: Literal[
        "name", "age", "city", "gender", "is_active", "about",
        "latitude", "longitude", "interesting_gender", "coordinates"
    ] = Field(..., description="Название изменяемого поля")
    value: Union[str, int, Coordinates] = Field(..., description="Новое значение поля")

    @model_validator(mode='after')
    def validate_field_name_matches_value_type(self) -> 'UpdateFieldRequest':
        if self.field_name == 'city' and not isinstance(self.value, str):
            raise ValueError('Поле "city" должно быть строкой')
        if self.field_name == 'coordinates' and not isinstance(self.value, Coordinates):
            raise ValueError('Поле "coordinates" должно быть объектом Coordinates')
        return self

    class Config:
        schema_extra = {
            "example": {
                "field_name": "city",
                "value": "Санкт-Петербург"
            }
        }

class SaveProfileResponse(BaseModel):
    profile_id: int = Field(..., description="Идентификатор созданного или обновлённого профиля")

    class Config:
        schema_extra = {
            "example": {
                "profile_id": 123
            }
        }

class GetProfileResponse(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    name: str = Field(..., description="Имя пользователя")
    gender: str = Field(..., description="Пол пользователя")
    city: Optional[str] = Field(None, description="Город пользователя")
    age: int = Field(..., description="Возраст")
    interesting_gender: str = Field(..., description="Интересующий пол")
    about: Optional[str] = Field(None, description="Описание профиля")
    is_active: bool = Field(..., description="Активен ли профиль")

    class Config:
        schema_extra = {
            "example": {
                "user_id": 101,
                "name": "Дмитрий",
                "gender": "male",
                "city": "Казань",
                "age": 30,
                "interesting_gender": "female",
                "about": "Инженер, люблю горные походы.",
                "is_active": True
            }
        }
