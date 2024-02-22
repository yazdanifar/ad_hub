from sqlalchemy import select, update
from sqlalchemy.orm import subqueryload

import models


def find_ad_by_id(ad_id: int, db):
    ad = db.execute(select(models.Ad).filter(models.Ad.id == ad_id)).scalar()
    return ad


def find_ad_by_id_with_comments(ad_id: int, db):
    return db.query(models.Ad).filter(models.Ad.id == ad_id).options(
        subqueryload(models.Ad.comments)
    ).first()


def delete(db_ad: models.Ad, db):
    db.delete(db_ad)
