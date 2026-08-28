# Reliance Compiler v0.1

> Compile AI outputs into evidence-bound claims, assumptions, failure modes and
> the minimum verification needed for safe human reliance.

Reliance Compiler makes the human loop smaller without making it weaker. Its
unit of reasoning is a claim, not a whole-answer confidence score, and its
objective is:

```text
minimise human verification cost
subject to residual reliance risk <= declared task policy
```

## What is included

- Reusable skill at [`skills/reliance-compiler/SKILL.md`](skills/reliance-compiler/SKILL.md)
  with progressive-disclosure references and examples.
- Machine contracts in [`schemas/`](schemas/): reliance packet, policy, and
  future shadow-audit records.
- Standard-library deterministic control plane in
  [`scripts/reliance.py`](scripts/reliance.py): `validate`, `plan`, `compare`,
  `evaluate`, and `render`.
- Fixture-scoped counterfactual evaluation under [`evals/`](evals/) and unit
  tests under [`tests/`](tests/).
- Architecture and Phase 2 boundary notes in [`docs/`](docs/).

## CLI

From this directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/reliance.py validate packet.json
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/reliance.py plan packet.json
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/reliance.py render packet.json
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/reliance.py compare baseline.json candidate.json
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/reliance.py evaluate evals/fixtures
```

All commands are local and deterministic. `validate`, `compare`, and malformed
inputs return non-zero status. `render` emits a human receipt and explicitly
reminds the reader that it is advisory.

## Architecture and limits

The skill owns semantic procedure—claim atomisation, graphing, evidence binding,
assumption and contradiction handling, disconfirmation, failure-mode modelling,
verification design, and claim-level reliance guidance. Python owns structural
checks, bounded set selection over declarations, rendering, comparison, and
fixture evaluation. It does not acquire evidence, execute checks, enforce
permissions, persist runtime state, orchestrate events, call external APIs, or
mutate systems. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

`exact` planner output means exact only within declared mappings and ordinal
cost bands. Large option sets use deterministic `heuristic`; impossible
coverage is `incomplete`. The project deliberately avoids fabricated numeric
confidence or production reliability/SLO claims.

## Evaluation scope

The suite has 25+ records (21 semantic cases plus 5 contract negatives) spanning
20 required categories, with raw inputs, model packets, counterfactual inputs,
and evaluator-owned truth kept separate. Semantic metrics exclude expected-invalid
contract negatives and report numerator/denominator with `scope: fixture_suite`;
they are not production reliability estimates. Negative controls exercise duplicate/dangling IDs,
cycles, unsupported evidence, unresolved contradictions, dependency
escalation, conditionless conditional reliance, stale plans, burden ceilings,
and execution-authority representations.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_project.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
python3 -B <path-to-skill-creator>/scripts/quick_validate.py skills/reliance-compiler
```

## Deliberate non-goals

No Gmail/Outlook/Slack/Teams/calendar connectors, autonomous sending,
authentication, enterprise policy service, cloud deployment, marketplace,
scraping, generic guardrails, or permission enforcement are included. Phase 2
interface design is documented in [`docs/PHASE2_INTERFACE.md`](docs/PHASE2_INTERFACE.md).

## License

MIT; see [`LICENSE`](LICENSE).
