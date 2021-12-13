from datetime import datetime

from pydantic import BaseModel, Field, validator
from enum import Enum
from bson import ObjectId
from typing import Optional

from tools import generate_hash_pass


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class RoleEnum(str, Enum):
    admin = 'admin'
    dev = 'dev'
    simple_mortal = 'simple_mortal'


class UserModel(BaseModel):
    first_name: str
    last_name: str
    role: RoleEnum
    is_active: bool
    last_login: datetime
    created_at: datetime

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class CreateUserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    first_name: str = Field(...)
    last_name: str = Field(...)
    role: RoleEnum = Field(...)
    is_active: bool = False
    last_login: datetime = None
    created_at: datetime = Field(datetime.utcnow())
    hashed_pass: str = Field(...)

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Snow",
                "role": "simple_mortal",
                "hashed_pass": "hashed_pass"
            }
        }

    @validator("hashed_pass", always=True)
    def validate_hashed_pass(cls, value):
        new_value = generate_hash_pass(value)
        return new_value


class UpdateUserModel(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[RoleEnum]

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Snow",
                "role": "simple_mortal"
            }
        }


class LoginModel(BaseModel):
    first_name: str
    last_name: str
    hashed_pass: str
