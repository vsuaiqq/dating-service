from pydantic import BaseModel, model_validator
from typing import Optional, Union, Literal

class SaveProfileRequest(BaseModel):
    name: str
    gender: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    age: int
    interesting_gender: str
    about: str

    @model_validator(mode="after")
    def check_location(self) -> 'SaveProfileRequest':
        if not self.city and (self.latitude is None or self.longitude is None):
            raise ValueError("Укажите либо город, либо координаты (широту и долготу).")
        return self

class ToggleActiveRequest(BaseModel):
    is_active: bool

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class UpdateFieldRequest(BaseModel):
    field_name: Literal["name", "age", "city", "gender", "is_active", "about", "latitude", "longitude", "interesting_gender", "coordinates"]
    value: Union[str, int, Coordinates]

    @model_validator(mode='after')
    def validate_field_name_matches_value_type(self) -> 'UpdateFieldRequest':
        if self.field_name == 'city' and not isinstance(self.value, str):
            raise ValueError('When field_name is "city", value must be a string')
        
        if self.field_name == 'coordinates' and not isinstance(self.value, Coordinates):
            raise ValueError('When field_name is "coordinates", value must be a Coordinates object')
        
        return self

class SaveProfileResponse(BaseModel):
    profile_id: int

class GetProfileResponse(BaseModel):
    user_id: int
    name: str
    gender: str
    city: Optional[str]
    age: int
    interesting_gender: str
    about: Optional[str]
    is_active: bool
