# Reliance policy

Policies specify required claim types/IDs, required failure modes, zero-tolerance
conditions, review obligations, and an optional maximum burden for auto-rely.
They define acceptable reliance; they never execute actions or grant authority.
The project runtime validates policies against its root `policy.schema.json`;
the mirrored skill intentionally keeps this guidance self-contained. The exact
material-assumption review flag is
`human_review.unsupported_material_assumption`; aliases are not equivalent.
