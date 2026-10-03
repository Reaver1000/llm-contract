"""A small eval harness. Golden cases in, a report out, a CI-friendly exit code."""
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .extract import extract
from .providers import MockProvider, Provider, load_provider

SCHEMA_REGISTRY = {}

try:
    from .schemas import JobPosting
    SCHEMA_REGISTRY["jobposting"] = JobPosting
except ImportError:
    pass


@dataclass
class CaseResult:
    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)


def _match(actual: Any, matcher: dict) -> bool:
    kind = matcher.get("match", "exact")
    expected = matcher.get("value")
    if kind == "exact":
        return actual == expected
    if kind == "contains":
        return actual is not None and expected.lower() in str(actual).lower()
    if kind == "approx":
        tol = matcher.get("tolerance", max(1, abs(expected) * 0.05))
        return actual is not None and abs(float(actual) - float(expected)) <= tol
    if kind == "one_of":
        return actual in expected
    if kind == "not_null":
        return actual is not None
    if kind == "is_null":
        return actual is None
    raise ValueError(f"Unknown matcher {kind!r}")


def _score_case(result_value, expect: dict) -> list[str]:
    failures = []
    for field_name, matcher in expect.items():
        actual = getattr(result_value, field_name, None)
        if not _match(actual, matcher):
            failures.append(f"{field_name}: got {actual!r}, wanted {matcher}")
    return failures


def load_cases(cases_dir: str | Path) -> list[dict]:
    cases = []
    for path in sorted(Path(cases_dir).glob("*.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    return cases


def run_cases(cases: list[dict], provider: Provider | None,
              base_dir: Path) -> tuple[list[CaseResult], int]:
    results = []
    skipped = 0
    for case in cases:
        if case.get("mode") == "live" and provider is None:
            skipped += 1
            continue
        schema = SCHEMA_REGISTRY[case["schema"]]
        input_text = (base_dir / case["input_file"]).read_text(encoding="utf-8")

        if case.get("mode") == "mock":
            case_provider = MockProvider(case["mock_responses"])
        else:
            case_provider = provider

        r = extract(input_text, schema, case_provider, max_retries=case.get("max_retries", 2))
        if not r.ok:
            results.append(CaseResult(case["name"], False, [f"extraction failed: {r.errors}"]))
            continue

        failures = _score_case(r.value, case.get("expect", {}))
        results.append(CaseResult(case["name"], not failures, failures))
    return results, skipped


def report(results: list[CaseResult], skipped: int = 0) -> int:
    if not results and not skipped:
        print("no cases found")
        return 1
    width = max([len(r.name) for r in results] + [10]) + 2
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{status}  {r.name.ljust(width)}" + ("; ".join(r.failures) if r.failures else ""))
    passed = sum(1 for r in results if r.passed)
    print(f"\n{passed}/{len(results)} cases passed", end="")
    if skipped:
        print(f" ({skipped} live case(s) skipped, no provider)")
    else:
        print()
    return 0 if passed == len(results) else 1


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Run llm-contract eval cases")
    p.add_argument("cases_dir", nargs="?", default="evals/cases")
    p.add_argument("--provider", default="mock", choices=["mock", "anthropic", "openai"])
    p.add_argument("--model", default=None)
    args = p.parse_args()

    base = Path(args.cases_dir)
    cases = load_cases(base)
    provider = load_provider(args.provider, args.model) if args.provider != "mock" else None
    results, skipped = run_cases(cases, provider, base)
    return report(results, skipped)


if __name__ == "__main__":
    sys.exit(main())
