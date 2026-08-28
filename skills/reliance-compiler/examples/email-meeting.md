# Email meeting example

Input: “Can we catch up next Tuesday afternoon?”

Atomise requester, meeting request, date, and time window. “2pm” is a separate
load-bearing claim and must be `DO_NOT_RELY` unless directly supplied. A useful
receipt recommends checking the latest message and asking the user to choose a
time; the route is `PREPARE_FOR_APPROVAL`. If latest-thread verification is
required but unavailable, declare that option with `available: false`, select
no verification IDs, list the uncovered obligations, and mark the minimum set
`incomplete`.
