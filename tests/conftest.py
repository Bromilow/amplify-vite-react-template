import pytest

from app import create_app, db as _db


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

