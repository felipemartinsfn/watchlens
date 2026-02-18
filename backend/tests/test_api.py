"""
API tests for WatchLens backend.
conftest.py sets DATABASE_URL=sqlite:///:memory: before any import.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    # All imports happen here, after conftest.py already set env vars
    from app.core.database import Base, engine, get_db, SessionLocal
    from app.main import app
    from app.models.watch import Brand, Collection, WatchReference

    # Create schema
    Base.metadata.create_all(bind=engine)

    # Seed
    db = SessionLocal()
    brand = Brand(name="TestBrand", slug="testbrand", country="Switzerland", founded_year=1900)
    db.add(brand); db.flush()
    coll = Collection(brand_id=brand.id, name="TestCollection", slug="testbrand-testcollection")
    db.add(coll); db.flush()
    db.add(WatchReference(
        collection_id=coll.id, name="Test Watch", slug="testbrand-test-watch-ref001",
        reference_number="REF001", is_published=True, watch_style="diver", era="modern",
        dial_color="Black", case_material="Steel", case_diameter_mm=40.0,
        movement_type="automatic", view_count=10,
    ))
    db.add(WatchReference(
        collection_id=coll.id, name="Another Diver", slug="testbrand-another-diver-ref002",
        reference_number="REF002", is_published=True, watch_style="diver", era="modern",
        dial_color="Blue", case_material="Steel", case_diameter_mm=42.0,
        movement_type="automatic", view_count=5,
    ))
    db.commit(); db.close()

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "WatchLens API"

def test_health(client):
    assert client.get("/health").json()["status"] == "healthy"

def test_list_watches(client):
    r = client.get("/api/v1/watches/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2

def test_search_by_query(client):
    r = client.get("/api/v1/watches/?q=Test")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert any("Test" in w["name"] for w in r.json()["results"])

def test_filter_by_style(client):
    r = client.get("/api/v1/watches/?watch_styles=diver")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

def test_filter_by_era(client):
    r = client.get("/api/v1/watches/?eras=modern")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

def test_filter_by_dial_color(client):
    r = client.get("/api/v1/watches/?dial_colors=Black")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

def test_filter_by_diameter(client):
    r = client.get("/api/v1/watches/?diameter_min=39&diameter_max=41")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    for w in data["results"]:
        assert 39 <= w["case_diameter_mm"] <= 41

def test_get_watch_by_slug(client):
    r = client.get("/api/v1/watches/testbrand-test-watch-ref001")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Watch"

def test_get_watch_not_found(client):
    assert client.get("/api/v1/watches/nonexistent-xyz").status_code == 404

def test_get_similar_watches(client):
    r = client.get("/api/v1/watches/testbrand-test-watch-ref001/similar")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        assert 0 <= item["score"] <= 100

def test_featured_watches(client):
    r = client.get("/api/v1/watches/featured")
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_trending_watches(client):
    r = client.get("/api/v1/watches/trending?style=diver")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_list_brands(client):
    r = client.get("/api/v1/brands/")
    assert r.status_code == 200
    assert any(b["name"] == "TestBrand" for b in r.json())

def test_get_brand_by_slug(client):
    r = client.get("/api/v1/brands/testbrand")
    assert r.status_code == 200
    assert r.json()["name"] == "TestBrand"

def test_get_brand_collections(client):
    r = client.get("/api/v1/brands/testbrand/collections")
    assert r.status_code == 200
    assert any(c["name"] == "TestCollection" for c in r.json())

def test_filter_options(client):
    r = client.get("/api/v1/filters/options")
    assert r.status_code == 200
    data = r.json()
    assert all(k in data for k in ["brands", "watch_styles", "dial_colors", "diameter_range"])
    assert "diver" in data["watch_styles"]

def test_autocomplete(client):
    r = client.get("/api/v1/search/autocomplete?q=Test")
    assert r.status_code == 200
    labels = [s["label"] for s in r.json()["suggestions"]]
    assert any("Test" in l for l in labels)

def test_autocomplete_by_reference(client):
    r = client.get("/api/v1/search/autocomplete?q=REF001")
    assert r.status_code == 200
    assert len(r.json()["suggestions"]) >= 1

def test_image_search_invalid_type(client):
    r = client.post("/api/v1/search/image", files={"file": ("t.txt", b"x", "text/plain")})
    assert r.status_code == 400

def test_pagination(client):
    r = client.get("/api/v1/watches/?page=1&per_page=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 1
    assert data["total_pages"] >= 2

def test_pagination_page2(client):
    r1 = client.get("/api/v1/watches/?page=1&per_page=1")
    r2 = client.get("/api/v1/watches/?page=2&per_page=1")
    assert r1.status_code == r2.status_code == 200
    if r1.json()["results"] and r2.json()["results"]:
        assert r1.json()["results"][0]["id"] != r2.json()["results"][0]["id"]
