import pytest

from llm_contract import MockProvider, extract
from llm_contract.schemas import JobPosting

GOOD = ('{"title": "QA Engineer", "company": "TestCorp", "location": "Remote", '
        '"remote_policy": "remote", "tech_stack": ["python"]}')


def test_first_try_success():
    r = extract("any text", JobPosting, MockProvider([GOOD]))
    assert r.ok and r.attempts == 1
    assert r.value.title == "QA Engineer"
    assert r.errors == []


def test_retry_on_invalid_json():
    r = extract("any text", JobPosting, MockProvider(["{broken json", GOOD]))
    assert r.ok and r.attempts == 2
    assert len(r.errors) == 1
    assert "not valid JSON" in r.errors[0]


def test_retry_on_schema_violation():
    bad = '{"title": "QA", "company": "C", "location": "X", "remote_policy": "sometimes"}'
    p = MockProvider([bad, GOOD])
    r = extract("any text", JobPosting, p)
    assert r.ok and r.attempts == 2
    assert "schema violation" in r.errors[0]
    assert "remote_policy" in p.calls[1]["user"]


def test_fails_after_max_retries():
    r = extract("any text", JobPosting, MockProvider(["no", "no", "no"]), max_retries=2)
    assert not r.ok and r.attempts == 3
    assert len(r.errors) == 3


def test_fence_stripping():
    fenced = "```json\n" + GOOD + "\n```"
    r = extract("any text", JobPosting, MockProvider([fenced]))
    assert r.ok and r.attempts == 1


def test_usage_accumulates_across_retries():
    p = MockProvider(["broken{", GOOD])
    r = extract("any text", JobPosting, p)
    assert r.usage.input_tokens == 20
    assert r.usage.output_tokens == 40


def test_error_feedback_goes_back_to_the_model():
    bad = '{"title": "QA", "company": "C", "location": "X", "remote_policy": "maybe"}'
    p = MockProvider([bad, GOOD])
    extract("input text here", JobPosting, p)
    assert "input text here" in p.calls[1]["user"]
    assert "violated the schema" in p.calls[1]["user"]
