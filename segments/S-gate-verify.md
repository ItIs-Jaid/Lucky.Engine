# S-gate-verify — END

**Purpose** — refuse to call it done without execution evidence.

## Do
1. Re-run the full suite, not the touched tests.
2. Paste the real output. No paraphrase, no invented results.
3. List what was skipped and the residual risk in one line each.
4. Emit the change-set artifact: diff, test log, review note.

## Gate
Command output present in the artifact. If a gate failed, the root is NOT done.

## Output
```
tests: <verbatim tail>
skipped: [..]
risk: <one line>
artifact: change-set/
```
