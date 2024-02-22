from sqlalchemy.exc import IntegrityError
import models
from database import session_factory
from repository import ad_repository
from service.exception.entity_not_found import EntityNotFound
from service.exception.unauthorized_action import UnauthorizedAction
from sqlalchemy.orm import Session


def create_ad(db_ad: models.Ad, db: Session):
    db.add(db_ad)
    db.commit()
    db.refresh(db_ad)
    return db_ad


def find_all_ads(db: Session):
    return db.query(models.Ad).all()


def add_comment(db_comment: models.Comment, db: Session):
    with db.begin_nested():
        if not ad_repository.find_ad_by_id(db_comment.ad_id, db):
            raise EntityNotFound()
        db.add(db_comment)
        try:
            db.commit()
        except IntegrityError:
            raise UserDuplicateCommentException()
    db.refresh(db_comment)
    return db_comment


def find_all_comments_of_ad(ad_id: int, db: Session):
    ad = ad_repository.find_ad_by_id_with_comments(ad_id, db)
    if not ad:
        raise EntityNotFound()
    return ad.comments


def delete_ad(ad_id: int, current_user, db: Session):
    with db.begin_nested():
        ad = ad_repository.find_ad_by_id(ad_id, db)
        if not ad:
            raise EntityNotFound()
        if ad.owner_id != current_user:
            raise UnauthorizedAction()
        ad_repository.delete(ad, db)
        db.commit()


def update_ad(ad_id: int, title: str, description: str, current_user: int, db: Session):
    with db.begin_nested():
        db_ad = ad_repository.find_ad_by_id(ad_id, db)
        if not db_ad:
            raise EntityNotFound()
        if db_ad.owner_id != current_user:
            raise UnauthorizedAction()
        if title is not None:
            db_ad.title = title
        if description is not None:
            db_ad.description = description
        db.commit()
    db.refresh(db_ad)
    return db_ad


class UserDuplicateCommentException(Exception):
    pass
