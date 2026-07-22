from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from booking.config.config import (
    ACCESS_TOKEN_LIFETIME,
    ALGORITHM,
    REFRESH_TOKEN_LIFETIME,
    SECRET_KEY,
)
from booking.database.db import SessionLocal
from booking.database.models import RefreshToken, User
from booking.database.schema import (
    UserAuthThreeObj,
    UserCreate,
    UserRegisterSchema,
)

# Настройка шифрования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Заголовок Authorization: Bearer <token>
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login/")

auth_router = APIRouter(prefix='/auth', tags=['Auth'])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_LIFETIME)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(days=REFRESH_TOKEN_LIFETIME)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_token_data(user: User):
    role_val = user.status.value if hasattr(user.status, 'value') else user.status
    return {"sub": str(user.id), "username": user.username, "role": role_val}


# Зависимость для извлечения текущего аутентифицированного пользователя
async def get_current_user(token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


### Endpoints

@auth_router.post('/register/', response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail='There is an username like this.')

    email = db.query(User).filter(User.email == user.email).first()
    if email:
        raise HTTPException(status_code=400, detail='There is an email like this.')

    hash_password = get_password_hash(user.password)

    user_data = User(
        username=user.username,
        email=user.email,
        user_name=user.user_name,
        phone_number=user.phone_number,
        status=user.status,
        password_hash=hash_password,
    )

    db.add(user_data)
    db.commit()
    db.refresh(user_data)

    return {'message': 'You are registered'}


@auth_router.post("/login/", response_model=dict)
async def login(user: UserRegisterSchema, db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.username == user.username).first()

    # Сравниваем с password_hash!
    if not user_db or not verify_password(user.password, user_db.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your information is not correct :("
        )

    token_data = get_token_data(user_db)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    token_db = RefreshToken(user_id=user_db.id, token=refresh_token)
    db.add(token_db)
    db.commit()

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'Bearer'}


@auth_router.post("/logout/")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not stored:
        raise HTTPException(status_code=401, detail="Token not found")

    db.delete(stored)
    db.commit()
    return {"message": "You logged out"}


@auth_router.post("/refresh/")
async def refresh_jwt(refresh_token: str, db: Session = Depends(get_db)):
    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

    if not stored:
        raise HTTPException(status_code=401, detail="Token not found")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    access_token = create_access_token({"sub": user_id})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@auth_router.get("/verify/", response_model=UserAuthThreeObj)
async def verify_access_token(current_user: User = Depends(get_current_user)):
    """
    Возвращает информацию о текущем авторизованном пользователе
    по переданному в заголовке Access-токену.
    """
    return current_user