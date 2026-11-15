# S-slice-build — MIDDLE

**Purpose** — deliver one thin verifiable slice per loop iteration.

## Do
1. RED: run the test, capture the failure.
2. GREEN: smallest change that passes.
3. REFACTOR: only if the diff stays net smaller.
4. Checkpoint the ledger: iteration, files, test state.

## Gate
Test suite green and output pasted, not summarised.

## Output
```
iter: n
changed: [..]
tests: pass/fail counts
```
