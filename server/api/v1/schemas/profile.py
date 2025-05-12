from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union, Literal

class SaveProfileRequest(BaseModel):
    name: str = Field(..., description="User's name")
    gender: str = Field(..., description="User's gender")
    city: Optional[str] = Field(None, description="User's city")
    latitude: Optional[float] = Field(None, description="Latitude (required if city is not provided)")
    longitude: Optional[float] = Field(None, description="Longitude (required if city is not provided)")
    age: int = Field(..., description="User's age")
    interesting_gender: str = Field(..., description="Gender(s) the user is interested in")
    about: str = Field(..., description="User's bio or description")

    @model_validator(mode="after")
    def check_location(self) -> 'SaveProfileRequest':
        if not self.city and (self.latitude is None or self.longitude is None):
            raise ValueError("Either city or both latitude and longitude must be provided.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Alice",
                "gender": "female",
                "city": "Prague",
                "latitude": None,
                "longitude": None,
                "age": 28,
                "interesting_gender": "male",
                "about": "I love traveling and reading books."
            }
        }
    }

class ToggleActiveRequest(BaseModel):
    is_active: bool = Field(..., description="Indicates whether the profile is active")

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_active": True
            }
        }
    }

class Coordinates(BaseModel):
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")

    model_config = {
        "json_schema_extra": {
            "example": {
                "latitude": 55.7558,
                "longitude": 37.6173
            }
        }
    }

class UpdateFieldRequest(BaseModel):
    field_name: Literal[
        "name", "age", "city", "gender", "is_active", "about",
        "latitude", "longitude", "interesting_gender", "coordinates"
    ] = Field(..., description="The name of the field to be updated")
    value: Union[str, int, Coordinates] = Field(..., description="New value for the field")

    @model_validator(mode='after')
    def validate_field_name_matches_value_type(self) -> 'UpdateFieldRequest':
        if self.field_name == 'city' and not isinstance(self.value, str):
            raise ValueError('The "city" field must be a string')
        if self.field_name == 'coordinates' and not isinstance(self.value, Coordinates):
            raise ValueError('The "coordinates" field must be a Coordinates object')
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field_name": "city",
                "value": "Saint Petersburg"
            }
        }
    }

class SaveProfileResponse(BaseModel):
    profile_id: int = Field(..., description="Unique identifier of the created or updated profile")

    model_config = {
        "json_schema_extra": {
            "example": {
                "profile_id": 1
            }
        }
    }

class GetProfileResponse(BaseModel):
    user_id: int = Field(..., description="User ID")
    name: str = Field(..., description="User's name")
    gender: str = Field(..., description="User's gender")
    city: Optional[str] = Field(None, description="User's city")
    age: int = Field(..., description="User's age")
    interesting_gender: str = Field(..., description="Gender(s) the user is interested in")
    about: Optional[str] = Field(None, description="User's bio or description")
    is_active: bool = Field(..., description="Indicates if the profile is active")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "name": "Alice",
                "gender": "female",
                "city": "Prague",
                "age": 20,
                "interesting_gender": "male",
                "about": "I love traveling and reading books.",
                "is_active": True
            }
        }
    }
