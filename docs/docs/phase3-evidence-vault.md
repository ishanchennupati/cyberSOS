# CyberSOS — Phase 3: Evidence Vault — Completion Report

This documents what was built on top of the existing Phase 0/1 codebase
(incident creation + financial-fraud triage). Nothing in Phase 0/1's
routes, models, or UI flow was removed or renamed — everything here is
additive.

---

## 1. Files created

### Backend (`backend/app/`)

```
models/evidence.py            Evidence, SuspectIdentifier, TimelineEvent
schemas/evidence.py           Pydantic schemas: extraction, comparison,
                               verify, suspects, timeline, readiness, summary
services/file_validation.py   extension + MIME + magic-byte validation
services/hash_service.py      SHA-256
services/storage_service.py   Supabase Storage client + local-disk fallback
services/evidence_extraction.py   EvidenceExtractionService (provider abstraction)
services/incident_summary.py  AI-summary service (provider abstraction)
services/evidence_service.py  upload/validate/hash/store/extract/verify/compare/readiness
services/suspect_service.py   suspect_identifiers CRUD
services/timeline_service.py  timeline_events CRUD + auto-log helper
api/routes/evidence.py        evidence endpoints
api/routes/suspects.py        suspect endpoints
api/routes/timeline.py        timeline endpoints
```

### Frontend (`frontend/`)

```
types/evidence.ts                          all Phase 3 types + option lists
components/evidence/evidence-upload.tsx     drag-and-drop / tap upload control
components/evidence/evidence-category-picker.tsx
components/evidence/evidence-preview.tsx
components/evidence/evidence-card.tsx
components/evidence/evidence-detail.tsx     preview + extraction + hash + delete
components/evidence/extraction-review.tsx   "we found these details" + edit + confirm
components/evidence/add-evidence-flow.tsx   select file → categorize → upload
components/evidence/evidence-dashboard.tsx  grid of evidence cards
components/evidence/suspect-form.tsx
components/evidence/url-evidence-form.tsx
components/evidence/readiness-panel.tsx
components/evidence/timeline-panel.tsx
components/evidence/incident-description.tsx
components/evidence/summary-generator.tsx
components/evidence/demo-banner.tsx         demo-data + independent-prototype notices
app/incident/[id]/evidence/page.tsx         the Evidence Vault page
```

## 2. Files modified

```
backend/app/core/config.py        Supabase / storage / extraction / summary env vars
backend/app/models/incident.py    + bank, wallet, merchant, description (nullable)
backend/app/db/schema.py          additive ALTER TABLE for the four new columns
backend/app/schemas/incident.py   + IncidentDetailsUpdate, extended IncidentRead
backend/app/services/incident_service.py   + update_incident_details/description
backend/app/api/routes/incidents.py  + /details, /description, /evidence-readiness,
                                      /generate-summary
backend/app/api/v1.py             registers evidence/suspects/timeline routers
backend/app/main.py               imports evidence models so create_all sees them
backend/requirements.txt          + python-multipart, pypdf, anthropic
backend/.env.example              + Phase 3 variables (see below)

frontend/lib/api.ts               + all Phase 3 endpoint calls
frontend/lib/format.ts            + formatFileSize, formatDateTime
frontend/types/incident.ts        + bank, wallet, merchant, description on Incident
frontend/components/result-screen.tsx  + "Go to evidence vault" link
frontend/app/incident/start/page.tsx   unrelated TS narrowing fix (pre-existing bug)
```

## 3. Database migrations / models added

Three new tables (`evidence`, `suspect_identifiers`, `timeline_events`),
created automatically by `Base.metadata.create_all()` on startup — no
manual migration needed for a fresh database. `db/schema.py`'s existing
additive-alter mechanism was extended to add `bank`, `wallet`, `merchant`,
`description` to the `incidents` table on an *existing* Phase 0/1
database without dropping data.

New Postgres enum types: `evidence_type_enum`, `extraction_status_enum`,
`verification_status_enum`, `suspect_identifier_type_enum`. On SQLite
(tests/local dev) these fall back to plain VARCHAR via SQLAlchemy's Enum
type — no special handling needed.

