from unittest.mock import patch

from audiodesk.providers.base import Candidate, SearchQuery
from audiodesk.providers.discogs import DiscogsProvider


def make_provider() -> DiscogsProvider:
    return DiscogsProvider("test-token")


def test_available_requires_token():
    assert DiscogsProvider("").available() == (False, "Kein API-Key hinterlegt.")
    ok, _why = DiscogsProvider("abc").available()
    assert ok is True


def test_search_splits_combined_title_heuristically():
    provider = make_provider()
    with patch.object(provider, "_get", return_value={"results": [
        {"id": 1, "title": "Rick Astley - Never Gonna Give You Up", "year": "1987"},
    ]}):
        candidates = provider.search(SearchQuery(title="Never Gonna Give You Up"))
    assert candidates[0].artist == "Rick Astley"
    assert candidates[0].title == "Never Gonna Give You Up"
    assert candidates[0].year == 1987


def test_search_without_dash_keeps_whole_title_no_artist():
    provider = make_provider()
    with patch.object(provider, "_get", return_value={"results": [
        {"id": 1, "title": "Untitled Compilation"},
    ]}):
        candidates = provider.search(SearchQuery(title="Untitled"))
    assert candidates[0].artist == ""
    assert candidates[0].title == "Untitled Compilation"


def test_details_uses_release_endpoint_for_clean_artist_title():
    # Der Suchtreffer haette "Emerson, Lake & Palmer - Karn Evil 9" am
    # ersten " - " falsch aufgetrennt (der Interpretenname selbst enthaelt
    # keinen Bindestrich hier, aber das Prinzip: die Suche ist nur eine
    # Heuristik) - details() muss die sauberen Felder aus dem Release
    # bevorzugen, nicht die aus der Suche uebernommenen Werte.
    provider = make_provider()
    candidate = Candidate(source="discogs", external_id="249504",
                          title="Heuristic Title", artist="Heuristic Artist")
    with patch.object(provider, "_get", return_value={
        "title": "Never Gonna Give You Up",
        "artists": [{"name": "Rick Astley"}],
        "year": 1987,
        "images": [{"resource_url": "https://example.com/cover.jpg"}],
    }):
        info = provider.details(candidate)
    assert info.title == "Never Gonna Give You Up"
    assert info.artist == "Rick Astley"
    assert info.year == 1987
    assert info.cover_url == "https://example.com/cover.jpg"


def test_details_joins_multiple_artists():
    provider = make_provider()
    candidate = Candidate(source="discogs", external_id="1", title="x", artist="y")
    with patch.object(provider, "_get", return_value={
        "title": "Karn Evil 9",
        "artists": [{"name": "Emerson, Lake & Palmer"}, {"name": "Guest"}],
        "year": 1973,
    }):
        info = provider.details(candidate)
    assert info.artist == "Emerson, Lake & Palmer, Guest"


def test_details_falls_back_to_search_heuristic_on_network_error():
    provider = make_provider()
    candidate = Candidate(source="discogs", external_id="1", title="Fallback Title",
                          artist="Fallback Artist", year=1999,
                          cover_url="https://example.com/old.jpg")
    with patch.object(provider, "_get", side_effect=RuntimeError("network error")):
        info = provider.details(candidate)
    assert info.title == "Fallback Title"
    assert info.artist == "Fallback Artist"
    assert info.year == 1999
    assert info.cover_url == "https://example.com/old.jpg"


def test_details_falls_back_when_release_has_no_artists_field():
    provider = make_provider()
    candidate = Candidate(source="discogs", external_id="1", title="x",
                          artist="Fallback Artist")
    with patch.object(provider, "_get", return_value={"title": "Some Title"}):
        info = provider.details(candidate)
    assert info.artist == "Fallback Artist"
    assert info.title == "Some Title"
