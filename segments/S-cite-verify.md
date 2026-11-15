# S-cite-verify — MIDDLE

**Purpose** — make every claim falsifiable before it enters the artifact.

## Do
1. Split the draft into atomic claims.
2. Attach exactly one source per claim. No source -> the claim is deleted, not softened.
3. Confirm the source says what is attributed. Quote <= 25 words as proof.
4. Mark contested claims with both sides and the reason for the pick.

## Gate
claims_cited / claims_total == 1.0. This is the loop exit predicate.

## Output
```
claims: [{id, text, src, quote, status: cited|contested}]
ratio: 1.0
```
