# S-scope-lock — PRE-LOOP

**Purpose** — stop scope creep before the first edit.

## Do
1. Write the acceptance test before the code.
2. List files to touch. Any file outside the list needs a spoken reason.
3. Pick the shortest working diff. No abstraction, no config, no new dependency without a stated need.
4. Name the guard that must not be cut: validation, security, error handling.

## Gate
One test exists that currently fails for the right reason.

## Output
```
acceptance: <test name>
files: [..]
skipped: [..]
guards_kept: [..]
```
