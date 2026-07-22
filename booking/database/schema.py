from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr
from .models import RoleChoices

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    user_name: str
    phone_number: Optional[str] = None
    status: RoleChoices = RoleChoices.simple_user

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    user_name: str
    phone_number: Optional[str] = None
    status: RoleChoices
    date_registered: date

    class Config:
        from_attributes = True

class UserRegisterSchema(BaseModel):
    username: str
    password: str


class UserAuthThreeObj(BaseModel):
    id: int
    username: str
    email: str
    status: str

    class Config:
        from_attributes = True