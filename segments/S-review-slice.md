# S-review-slice — LOOP BODY

**Purpose** — catch the weak diff before it compounds.

## Do
1. Read your own diff as a hostile reviewer.
2. Check: unasked abstraction, dead config, swallowed exception, widened scope.
3. Confirm validation, security, and error handling were not cut for brevity.
4. Fix now. A known defect left in a slice becomes a rewrite later.

## Gate
Diff reviewed line by line, findings listed, none deferred without a reason.
