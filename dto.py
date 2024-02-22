from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class AdBase(BaseModel):
    title: str
    description: str


class AdCreate(AdBase):
    pass


class Ad(AdBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class AdUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    owner_id: int
    ad_id: int
    text: str

    class Config:
        from_attributes = True

