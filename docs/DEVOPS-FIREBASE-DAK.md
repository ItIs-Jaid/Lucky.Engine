# Lucky.Engine v1.6.0 — Firebase & Data Agent Kit (DAK) DevOps Guide

This document records the v1.6.0 DevOps, database management, and data-science harness review conducted against the **Firebase** and **Data Agent Kit (DAK)** skill suites while preserving `ETHOS.md` (100% stdlib-only core, local-first execution, zero mandatory cloud egress, \$0/mo recurring spend).

---

## 1. Architecture Boundary (`ETHOS.md` Compliance)

| Layer | Modules | Dependencies | Network / Cost |
|---|---|---|---|
| **Layer 1 (Graph Bridge)** | `bridge/engine.py`, `bridge/cache.py` | Python stdlib only | Local-only, \$0 |
| **Layer 2 (Router & Gateway)** | `router.py`, `gateway.py`, `chainlib.py`, `chains.yaml` | Python stdlib only | Local-only, \$0 |
| **Eval & Benchmark Harness** | `evals/routing.py`, `harness/run_experiment.py`, `bridge/eval/runner.py` | Python stdlib only | Local-only, \$0 |
| **Optional DevOps & Telemetry** | `harness/firebase/`, `devops/verify_all.py`, `.github/workflows/ci.yml` | Optional (`pyproject.toml` extras) | Emulator-first (\$0); opt-in cloud |

Core modules **never** import `firebase-admin`, `google-cloud-bigquery`, or any third-party package.

---

## 2. Firebase Skills Review (Harness & DB Management)

1. **`firebase-firestore` & `firebase-basics`**:
   - Configured `harness/firebase/firebase.json` (Firestore Emulator on `127.0.0.1:8080`, `singleProjectMode: true`) and `harness/firebase/firestore.indexes.json` so evaluation telemetry (`eval_runs`, `benchmark_snapshots`) can be tested locally with zero cloud spend via `npx -y firebase-tools@latest emulators:start --only firestore`.
2. **`firestore-rules-creation` & `firebase-security-rules-auditor`**:
   - `harness/firebase/firestore.rules` uses `rules_version = '2'` with a default-deny catch-all (`allow read, write: if false`).
   - **Audit Checklist Verification**:
     - *Update Bypass*: Identical `isValidEvalRun()` / `isValidBenchmarkSnapshot()` validators run on both `create` and `update`; `ownerUid` and `createdAt` are immutable on update.
     - *Authority Source*: Ownership derives solely from `request.auth.uid == resource.data.ownerUid` (never trusting unverified client role flags).
     - *Storage Abuse / DoS*: Bounded string lengths (`1..128`, `1..64`, `1..32`) and numeric ranges (`hitRate` / `recall` in `[0, 1]`, `totalCount >= 1`).
     - *Type Safety*: Explicit `is string`, `is int`, `is number`, `is timestamp` checks on every field.
     - *Field vs. Identity Security*: `hasOnly` + `hasAll` combined with `isDocOwner()`.

---

## 3. Data Agent Kit (DAK) Skills Review (Data Science & DevOps)

1. **`managing-python-dependencies`**:
   - Added `pyproject.toml` declaring `dependencies = []` for the stdlib core and isolated `[project.optional-dependencies]` (`firebase`, `gcp`).
2. **`ml-best-practices`**:
   - Fixed `evals/routing.py`, `harness/run_experiment.py`, `scripts/lucky_solver.py`, and `benchmark/expected/t009.json` so deterministic Axis 1 (routing accuracy: `0.79` / `11/14`) and Axis 2 local (`baseline_acc=0.83`, `framework_acc=0.83`) run reproducibly without fabricated metrics.
   - Corrected `bridge/BENCHMARKS.md` stale token claims (`18.3` avg / `457` total -> actual `56.2` avg / `1404` total from `bridge/eval/runner.py`) and documented `chars/4` estimation semantics.
3. **`schema-mapping` & `data-autocleaning`**:
   - **Data Quality Gate**: `check_public.py` acts as an automated PII/secret/personal-path scrubbing gate across `public/`, `public_bench/`, and the full repository.
   - **Schema Alignment**: `bridge/tests/fixtures/graph_minimal.json` -> `bridge/eval/queries.json` -> `harness/run_experiment.py` -> `eval_runs` Firestore schema.
4. **`google-cloud-auth-verification` & `enforcing-resource-attribution` & `accidental-data-loss-prevention`**:
   - Any optional `gcloud` / `bq` export commands must verify active credentials first (`gcloud auth list --format="json" && gcloud config list --format="json"`), attach `--label datacloud:<ide>` / `CLOUDSDK_METRICS_ENVIRONMENT`, and require explicit user confirmation before any destructive delete/drop operation.
5. **CI/CD Gate**:
   - Run `python devops/verify_all.py` locally or via `.github/workflows/ci.yml` before any commit or push.
