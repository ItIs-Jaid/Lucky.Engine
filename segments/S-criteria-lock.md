# S-criteria-lock — PRE-LOOP

**Purpose** — turn vague intent into pass/fail criteria before searching.

## Do
1. Convert preferences into numbers: max rent, max commute, min sqft, needed bus line.
2. Separate hard filters from nice-to-haves.
3. State the walk-away condition.
4. Name the budget source and the true monthly ceiling.

## Gate
Every hard filter is numeric or binary. No "nice area".

## Output
```
hard: {rent_max, commute_min, ...}
soft: [..]
walk_away: <condition>
```
