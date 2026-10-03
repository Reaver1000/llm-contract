import pytest

from llm_contract import MockProvider, load_provider


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        load_provider("nonexistent")


def test_mock_provider_exhaustion_raises():
    p = MockProvider(["one"])
    p.complete(system="s", user="u")
    with pytest.raises(AssertionError):
        p.complete(system="s", user="u")


def test_mock_provider_records_calls():
    p = MockProvider(["one", "two"])
    p.complete(system="a", user="b")
    p.complete(system="c", user="d")
    assert [c["system"] for c in p.calls] == ["a", "c"]
