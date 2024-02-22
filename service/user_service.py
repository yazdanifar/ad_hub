from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from database import session_factory
import models
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(username, password, db: Session):
    user = db.query(models.User).filter(models.User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    expires_delta = timedelta(minutes=30)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": str(user.id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_user(user, db: Session):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise DuplicatedUserException()
    return db_user


class InvalidTokenException(Exception):
    pass


class DuplicatedUserException(Exception):
    pass
