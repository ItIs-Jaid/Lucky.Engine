# public/ — publishable slice

Everything here is safe to publish as-is. Everything outside is private by default.

| File | Publishable | Why |
|---|---|---|
| `catalog.json` | yes | generic skill names + public repo URLs |
| `../PUBLIC-CATALOG.md` | yes | rename map and naming contract |
| `../router.py`, `../gateway.py`, `../chainlib.py` | yes after gate | no operator data in code |
| `../chains.yaml` | **no** | location keywords; publish a genericized copy |
| `../segments/*.md` | yes after gate | procedures only; scan before copying |
| `../ANALYSIS.md`, `../RESUME-EVIDENCE.md` | **no** | cite private session telemetry |
| `../README.md` | **no** | mentions this host's measured history |

Gate: `python check_public.py --path public/` must exit 0.
