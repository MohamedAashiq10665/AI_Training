# Prompt Engineering Report

## Prompt Strategy

- System behavior anchored to enterprise staffing use case.
- Retrieval-grounded generation with strict context-only guidance.
- Output constrained to ranked list, scores, explanation, gaps, upskilling.

## Anti-Hallucination Controls

- Inject only retrieved candidate snippets.
- Ask model to answer using supplied context.
- Return concise structured response format.
