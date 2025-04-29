from pydantic import BaseModel, model_validator
from typing import Optional

class ProfileBase(BaseModel):
    user_id: int
    name: str
    gender: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    age: int
    interesting_gender: str
    about: str

    @model_validator(mode="after")
    def check_location(self) -> 'ProfileBase':
        if not self.city and (self.latitude is None or self.longitude is None):
            raise ValueError("Укажите либо город, либо координаты (широту и долготу).")
        return self

class ProfileId(BaseModel):
    profile_id: int

class ToggleActive(BaseModel):
    user_id: int
    is_active: bool
