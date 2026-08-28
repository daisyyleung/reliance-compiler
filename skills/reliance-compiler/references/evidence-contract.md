# Evidence contract

Evidence states are `observed`, `reconstructed`, `inferred`, `unavailable`, and
`not_inspected`. The last two carry no semantic support. Every evidence item
has a stable ID, source, kind, locator, provenance, and inspection/run marker.
Keep source content separate from model interpretation; never fabricate a
locator, observation, or confidence percentage. A check's `evidence_required`
field contains evidence IDs. If the needed artifact was not supplied, represent
it as an unavailable source/evidence pair without semantic content so the ID
still resolves; the associated verification option must be unavailable.
