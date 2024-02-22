import pytest
from starlette import status


from controller.jwt_token import get_current_user
from models import User, Ad, Comment
from main import app
from fastapi.testclient import TestClient
from database import get_db, session_factory, engine


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = session_factory(bind=connection)
    session.begin_nested()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    session.rollback()
    session.close()
    transaction.rollback()
    connection.close()


client = TestClient(app)


@pytest.fixture(scope="function")
def populate_users(db_session):
    u1 = User(email="a@b.com", hashed_password="pass1")
    u2 = User(email="c@d.com", hashed_password="pass2")
    db_session.add_all([u1, u2])
    db_session.commit()


@pytest.fixture(scope="function")
def auth_with_user1(db_session, populate_users):
    u1 = db_session.query(User).filter(User.email == "a@b.com").first()
    app.dependency_overrides[get_current_user] = lambda: u1.id
    yield u1
    app.dependency_overrides[get_current_user] = get_current_user


@pytest.fixture(scope="function")
def auth_with_user2(db_session, populate_users):
    u2 = db_session.query(User).filter(User.email == "c@d.com").first()
    app.dependency_overrides[get_current_user] = lambda: u2.id
    yield u2
    app.dependency_overrides[get_current_user] = get_current_user


def test_create_user(db_session):
    response = client.post("/register/", json={"email": "joe@doe.com", "password": "secret"})
    assert response.status_code == 201
    user = db_session.query(User).filter(User.email == "joe@doe.com").first()
    assert user is not None


def test_duplicate_user_email(db_session):
    client.post("/register/", json={"email": "joe@doe.com", "password": "secret"})
    response = client.post("/register/", json={"email": "joe@doe.com", "password": "secret"})
    assert response.status_code == 400


def test_get_token_correct_credentials(db_session):
    client.post("/register/", json={"email": "joe@doe.com", "password": "secret"})
    response = client.post("/token", data={"username": "joe@doe.com", "password": "secret"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("access_token") is not None
    assert response.json().get("token_type") == "bearer"


def test_get_token_wrong_credentials(db_session):
    client.post("/register/", json={"email": "joe@doe.com", "password": "secret"})
    response = client.post("/token", data={"username": "joe@doe.com", "password": "test_password"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json().get("access_token") is None
    assert response.json().get("token_type") is None


def test_add_ad_no_auth(db_session):
    ad_create_data = {"title": "Test Ad", "description": "Test Description"}
    response = client.post("/ads/", json=ad_create_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_ad(db_session, auth_with_user1):
    ad_create_data = {"title": "Test Ad", "description": "Test Description"}
    response = client.post("/ads/", json=ad_create_data)
    assert response.status_code == status.HTTP_201_CREATED
    ad_id = response.json()["id"]
    ad = db_session.query(Ad).filter(Ad.id == ad_id).first()
    assert ad is not None
    assert ad.title == "Test Ad" and ad.description == "Test Description" and ad.owner_id == auth_with_user1.id


@pytest.fixture(scope="function")
def populate_ads(db_session, populate_users):
    u1 = db_session.query(User).filter(User.email == "a@b.com").first()
    u2 = db_session.query(User).filter(User.email == "c@d.com").first()
    ad1 = Ad(title="Ad 1", description="1st Ad", owner_id=u1.id)
    ad2 = Ad(title="Ad 2", description="2nd Ad", owner_id=u2.id)
    db_session.add_all([ad1, ad2])
    db_session.commit()


def test_find_all_ads(db_session, populate_ads):
    response = client.get("/ads/")
    assert response.status_code == status.HTTP_200_OK
    ad1, ad2 = None, None
    for ad in response.json():
        if ad["title"] == "Ad 1":
            ad1 = ad
        if ad["title"] == "Ad 2":
            ad2 = ad
    assert ad1 is not None and ad2 is not None


def invalid_ad_id(db_session):
    ids = [ad.id for ad in db_session.query(Ad).all()]
    return max(ids) + 1 if len(ids) > 0 else 1


def test_update_non_existing_ad(db_session, populate_ads, auth_with_user1):
    non_existing = invalid_ad_id(db_session)
    response = client.put(f"/ads/{non_existing}", json={"title": "Updated title", "description": "Updated description"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_ad_authorized(db_session, populate_ads, auth_with_user1):
    ad = db_session.query(Ad).filter(Ad.title == "Ad 1").first()
    response = client.put(f"/ads/{ad.id}", json={"title": "Updated title", "description": "Updated description"})
    assert response.status_code == status.HTTP_200_OK

    updated = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert updated.title == "Updated title" and updated.description == "Updated description"


def test_update_ad_un_authorized(db_session, populate_ads, auth_with_user2):
    ad = db_session.query(Ad).filter(Ad.title == "Ad 1").first()
    response = client.put(f"/ads/{ad.id}", json={"title": "Updated title"})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_ad_authorized(db_session, auth_with_user1):
    ad = Ad(title="Test Ad", description="An Ad", owner_id=auth_with_user1.id)
    db_session.add(ad)
    commenter = User(email="random@guy.com", hashed_password="secret")
    db_session.add(commenter)
    db_session.commit()
    db_session.refresh(ad)
    db_session.refresh(commenter)
    comment = Comment(ad_id=ad.id, owner_id=commenter.id, text="Wow!")
    db_session.add(comment)
    db_session.commit()
    response = client.delete(f"/ads/{ad.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    retrieved_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert retrieved_ad is None
    retrieved_comment = db_session.query(Comment).filter(Comment.id == comment.id).first()
    assert retrieved_comment is None


def test_delete_ad_un_authorized(db_session, populate_ads, auth_with_user2):
    ad = db_session.query(Ad).filter(Ad.title == "Ad 1").first()
    response = client.delete(f"/ads/{ad.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_add_comment_no_auth(db_session, populate_ads):
    ad = db_session.query(Ad).first()
    response = client.post(f"/ads/{ad.id}/comments/", json={"text": "Great!"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_comment(db_session, populate_ads, auth_with_user1):
    ad = db_session.query(Ad).first()
    response = client.post(f"/ads/{ad.id}/comments/", json={"text": "Great!"})
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["owner_id"] == auth_with_user1.id
    assert body["ad_id"] == ad.id


def test_add_duplicate_comment(db_session, populate_ads, auth_with_user1):
    ad = db_session.query(Ad).first()
    client.post(f"/ads/{ad.id}/comments/", json={"text": "Great!"})
    response = client.post(f"/ads/{ad.id}/comments/", json={"text": "Excellent!"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_add_comment_to_invalid_ad(db_session, populate_ads, auth_with_user1):
    invalid_id = invalid_ad_id(db_session)
    response = client.post(f"/ads/{invalid_id}/comments/", json={"text": "Great!"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_find_all_comments(db_session):
    ad = Ad(title="Ad 1", description="1st Ad")
    db_session.add(ad)
    db_session.commit()
    db_session.refresh(ad)
    users = [User(email=str(i), hashed_password=str(i)) for i in range(10)]
    db_session.add_all(users)
    db_session.commit()
    for user in users:
        db_session.refresh(user)
        comment = Comment(ad_id=ad.id, owner_id=user.id, text=user.email)
        db_session.add(comment)
    db_session.commit()
    response = client.get(f"/ads/{ad.id}/comments/")
    assert response.status_code == status.HTTP_200_OK
    assert set([str(i) for i in range(10)]) == set([item['text'] for item in response.json()])


def test_find_all_comments_for_invalid_ad(db_session):
    invalid_id = invalid_ad_id(db_session)
    response = client.get(f"/ads/{invalid_id}/comments/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
