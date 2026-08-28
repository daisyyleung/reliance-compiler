# Claim graph

Create claims for independently falsifiable propositions, not every token.
Give each claim a stable ID and record materiality, support state, verification
status, assumptions, dependencies, contradictions, load-bearing flag, and
claim-level reliance status. A downstream claim cannot outrun an unresolved
load-bearing dependency. Dependencies have one canonical direction: if claim B
depends on claim A, B lists A in `dependencies`, and a `depends_on` relation has
`from_claim_id: B` and `to_claim_id: A`. The complete dependency list and the
complete set of `depends_on` relation edges must match exactly.