`extracted_data` uses JSONB on Postgres and plain JSON on SQLite, via a
small `TypeDecorator` so both environments work from the same model.

## 4. Supabase Storage setup

1. Create a **private** bucket named `cybersos-evidence` (or set
   `SUPABASE_EVIDENCE_BUCKET` to whatever you name it).
2. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.
3. That's it — no public access policy is needed or wanted. The backend
   uses the service-role key server-side only, and hands the frontend
   short-lived signed URLs (or streams bytes itself) via
   `GET /api/v1/evidence/{id}/file`. The frontend never talks to Supabase
   directly and never sees a permanent URL.

**If you don't configure Supabase** (e.g. running this locally without a
project), the backend automatically falls back to on-disk storage under
`backend/var/evidence-storage/`. Everything else — upload, hash, extract,
verify, preview — works identically. This was essential for testing this
phase without a live Supabase project, and keeps the Evidence Vault
usable for anyone cloning the repo without cloud setup.

## 5. Environment variables required

Add to `backend/.env` (see `backend/.env.example` for the full annotated list):

```
# Storage (optional — falls back to local disk if unset)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_EVIDENCE_BUCKET=cybersos-evidence

# File-size limits
MAX_EVIDENCE_FILE_SIZE_MB=10
MAX_ID_DOCUMENT_SIZE_MB=5

# Extraction / summary providers (both default to no-API-key options)
EXTRACTION_PROVIDER=heuristic       # or "anthropic"
SUMMARY_PROVIDER=template           # or "anthropic"
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

DEMO_MODE=true
```

Frontend needs nothing new — it already had `NEXT_PUBLIC_API_URL`.

## 6. API endpoints added

```
POST   /api/v1/incidents/{incident_id}/evidence          multipart upload
GET    /api/v1/incidents/{incident_id}/evidence
GET    /api/v1/evidence/{evidence_id}
GET    /api/v1/evidence/{evidence_id}/file                private preview/download
PATCH  /api/v1/evidence/{evidence_id}
DELETE /api/v1/evidence/{evidence_id}
POST   /api/v1/evidence/{evidence_id}/extract
POST   /api/v1/evidence/{evidence_id}/verify
GET    /api/v1/evidence/{evidence_id}/compare

POST   /api/v1/incidents/{incident_id}/suspects
GET    /api/v1/incidents/{incident_id}/suspects
PATCH  /api/v1/suspects/{suspect_id}
DELETE /api/v1/suspects/{suspect_id}

POST   /api/v1/incidents/{incident_id}/timeline
GET    /api/v1/incidents/{incident_id}/timeline
PATCH  /api/v1/timeline/{event_id}
DELETE /api/v1/timeline/{event_id}

PATCH  /api/v1/incidents/{incident_id}/details             bank/wallet/merchant
PATCH  /api/v1/incidents/{incident_id}/description
GET    /api/v1/incidents/{incident_id}/evidence-readiness
POST   /api/v1/incidents/{incident_id}/generate-summary
```

