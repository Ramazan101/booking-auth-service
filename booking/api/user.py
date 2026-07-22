from booking.database.models import User
from booking.database.schema import UserCreate
from booking.database.db import SessionLocal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from typing import List

user_router = APIRouter(prefix="/users", tags=["Users"])

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@user_router.get("/", response_model=List[UserCreate])
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@user_router.get("/{user_id}/", response_model=UserCreate)
async def detail_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail = "User not found")
    return db_user

@user_router.put("/{user_id}/", response_model=dict)
async def update_user(user_id: int, user: UserCreate,db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code=401, detail="User not authorization")
    for user_key, user_value in user.dict().items():
        setattr(user_db, user_key, user_value)
    db.commit()
    db.refresh(user_db)
    return {"message": "Category change"}

@user_router.delete("/{user_id}/", response_model=dict)
async def delete_user_in_db(user_id: int, db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user_db)
    db.commit()
    return {"message": "del user"}