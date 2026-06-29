# MAOE

MAOE is a skill-native workflow compiler for engineering tasks.

The system accepts a user goal, compiles it into a capability graph, selects
skills and agents under cost and risk constraints, and executes the resulting
workflow with explicit trace, budget, and quality evidence.

## Runtime contract

- Load the core files first.
- Only use registered agents, commands, and skills.
- Keep execution bounded by budget, risk, and time limits.
- Record load trace, decision trace, and output artifacts for every run.

## Current focus

- Stabilize the bootstrap and manifest path.
- Make task execution deterministic enough to benchmark.
- Keep the demo path short enough for competition review.
