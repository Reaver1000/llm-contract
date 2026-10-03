# Live eval report

Run on 2026-10-03 with `claude-sonnet-4-6` via `python -m llm_contract.evals evals/cases --provider anthropic`.

```
PASS  live-customlytics-junior-data-engineer
PASS  live-everlast-junior-softwareentwickler
PASS  live-smartclip-junior-tpo-data
PASS  harness-retry-on-bad-json
PASS  harness-retry-on-schema-violation

5/5 cases passed
```

## Extracted output per live case

### smartclip_tpo_data.txt

```json
{
  "title": "Junior Technical Product Owner - Data",
  "company": "smartclip Europe GmbH",
  "location": "Berlin, Germany",
  "remote_policy": "hybrid",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "min_years_experience": null,
  "german_level": "required",
  "english_level": null,
  "requires_degree": false,
  "tech_stack": ["TDD", "ETL", "Grafana", "Graylog"]
}
```

Note. The posting is tagged Fully Remote but states the team comes together in Berlin for larger sessions. The model judged that hybrid, which the case's `one_of [remote, hybrid]` expectation accepts on purpose. This is a judgment call a strict matcher would have failed, and the kind of edge the case exists to surface.

### trg_data_engineer.txt

```json
{
  "title": "Junior Data Engineer & MarTech Specialist (Mobile Apps)",
  "company": "Customlytics",
  "location": "Germany",
  "remote_policy": "remote",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "min_years_experience": null,
  "german_level": "none",
  "english_level": "required",
  "requires_degree": false,
  "tech_stack": ["Excel", "Google Sheets", "ChatGPT", "Make.com", "Google Sheets automation"]
}
```

### everlast_junior_dev.txt

```json
{
  "title": "Junior Entwickler",
  "company": "Everlast Consulting GmbH",
  "location": "Remote",
  "remote_policy": "remote",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "min_years_experience": null,
  "german_level": "C1",
  "english_level": null,
  "requires_degree": false,
  "tech_stack": ["Next.js", "TypeScript", "React", "Tailwind", "Node.js", "PostgreSQL", "Supabase", "Claude Code", "Codex", "Cursor"]
}
```
