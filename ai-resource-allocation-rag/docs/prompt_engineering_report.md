# Prompt Engineering Report

## Implemented Strategies

The recommendation reason generator now supports three prompt strategies in
[backend/services/recommendation_service.py](../backend/services/recommendation_service.py).

- `zero_shot`
- `few_shot`
- `chain_of_thought` (internal reasoning only, single-sentence final output)

The runtime strategy is configurable through:

- `RECOMMENDATION_PROMPT_STRATEGY` in [.env.example](../.env.example)
- Supported values: `zero_shot`, `few_shot`, `chain_of_thought`, `auto`

When `auto` is used, the service generates candidates with all three strategies and
keeps the response with the highest quality score (mentions of skills, experience,
utilization, and certifications).

## Prompt Variations

### 1) Zero-shot

- Direct instruction
- No examples
- Output constraint: one sentence, <= 40 words

### 2) Few-shot

- Two in-context examples included
- Demonstrates desired style for strong-fit and partial-fit candidates
- Output constraint: one sentence, <= 40 words

### 3) Chain-of-thought style

- Instructs checklist-style internal reasoning (skills, experience, certifications, utilization)
- Explicitly requests hidden reasoning and final concise answer only

## Observed Improvements

Local evaluation run (same request, 5 candidates, Llama via Ollama, quality rubric 0-4):

- Request: `Healthcare Modernization` with required skills `Azure, Python`, min experience `3`, preferred cert `Azure-AZ900`
- Rubric signals: mention of matched skills, experience, utilization, and certification

Results:

- `zero_shot`: average quality `1.8/4`
- `few_shot`: average quality `2.8/4`
- `chain_of_thought`: average quality `1.0/4`

Observed behavior:

- `few_shot` produced the most complete and consistently grounded recommendation reasons.
- `zero_shot` was concise but often omitted experience/certification details.
- `chain_of_thought` style occasionally over-focused on narrative and reduced factual coverage.

## Recommendation

- Default strategy: `few_shot` (current default in settings).
- Use `auto` when response completeness is more important than latency.

## Anti-Hallucination Controls

- Prompt includes only project/candidate fields from retrieved records and scoring output.
- Prompt explicitly disallows inventing skills or certifications.
- Fallback reason is deterministic when LLM generation fails.
