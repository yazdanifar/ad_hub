from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
import dto
from database import get_db

from service.user_service import create_user, create_access_token, DuplicatedUserException

router = APIRouter()


@router.post("/register", response_model=dto.User, status_code=status.HTTP_201_CREATED)
def register_user(user: dto.UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(user, db)
    except DuplicatedUserException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return new_user


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    access_token = create_access_token(form_data.username, form_data.password, db)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}

