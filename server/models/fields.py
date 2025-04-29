from pydantic import BaseModel, model_validator
from typing import Union

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class UpdateField(BaseModel):
    user_id: int
    field_name: str
    value: Union[str, Coordinates]

    @model_validator(mode='after')
    def validate_field_name_matches_value_type(self) -> 'UpdateField':
        if self.field_name == 'city' and not isinstance(self.value, str):
            raise ValueError('When field_name is "city", value must be a string')
        
        if self.field_name == 'coordinates' and not isinstance(self.value, Coordinates):
            raise ValueError('When field_name is "coordinates", value must be a Coordinates object')
        
        return self
