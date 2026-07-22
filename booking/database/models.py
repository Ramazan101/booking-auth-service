from enum import Enum as PyEnum
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Integer, String, Enum, Date, ForeignKey, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

class RoleChoices(str, PyEnum):
    hotel_owner = "hotel_owner"
    simple_user = "simple_user"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer,
                                    primary_key=True,
                                    autoincrement=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    user_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    status: Mapped[RoleChoices] = mapped_column(Enum(RoleChoices),
                                              default=RoleChoices.simple_user)
    date_registered: Mapped[date] = mapped_column(Date,
                                                  default=date.today)

    refresh_tokens: Mapped[List['RefreshToken']] = relationship('RefreshToken',
                                                                back_populates='user_token',
                                                                cascade='all, delete-orphan'
                                                                )

    def __str__(self) -> str:
        return f"{self.username}"


class RefreshToken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[int] = mapped_column(Integer,
                                    primary_key=True,
                                    autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user_token: Mapped[User] = relationship(User,
                                            back_populates="refresh_tokens")
    token: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime,
                                                 default=datetime.utcnow)