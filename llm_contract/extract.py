"""The contract loop. Prompt from a schema, parse, validate, feed errors back, retry."""
import json
import re
from dataclasses import dataclass, field
from typing import Type, TypeVar

from pydantic import TypeAdapter, ValidationError

from .providers import Provider, Usage

T = TypeVar("T")

SYSTEM_TEMPLATE = (
    "You extract structured data from text. "
    "Reply with a single JSON object and nothing else. No markdown fences, no commentary. "
    "Every field must follow this JSON schema exactly:\n{schema}\n"
    "If a value is not present in the text, use null. "
    "Never guess values the text does not support."
)


@dataclass
class ExtractResult:
    value: object | None
    ok: bool
    attempts: int
    usage: Usage
    errors: list[str] = field(default_factory=list)


def strip_fences(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, re.S)
    return m.group(1) if m else t


def _parse_json(text: str) -> dict:
    return json.loads(strip_fences(text))


def _flatten_validation_errors(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def extract(text: str, schema: Type[T], provider: Provider,
            max_retries: int = 2) -> ExtractResult:
    """Extract a typed object from text. Retries with explicit error feedback when
    the model output fails JSON parsing or schema validation."""
    adapter = TypeAdapter(schema)
    system = SYSTEM_TEMPLATE.format(schema=json.dumps(adapter.json_schema(), indent=2))
    usage = Usage()
    errors: list[str] = []
    user = text

    for attempt in range(1, max_retries + 2):
        completion = provider.complete(system=system, user=user)
        usage.add(completion.usage)

        try:
            parsed = _parse_json(completion.text)
        except json.JSONDecodeError as e:
            errors.append(f"attempt {attempt}: output was not valid JSON ({e.msg})")
            user = (text + "\n\nYour previous reply was not valid JSON: "
                    + e.msg + "\nReply again with a single JSON object only.")
            continue

        try:
            value = adapter.validate_python(parsed)
            return ExtractResult(value=value, ok=True, attempts=attempt,
                                usage=usage, errors=errors)
        except ValidationError as e:
            flat = _flatten_validation_errors(e)
            errors.append(f"attempt {attempt}: schema violation ({flat})")
            user = (text + "\n\nYour previous JSON violated the schema:\n" + flat
                    + "\nFix exactly these fields and reply again with a single JSON object.")

    return ExtractResult(value=None, ok=False, attempts=max_retries + 1,
                         usage=usage, errors=errors)


def extract_or_raise(text: str, schema: Type[T], provider: Provider,
                     max_retries: int = 2) -> T:
    result = extract(text, schema, provider, max_retries)
    if not result.ok:
        raise ValueError("extraction failed after retries: " + " | ".join(result.errors))
    return result.value
