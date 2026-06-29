# RULES

- Do not invent capability or model support that is not registered.
- Do not run unbounded loops or retries.
- Do not treat missing evidence as success.
- Do not overwrite user data or secrets.
- Do not ship a workflow without tests or a replayable trace.
- Prefer deterministic checks before LLM-based judgment.
- Keep cost, token usage, and failure reasons visible in results.
