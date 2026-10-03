"""Parse a raw job posting into validated JSON.

Usage:
    python examples/parse_posting.py evals/cases/postings/smartclip_tpo_data.txt
    python examples/parse_posting.py posting.txt --provider openai --model gpt-5-mini
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_contract import extract, load_provider
from llm_contract.schemas import JobPosting


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("posting_file")
    p.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"])
    p.add_argument("--model", default=None)
    args = p.parse_args()

    text = Path(args.posting_file).read_text(encoding="utf-8")
    provider = load_provider(args.provider, args.model)
    r = extract(text, JobPosting, provider)

    if not r.ok:
        for e in r.errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(r.value.model_dump(), indent=2, ensure_ascii=False))
    print(f"\n[{r.attempts} attempt(s), {r.usage.input_tokens} in / {r.usage.output_tokens} out tokens]",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
