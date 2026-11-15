# S-listing-verify — MIDDLE

**Purpose** — kill stale and fake listings fast.

## Do
1. Open the live page. No cached snippet.
2. Confirm: price visible, address or cross-streets, posted date, contact route.
3. Reject: "call for price", duplicate photos across postings, broker-only listings with no unit.
4. Log price and date captured. A listing older than 14 days is unverified.

## Gate
listings_verified == listings_candidates.

## Output
```
verified: [{url, price, date_captured, address}]
rejected: [{url, reason}]
```
