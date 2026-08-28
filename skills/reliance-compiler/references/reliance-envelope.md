# Reliance envelope

Return claim statuses `RELY`, `RELY_WITH_CONDITION`, `VERIFY`, `DO_NOT_RELY`,
or `ABSTAIN`, with explicit conditions and prohibited reliance. Also report a
separate human burden level: `0 NO_MANUAL_CHECK`, `1 GLANCE`, `2
REVIEW_EVIDENCE`, `3 VERIFY_SOURCE`, `4 HUMAN_JUDGMENT`, or `5 HUMAN_ONLY`.
An overall route is advisory and may be `RELY`, `VERIFY_FIRST`,
`PREPARE_FOR_APPROVAL`, `HUMAN_DECISION_REQUIRED`, or `ABSTAIN`.
