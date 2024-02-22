from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import dto
import models
from controller.jwt_token import get_current_user
from database import get_db
from service.exception.entity_not_found import EntityNotFound
from service.exception.unauthorized_action import UnauthorizedAction
from service import ad_service

router = APIRouter()


@router.post("/ads/", response_model=dto.Ad, status_code=status.HTTP_201_CREATED)
async def create_ad(ad: dto.AdCreate, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    db_ad = models.Ad(**ad.dict(), owner_id=user_id)
    return ad_service.create_ad(db_ad, db)


@router.get("/ads/", response_model=List[dto.Ad])
async def read_ads(db: Session = Depends(get_db)):
    return ad_service.find_all_ads(db)


@router.put("/ads/{ad_id}", response_model=dto.Ad)
async def update_ad(ad_id: int, ad: dto.AdUpdate, current_user: int = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    try:
        db_ad = ad_service.update_ad(ad_id, ad.title, ad.description, current_user, db)
    except UnauthorizedAction:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this ad")
    return db_ad


@router.delete("/ads/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(ad_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ad_service.delete_ad(ad_id, current_user, db)
    except UnauthorizedAction:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this ad")


@router.post("/ads/{ad_id}/comments/", response_model=dto.Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(ad_id: int, comment: dto.CommentCreate,
                         user_id: int = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    db_comment = models.Comment(**comment.dict(), ad_id=ad_id, owner_id=user_id)
    try:
        return ad_service.add_comment(db_comment, db)
    except EntityNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")
    except ad_service.UserDuplicateCommentException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already commented on this ad")


@router.get("/ads/{ad_id}/comments/", response_model=List[dto.Comment])
async def read_comments(ad_id: int, db: Session = Depends(get_db)):
    return ad_service.find_all_comments_of_ad(ad_id, db)
