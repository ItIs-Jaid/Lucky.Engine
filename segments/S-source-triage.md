# S-source-triage — PRE-LOOP

**Purpose** — reject most sources fast so the loop converges.

## Do
1. For each candidate: capture url, publisher, date, and one-line claim.
2. Reject if: undated, no named author, aggregator of an aggregator, paywalled with no fallback.
3. Prefer primary: filings, docs, papers, official records. Secondary only to frame.
4. Cap the working set at 5 sources. More means the question is wrong.

## Gate
Every kept source has a resolvable url verified this session (not recalled).

## Output
```
kept:  [{url, publisher, date, claim}]
dropped:[{url, reason}]
```
