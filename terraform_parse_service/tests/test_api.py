import pytest

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "OUTPUT_DIR", tmp_path)
    return app_module.create_app().test_client()


VALID_BODY = {
    "payload": {
        "properties": {
            "aws-region": "eu-west-1",
            "acl": "private",
            "bucket-name": "tripla-bucket",
        }
    }
}


def test_render_success(client, tmp_path):
    resp = client.post("/api/v1/render", json=VALID_BODY)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["filename"] == "tripla-bucket.tf"
    assert 'resource "aws_s3_bucket" "this"' in data["terraform"]
    # File persisted to the output directory too.
    assert (tmp_path / "tripla-bucket.tf").read_text() == data["terraform"]


def test_render_rejects_invalid_acl(client):
    body = {
        "payload": {
            "properties": {
                "aws-region": "eu-west-1",
                "acl": "not-an-acl",
                "bucket-name": "tripla-bucket",
            }
        }
    }
    resp = client.post("/api/v1/render", json=body)
    assert resp.status_code == 400
    assert "acl must be one of" in resp.get_json()["error"]


def test_render_rejects_missing_properties(client):
    resp = client.post("/api/v1/render", json={"payload": {"properties": {}}})
    assert resp.status_code == 400
    assert "missing required properties" in resp.get_json()["error"]


def test_render_rejects_non_json_body(client):
    resp = client.post(
        "/api/v1/render", data="not json", content_type="text/plain"
    )
    assert resp.status_code == 400
    assert "valid JSON" in resp.get_json()["error"]


def test_render_write_failure_returns_500(client, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(app_module.Path, "write_text", boom)
    resp = client.post("/api/v1/render", json=VALID_BODY)
    assert resp.status_code == 500
    assert "persist" in resp.get_json()["error"]


def test_get_on_render_is_405(client):
    assert client.get("/api/v1/render").status_code == 405


def test_unknown_route_is_404_json(client):
    resp = client.get("/nope")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not found"


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"