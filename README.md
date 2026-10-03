# llm-contract

Make an LLM API honor a contract.

You give it text and a typed schema. It prompts the model, parses the JSON, validates it against the schema, and when validation fails it feeds the exact errors back to the model and retries. Then a small eval harness proves the contract holds, with golden cases you can run in CI.

[![CI](https://github.com/Reaver1000/llm-contract/actions/workflows/ci.yml/badge.svg)](https://github.com/Reaver1000/llm-contract/actions/workflows/ci.yml)

## Why

Every serious LLM integration needs the same three boring things, and most code samples quietly skip all of them:

1. **A schema** the output is held to, not a vibe the output is checked against
2. **A retry loop** that tells the model what it got wrong instead of just failing
3. **An eval set** so you notice regressions when you change models or prompts

This library is those three things in about 200 lines, with nothing else to learn.

## Install

```bash
pip install pydantic anthropic openai
```

## Use

```python
from llm_contract import extract, AnthropicProvider
from llm_contract.schemas import JobPosting

provider = AnthropicProvider()  # reads ANTHROPIC_API_KEY from the environment

result = extract(raw_posting_text, JobPosting, provider)
if result.ok:
    posting = result.value          # a validated pydantic object
    posting.remote_policy           # "remote" | "hybrid" | "onsite" | "unknown"
    result.attempts                 # how many round trips the contract took
    result.usage.input_tokens       # token accounting, because it is not free
else:
    result.errors                   # the exact failure at each attempt
```

Swap `AnthropicProvider()` for `OpenAIProvider()` and nothing else changes. The provider interface is two methods deep, so adding a new provider or a fake for tests is a few lines.

## The contract loop

```
text + schema
    |
    v
prompt model with the JSON schema
    |
    v
parse output as JSON ------- fails ----> tell model the parse error, retry
    |
    v
validate against schema ---- fails ---> tell model the violated fields, retry
    |
    v
typed, validated object
```

Retries default to two. Every attempt's failure is recorded, and token usage is accumulated across the whole loop, so a three-attempt extraction reports three attempts honestly.

## Evals

```bash
python -m llm_contract.evals evals/cases --provider mock      # CI-safe, no API key
python -m llm_contract.evals evals/cases --provider anthropic  # live golden cases
```

Cases are small JSON files: an input text, a schema name, expected values with matchers (exact, contains, approx, one_of, not_null, is_null), and either scripted mock responses or a live provider. Mock cases test the mechanics of the loop in CI. Live cases run real postings through a real model and check the extraction against hand-written expectations, with tolerances chosen for what a model can honestly be expected to get right.

The repo ships five cases: two mock cases exercising the retry paths, and three live cases parsing real German and English job postings, the demo domain.

All five cases pass against `claude-sonnet-4-6` on a real run, including the live postings. The full report with extracted output is in `evals/results/`.

## Extend

Add a schema:

```python
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    total: float
    currency: str
```

Register it in `llm_contract/evals.py`, write a case file, done. `extract()` works with any pydantic model, no registration needed for direct use.

## Design choices

- Feedback retries beat temperature tweaks. Telling the model exactly which fields violated the schema fixes the actual failure. Raising the temperature and hoping fixes nothing.
- Mock providers make the loop testable in CI without keys, and make the tests deterministic.
- Token accounting is built in, because an extraction pipeline that hides its own cost is lying to you.
- No agent framework, no tool use, no magic. This is the reliable twenty percent that every fancier thing needs anyway.
