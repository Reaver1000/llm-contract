from pathlib import Path

from llm_contract.evals import _match, load_cases, run_cases

CASES = Path(__file__).resolve().parents[1] / "evals" / "cases"


def test_matchers():
    assert _match("remote", {"match": "exact", "value": "remote"})
    assert not _match("hybrid", {"match": "exact", "value": "remote"})
    assert _match("Junior Data Engineer", {"match": "contains", "value": "data"})
    assert _match(50100, {"match": "approx", "value": 50000, "tolerance": 200})
    assert _match("remote", {"match": "one_of", "value": ["remote", "hybrid"]})
    assert _match(None, {"match": "is_null"})
    assert _match("x", {"match": "not_null"})


def test_repo_mock_cases_all_pass():
    cases = load_cases(CASES)
    results, skipped = run_cases(cases, provider=None, base_dir=CASES)
    assert skipped == 3, "expected exactly the three live cases to be skipped"
    mock_results = [r for r in results]
    for r in mock_results:
        assert r.passed, f"{r.name}: {r.failures}"
