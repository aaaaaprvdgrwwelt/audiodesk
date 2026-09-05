from dataclasses import dataclass, field

from audiodesk.library import CHAPTER, TRACK
from audiodesk.matcher import MatchConfig, collect_candidates, score_candidate
from audiodesk.providers.base import (
    Candidate, MetadataProvider, SearchQuery, artist_similarity,
)


def test_artist_similarity_exact_match():
    assert artist_similarity("Daft Punk", "daft punk") == 1.0


def test_artist_similarity_empty_side_is_zero():
    assert artist_similarity("", "Daft Punk") == 0.0


def test_score_candidate_full_match_is_100():
    query = SearchQuery(title="Get Lucky", artist="Daft Punk", album="Random Access Memories")
    candidate = Candidate(source="musicbrainz", external_id="1", title="Get Lucky",
                          artist="Daft Punk", album="Random Access Memories")
    assert score_candidate(query, candidate) == 100


def test_score_candidate_title_only_uses_60_percent_weight():
    query = SearchQuery(title="Get Lucky", artist="", album="")
    candidate = Candidate(source="musicbrainz", external_id="1", title="Get Lucky",
                          artist="Daft Punk", album="Random Access Memories")
    assert score_candidate(query, candidate) == 60


def test_score_candidate_album_only_scores_when_both_sides_have_one():
    with_album_query = SearchQuery(title="Get Lucky", artist="", album="Random Access Memories")
    candidate = Candidate(source="musicbrainz", external_id="1", title="Get Lucky",
                          artist="", album="Random Access Memories")
    without_album_query = SearchQuery(title="Get Lucky", artist="", album="")
    candidate_no_album = Candidate(source="musicbrainz", external_id="1",
                                   title="Get Lucky", artist="")
    assert score_candidate(with_album_query, candidate) > \
        score_candidate(without_album_query, candidate_no_album)


def test_score_candidate_caps_at_100():
    query = SearchQuery(title="X", artist="Y", album="Z")
    candidate = Candidate(source="musicbrainz", external_id="1", title="X",
                          artist="Y", album="Z")
    assert score_candidate(query, candidate) <= 100


@dataclass
class _FakeProvider(MetadataProvider):
    name: str = "fake"
    supports_track: bool = False
    supports_chapter: bool = False
    results: list = field(default_factory=list)

    def available(self):
        return True, ""

    def search(self, query, limit=10):
        return list(self.results)


def test_collect_candidates_skips_provider_not_supporting_track_kind():
    provider = _FakeProvider(supports_track=False, supports_chapter=True,
                             results=[Candidate(source="fake", external_id="1",
                                                 title="Should not appear")])
    config = MatchConfig(providers=[provider])
    query = SearchQuery(title="Get Lucky", kind=TRACK)
    assert collect_candidates(query, config) == []


def test_collect_candidates_skips_provider_not_supporting_chapter_kind():
    provider = _FakeProvider(supports_track=True, supports_chapter=False,
                             results=[Candidate(source="fake", external_id="1",
                                                 title="Should not appear")])
    config = MatchConfig(providers=[provider])
    query = SearchQuery(title="Chapter 1", kind=CHAPTER)
    assert collect_candidates(query, config) == []


def test_collect_candidates_includes_matching_provider():
    provider = _FakeProvider(supports_track=True, supports_chapter=False,
                             results=[Candidate(source="fake", external_id="1",
                                                 title="Get Lucky")])
    config = MatchConfig(providers=[provider])
    query = SearchQuery(title="Get Lucky", kind=TRACK)
    candidates = collect_candidates(query, config)
    assert len(candidates) == 1
    assert candidates[0].title == "Get Lucky"


def test_collect_candidates_skips_unavailable_provider():
    class Unavailable(_FakeProvider):
        def available(self):
            return False, "kein API-Key"
    provider = Unavailable(supports_track=True,
                           results=[Candidate(source="fake", external_id="1", title="X")])
    config = MatchConfig(providers=[provider])
    query = SearchQuery(title="X", kind=TRACK)
    assert collect_candidates(query, config) == []


def test_collect_candidates_sorts_by_score_descending():
    provider = _FakeProvider(supports_track=True, results=[
        Candidate(source="fake", external_id="1", title="Totally Unrelated Song"),
        Candidate(source="fake", external_id="2", title="Get Lucky"),
    ])
    config = MatchConfig(providers=[provider])
    query = SearchQuery(title="Get Lucky", kind=TRACK)
    candidates = collect_candidates(query, config)
    assert candidates[0].title == "Get Lucky"
