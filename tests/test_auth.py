from app import create_app


def test_app_boots():
    app = create_app("test")
    client = app.test_client()
    assert client.get("/api/health").status_code == 200