## 7. How to run

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL at minimum
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`, go through the existing "I've been
scammed" flow, and on the result screen click **"Go to evidence vault"**
— or navigate directly to `/incident/{incident_id}/evidence`.

## 8. How to test the complete Evidence Vault flow

1. Start an incident and complete triage (Phase 0/1 flow) so you land on
   the result/action-plan screen.
2. Click **Go to evidence vault**.
3. Upload a `.png`, `.jpg`, or `.pdf` (or `.txt` for the heuristic
   extractor to have something to read); pick a category.
4. Confirm a `.exe`/`.bat` upload is rejected with a clear message.
5. Open the uploaded item — extraction runs automatically; review the
   "We found these details" panel, edit anything wrong, click **Confirm
   details**.
6. If the incident's amount/payment method/transaction ID/bank differ
   from what was extracted, the comparison panel flags it — the incident
   itself is never changed automatically.
7. Add a suspect phone/UPI ID/email; add a suspicious URL.
8. Watch **Evidence readiness** update as you add each piece.
9. Add a timeline event or two.
10. Write a description in **Tell us what happened**, save it.
11. Click **Generate incident summary** — review the AI disclaimer, edit
    if needed, accept.
12. Expand **Evidence details** on an item to see the SHA-256 hash and
    plain-language explanation.
13. Delete a piece of evidence and confirm it's gone from Supabase/local
    storage and the dashboard.

Backend can also be smoke-tested directly against the API with `curl` or
the FastAPI `/docs` Swagger UI once the server is running.

## 9. What AI functionality is implemented

Two independent, swappable services — neither is hardwired to a specific
vendor, and both work with **zero API keys** by default:

- **`EvidenceExtractionService`** (`EXTRACTION_PROVIDER`):
  - `heuristic` (default) — regex/text-based extraction from PDF and
    `.txt` evidence (amount, UPI ID, transaction ID, phone, email, URL,
    date/time, bank/wallet/payment-method hints). No image OCR is bundled
    (no system dependency for it in this environment), so image uploads
    report `extraction unavailable` and fall through to manual entry —
    by design, this is a real fallback path, not a broken feature.
  - `anthropic` (optional) — sends the image/PDF to Claude's vision API
    and asks for the same structured JSON, still returning `null` for
    anything not confidently found. Enable by setting
    `EXTRACTION_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`.

- **`incident_summary` service** (`SUMMARY_PROVIDER`):
  - `template` (default) — deterministic paragraph built only from
    fields the citizen has verified plus their own free-text description.
  - `anthropic` (optional) — asks Claude to phrase the same facts as a
    neutral paragraph, still constrained to only the given facts.

In both cases: nothing is invented, nothing is auto-verified, nothing is
submitted anywhere. Every AI output is explicitly labelled ("We found
these details. Please verify them." / "AI-generated draft — review
carefully before using.") and requires the citizen's explicit
confirm/accept action before it's treated as real data.

## 10. What remains for Phase 4

Per the spec's explicit "do NOT implement" list, none of this was
attempted, and it's the natural Phase 4 scope:
- Real integration with cybercrime.gov.in / 1930 / bank/UPI APIs
- Automatic complaint submission
- URL/malware scanning
- Real identity verification (Aadhaar, etc.)
- The final "Review report" screen that assembles evidence + suspects +
  timeline + summary into a single exportable complaint document
- Wiring the Evidence Vault into the main step-by-step `ProgressSteps`
  flow (it currently is reachable as its own page from the result
  screen, per the instruction not to disturb the existing 5-step flow)
- Image OCR for the heuristic extraction provider (would need a system
  dependency such as Tesseract, deliberately left out to keep the
  default zero-dependency path working everywhere)

## 11. Assumptions and limitations

- No OCR library is bundled, so the no-API-key extraction path only
  reads PDF/TXT; screenshots need either the optional Anthropic provider
  or manual entry. This was a deliberate scope decision, documented
  above, not an oversight.
- Local-disk storage fallback is for dev/demo only — a real deployment
  should always configure Supabase (or another private object store).
- The evidence/suspect/timeline tables are additive and don't touch
  Phase 0/1 data; a Phase 0/1 database only needs `ensure_schema()` (run
  automatically on startup) to pick up the new columns and tables.
- Comparison logic only checks fields both the incident and the evidence
  have values for; it never treats a missing value as a mismatch.
- This is a hackathon-grade prototype: authentication/authorization is
  out of scope for both Phase 0/1 and Phase 3 alike (no user accounts
  yet), so evidence endpoints trust the incident_id in the URL. Adding
  auth is a cross-cutting concern for a later phase, not specific to the
  Evidence Vault.

## 12. Errors encountered during development

- A container filesystem/permissions quirk (directories extracted as
  read-only) caused the *pre-existing* Phase 0/1 pytest suite to fail
  with `attempt to write a readonly database`. Confirmed via `git stash`
  that this reproduces on the unmodified codebase and is unrelated to
  Phase 3; fixed locally by `chmod u+w` on the extracted directories.
  A real deployment/CI environment won't have this issue.
- `next build` fails in this sandbox only because outbound requests to
  `fonts.googleapis.com` are blocked by network policy here — unrelated
  to the code. `tsc --noEmit` and `eslint` both pass clean across the
  full `app/components/lib/types` tree, which is the meaningful
  correctness signal available in this environment.
