# Verification commands and recorded baselines

Current developer commands/results: see "Phase 2 UX repair verification" below.
The Phase 0A/0B sections preserve historical evidence and failures.

Executed 2026-09-30 on branch `phase-0`, HEAD `cadb2d7986b9c053a1262742a650544c283daa7c`. Shell: PowerShell. Repository root: `C:\Users\Ishan Chennupati\Downloads\cybersos`.
This file did not exist when 0A started; commands were discovered from `backend/pytest.ini`, `backend/requirements.txt`, `backend/alembic.ini`, `frontend/package.json`, and existing tests. It is now the repeatable command record. No code or test corrections were made.

## Prerequisites and environment

- Existing root `.venv\Scripts\python.exe`: Python 3.13.12, pytest 8.3.3, installed SQLAlchemy/Alembic/FastAPI packages. This was the active interpreter (`Get-Command python`), not the separate backend/.venv.
- Node v24.14.1, npm 11.11.0; frontend/node_modules already present. Package scripts use Next.js 14.2.35.
- No dependency install or network/provider request was made. This audit uses the available environment rather than claiming a clean requirements-only installation.
- Frontend build reports loading .env.local; contents were not read or recorded. API probes override DATABASE_URL/CORS_ORIGINS with synthetic local values. Backend fixtures override these too.
- Tests use a shared relative ./test.db and drop tables. Running from backend would risk the existing backend/test.db. Run the actual complete suite via pytest.main with its real config and absolute tests path, with a newly generated temporary CWD. This changes runtime file location, not app/test code or clock.
- Fresh Alembic test uses a new temporary SQLite file, never the configured PostgreSQL or existing databases. PostgreSQL-specific enum behavior, supported prior-schema upgrades and production readiness remain unverified.
- Initial sandbox access to OS temporary directories failed. The exact same commands were rerun with approved escalation. Branch creation likewise required approval to write .git metadata.
- Existing pytest cache directories are unreadable to sandbox git enumeration; git status emitted warnings. Test cache was disabled with -p no:cacheprovider. Those warnings are not application test results.

## Baseline results

| Check | Execution CWD | Outcome |
| --- | --- | --- |
| Backend full suite, initial sandbox attempt | root launcher; temp CWD attempted | NOT RUN: exit 1, WinError 5 during chdir before pytest |
| Backend full suite, approved retry | root launcher; temporary tests CWD below; pytest rootdir backend | FAIL: exit 1, 163 collected, 161 passed, 2 failed in 4.29s |
| Frontend lint | frontend | PASS: exit 0, no ESLint warnings/errors |
| Frontend production build | frontend | PASS: exit 0; compile, lint, types, static generation and build traces completed |
| Fresh Alembic, initial sandbox attempt | backend after root launcher | FAIL TO EXECUTE MIGRATIONS: exit 1, SQLite unable to open temp file |
| Fresh Alembic, approved retry | backend after root launcher | PASS for fresh SQLite: exit 0, head 20260824_urgency_metadata |
| OpenAPI/model collision probe | backend | OpenAPI generated; intentional second model import FAIL: exit 1, duplicate-table InvalidRequestError |
| Corrected all-call OpenAPI comparison | backend | PASS as audit comparison: exit 0, 25 calls/URLs, 19 missing operations. This confirms mismatches; it is not an integration pass. |
| Documentation diff/consistency check | root | Final result recorded in phase-status.md |
| Live provider | none | NOT RUN; no remote credentials/model/storage behavior tested |
| Manual browser / accessibility journey | none | NOT RUN; no manual app pass claimed |
| Fresh PostgreSQL / prior-schema migration | none | NOT RUN |

### Backend tests — exact command

Launcher CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos`.

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); tmp=tempfile.mkdtemp(prefix='cybersos-0A-tests-'); print('Temporary working directory:',tmp,flush=True); os.chdir(tmp); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests'),'-v','-p','no:cacheprovider']))"
```

Initial sandbox attempt generated `C:\Users\ISHANC~1\AppData\Local\Temp\cybersos-0A-tests-d_zhs10l` and failed before test collection with `PermissionError: [WinError 5] Access is denied`.
Approved retry used `C:\Users\ISHANC~1\AppData\Local\Temp\cybersos-0A-tests-c25udplz`.
Pytest config: `C:\Users\Ishan Chennupati\Downloads\cybersos\backend\pytest.ini`; tests: `C:\Users\Ishan Chennupati\Downloads\cybersos\backend\tests`.
The autouse fixtures ran unchanged, including startup ensure_schema and teardown drop_all. File/evidence test data were synthetic; repository database contents were neither inspected nor mutated.

Actual failure output:

```text
collected 163 items
test_triage_without_transaction_id_succeeds
backend/tests/test_incidents_api.py:57
assert data["urgency"] == "critical"
AssertionError: assert 'low' == 'critical'

test_action_plan_includes_draft_and_actions
backend/tests/test_incidents_api.py:89
assert data["urgency"] == "critical"
AssertionError: assert 'low' == 'critical'

2 failed, 161 passed in 4.29s
```

Root-cause evidence: API tests use fixed NOW=2026-08-24T12:00:00Z (`tests/test_incidents_api.py:9`) and occurred_at 20 minutes earlier (`:24`) but the API supplies actual clock to rules (`app/services/incident_service.py:832`). September 30 is older than seven days, giving low (`app/rules/action_rules.py:29`). A read-only clock probe observed 2026-09-30T16:36:44.942897+00:00. No clock was frozen and no assertions changed. The failures predate this documentation-only change.

### Frontend lint — exact command

CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos\frontend`.

```powershell
npm run lint
```

Actual result: exit 0, `next lint`, “No ESLint warnings or errors.”

### Frontend build — exact command

CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos\frontend`.

```powershell
npm run build
```

Actual result: exit 0; Next.js 14.2.35 compiled successfully, completed lint/type validity, generated 5/5 static pages and build traces. Routes included /, /_not-found, /incident/start, /incident/[id]/result, /incident/[id]/evidence.
Ignored .next build outputs were generated by the real build. Tracked tsconfig.tsbuildinfo had no resulting tracked diff. A successful build does not execute backend calls or establish functional evidence-vault behavior.

### Fresh temporary Alembic — exact command

Launcher CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos`; command changes CWD to `C:\Users\Ishan Chennupati\Downloads\cybersos\backend` before reading alembic.ini.

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile; from pathlib import Path; from alembic.config import Config; from alembic import command; from sqlalchemy import create_engine,inspect,text; root=Path.cwd(); tmp=Path(tempfile.mkdtemp(prefix='cybersos-0A-alembic-')); url='sqlite:///'+(tmp/'fresh.db').as_posix(); os.environ['DATABASE_URL']=url; os.chdir(root/'backend'); print('Working directory:',Path.cwd(),flush=True); print('Fresh database:',url,flush=True); cfg=Config('alembic.ini'); command.upgrade(cfg,'head'); eng=create_engine(url); print('Tables:',inspect(eng).get_table_names()); print('Revision:',eng.connect().execute(text('select version_num from alembic_version')).all())"
```

Initial sandbox attempt: database URL `sqlite:///C:/Users/ISHANC~1/AppData/Local/Temp/cybersos-0A-alembic-wgqfkt2h/fresh.db`, exit 1, `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`. No migration execution succeeded.
Approved retry: fresh file `C:\Users\ISHANC~1\AppData\Local\Temp\cybersos-0A-alembic-agilwv1a\fresh.db`.

```text
Context impl SQLiteImpl.
Running upgrade -> 20260824_phase2
Running upgrade 20260824_phase2 -> 20260824_urgency_metadata
Tables: ['alembic_version', 'evidence', 'incidents']
Revision: [('20260824_urgency_metadata',)]
```

Exit 0. There are no suspect_identifiers/timeline_events tables. The first migration called Base.metadata.create_all and returned on this fresh DB; runtime models determine that schema. Do not interpret this pass as evidence of immutable migrations, new vault schema readiness, or PostgreSQL upgrade safety.

## Audit probes

### Mounted OpenAPI and duplicate Evidence reproduction

CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos\backend`.

```powershell
$env:DATABASE_URL='sqlite:///:memory:'; $env:CORS_ORIGINS='http://testserver'; ..\.venv\Scripts\python.exe -c "from app.main import app; import json; schema=app.openapi(); print(json.dumps({p:{m:{'operationId':v.get('operationId'),'response':v.get('responses',{}).get('200',v.get('responses',{}).get('201',{}))} for m,v in ops.items()} for p,ops in schema['paths'].items()},indent=2)); import app.models.evidence"
```

Generated the eight mounted operations tabulated in audit.md. Then importing app.models.evidence failed:

```text
sqlalchemy.exc.InvalidRequestError: Table 'evidence' is already defined for this MetaData instance.
Specify 'extend_existing=True' to redefine options and columns on an existing Table object.
```

Exit 1 is expected reproduction evidence, not a passing app check. Do not apply extend_existing as a fix; it is just SQLAlchemy's error text. No startup/database migration or live HTTP service was run by this probe.

### Corrected automatic frontend/OpenAPI comparison

CWD: `C:\Users\Ishan Chennupati\Downloads\cybersos\backend`.

```powershell
$env:DATABASE_URL='sqlite:///:memory:'; $env:CORS_ORIGINS='http://testserver'; ..\.venv\Scripts\python.exe -c "from app.main import app; import re; from pathlib import Path; schema=app.openapi(); print('MOUNTED'); [print(m.upper(),p) for p,ops in schema['paths'].items() for m in ops]; mounted={(m.upper(),re.sub(r'\{[^}]+\}','{}',p)) for p,ops in schema['paths'].items() for m in ops}; source=Path('../frontend/lib/api.ts').read_text(); total=missing=0;
for name,block in re.findall(r'export function (\w+)\((.*?)(?=\nexport function|\Z)',source,re.S):
 match=re.search(r'/(?:api/v1/|health)[^'+chr(34)+chr(96)+']*',block)
 if not match: continue
 path=re.sub(r'\$\{[^}]+\}','{}',match.group()); method_match=re.search(r'method: '+chr(34)+r'(\w+)',block); method=method_match.group(1) if method_match else 'GET'; ok=(method,path) in mounted; total+=1; missing+=not ok; print(name,method,path,'MATCH' if ok else 'MISSING')
print('TOTAL',total,'MISSING',missing)"
```

Exit 0, output `TOTAL 25 MISSING 19`; full per-operation results in audit.md. The six matched names were getApiHealth, createIncident, getIncident, triageIncident, uploadEvidence and getActionPlan.
An earlier ad hoc parser exited 0 but erroneously reported 24 missing because it retained string delimiters/closing syntax. Its result was rejected after checking known mounted operations; the command above corrected extraction and was run successfully. This was an audit-script error, not an application failure. The corrected comparison does not validate request/response bodies; upload schema mismatch was separately traced to source and OpenAPI schemas.

### Read-only discovery commands

CWD root unless noted:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git ls-files test.db backend/test.db frontend/tsconfig.tsbuildinfo docs/roadmap.md docs/phase-status.md docs/verification.md
Test-Path docs/phase-status.md
Test-Path docs/verification.md
Test-Path docs/roadmap.md
Test-Path backend/tests/fixtures/scenarios.yaml
Get-Command python,node,npm | Select-Object Name,Source
.\.venv\Scripts\python.exe --version
node --version
npm --version
```

Before audit document creation, all four Test-Path results were False. Tracked file listing returned only root test.db and frontend/tsconfig.tsbuildinfo. Source searches used rg with numbered output; Windows wildcard-path attempts such as backend/alembic/versions/*.py were rejected by rg and repeated using the directory argument. Only successful reads underpin file:line evidence.

Branch command `git switch -c phase-0` initially failed with permission denied writing phase-0.lock; approved retry exited 0 and created phase-0. No commit/push operation ran.

## Documentation consistency check

CWD: repository root.

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; import re,subprocess; names=['audit.md','verification.md','phase-status.md']; docs={n:(Path('docs')/n).read_text(encoding='utf-8') for n in names}; [print(n,len(t.splitlines()),'lines') for n,t in docs.items()]; assert all(all('R'+str(i) in t for i in range(1,6)) for t in [docs['audit.md'],docs['phase-status.md']]); rows=[l for l in docs['audit.md'].splitlines() if re.match(r'\| \w+ :\d+ \|',l)]; assert len(rows)==25,len(rows); assert sum('MISSING' in l for l in rows)==19; assert sum('MATCH' in l for l in rows)==6; assert all('NOT RUN' in docs[n] for n in ['verification.md','phase-status.md']); assert all(t.count(chr(96)*3)%2==0 for t in docs.values()); assert all(l==l.rstrip() for t in docs.values() for l in t.splitlines()); changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines(); assert changed==['AGENTS.md'],changed; print('PASS: R1-R5 coverage, 25 API rows / 19 missing / 6 matching, separate not-run results, balanced code fences, no application tracked diff.')"
```

Corrected check: exit 0. Confirms R1–R5 coverage in audit/status, exactly 25 API rows (19 missing, 6 matched), explicit NOT RUN in the verification/status records, balanced code fences, no trailing whitespace, and only the pre-existing AGENTS.md tracked diff.
The first consistency-script attempt required the exact uppercase phrase NOT RUN in audit.md too, although that narrative already said the checks were not run. It raised AssertionError. The checker was corrected to inspect the explicit outcome records; no application source changed. Its combined PowerShell command ended with a successful Git command, masking Python's nonzero status at the shell level; the traceback was reviewed and rejected as a pass. The corrected standalone Python command above exited 0.

## Repeat-check boundaries

Use these exact baseline commands while shared-db fixtures remain. Do not run unisolated pytest from the root/backend against existing test.db. Later steps may change these commands only with their documented implementation and verification evidence.
Keep automated, live-provider and manual outcomes distinct. No failed or unavailable check is treated as passed. 0A documents failures; it does not repair them.

## Step 0B verification — 2026-09-30

Supersedes shared-database repeat instructions above. R is repository root.
Prerequisites: existing root .venv/backend dependencies, frontend/node_modules,
Node/npm, installed Playwright driver and cached Chromium. No installation or
cloud credentials/user database required. Synthetic data only.

### Backend and migrations (R1–R7)

Launcher CWD R; pytest runs from a new temporary directory. conftest.py creates
session-private migrated SQLite and temporary evidence, resets rows between tests,
disposes connections and cleans up. No shared ./test.db.

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); os.chdir(tempfile.mkdtemp(prefix='cybersos-0B-final-')); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests'),'-q','-p','no:cacheprovider','--tb=short']))"
```

Final result: exit 0, **188 passed in 3.84s**. Includes five migration cases:
fresh metadata parity; current schema unversioned, stamped at 20260824_phase2,
stamped at 20260824_urgency_metadata; missing original bytes. Upgrade cases
preserve incident values, evidence metadata/private paths/bytes and timestamps;
available originals establish SHA-256. Existing create/triage/action-plan passes;
fixed August fixture clock in tests only, production rules unchanged.

Test-first commands, CWD R, before production edits:

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); tmp=tempfile.mkdtemp(prefix='cybersos-0B-red-'); os.chdir(tmp); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests/test_evidence_contract.py'),str(root/'backend/tests/test_config.py'),'-q','-p','no:cacheprovider']))"
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); os.chdir(tempfile.mkdtemp(prefix='cybersos-0B-migration-red-')); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests/test_migrations.py'),'-q','-p','no:cacheprovider','--tb=short']))"
```

Respectively exit 1, 18 failed in 2.47s; exit 1, 5 failed in 1.25s.
Initial full green used final launcher with prefix cybersos-0B-green-:
exit 0, 186 passed in 3.80s. Independent review found verified corrections
overwritten by re-extraction; regression command (CWD R):

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); os.chdir(tempfile.mkdtemp(prefix='cybersos-0B-review-red-')); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests/test_evidence_contract.py'),'-k','reextraction','-q','-p','no:cacheprovider','--tb=short']))"
```

Exit 1, 2 failed / 16 deselected in 0.63s. Final 188-test pass includes these
regressions after HTTP 409 protects verified data. Approved execution was used
because the audited Windows sandbox could not open temporary files.

### Frontend (R2)

CWD R/frontend, independent commands:

```powershell
node --test __tests__/api-contract.test.cjs
npm run lint
npm run build
```

Actual: Node exit 0, **4 passed**; lint exit 0, no warnings/errors; build exit 0,
compilation/type/lint checks, five static pages/build traces. Node exercises real
transpiled API: 204 deletes, preview origin, list/verify responses, failed deletes.
Initial sandbox spawn EPERM required approved retry; red retry 3 failed / 1 passed,
green retry 4 passed. No dependency/lockfile changed.

### Existing automated browser smoke

CWD R; existing production build, installed global driver and cached Chromium:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```

Approved headless-browser/local-server execution. Final **exit 0, PASS**, including
cleanup. Runner migrates fresh temporary SQLite through all three revisions to
20260930_evidence_contract; backend 8000/frontend 3001, refuses occupied ports,
terminates only owned subprocesses. scenarios.yaml drives existing guided create
→ triage/actions → vault upload → original image preview loaded from backend
origin → honest extraction failure/manual verification → description/suspect/
timeline/template summary → reload persistence → deletion. Original-file HTTP
response and mobile viewport load checked; browser errors/failed API calls fail.
No live provider contacted.

Earlier smoke passed and exited 0. Strengthened rerun passed preview/journey but
exited 1 during temporary SQLite cleanup (WinError 32). Disposing the application
engine imported by migrations after server shutdown fixed cleanup; identical final
command exited 0. The failed cleanup is not counted as a pass.

### Separate outcomes and limits

| Result class | Step 0B result |
| --- | --- |
| Local automated | PASS: 188 backend + 4 frontend contract tests, lint/build, fresh/legacy SQLite migrations, existing browser journey |
| Live-provider | NOT RUN: live AI/storage and PostgreSQL |
| Manual application | NOT RUN: automated browser is not a manual keyboard/mobile/speech pass |
| Independent review | Completed; verified-data overwrite reproduced and fixed with two regressions |

PostgreSQL tools/Docker and C:/Program Files/PostgreSQL absent; PostgreSQL DDL
inspected, execution NOT RUN. No existing database migrated. Legacy unavailable
MIME/hash remain null; new uploads calculate hashes. Real-data authorization/
retention and 0C wording/rules remain open.

Operational upgrade (documented, not executed on existing data): back up database
and evidence, set DATABASE_URL and LOCAL_STORAGE_ROOT to previous evidence
directory; CWD R/backend run `..\.venv\Scripts\alembic.exe upgrade head`.
Supported old schema: backend/tests/fixtures/legacy_schema.sql. Arbitrary schemas
need inspection. Consolidation forward-only; rollback requires backup restore.

Coverage: R1 canonical model/metadata; R2 all mounted calls/CRUD/browser; R3
startup no-DDL and preservation; R4 fresh/legacy migrations; R5 temporary
database/storage; R6 settings/defaults; R7 service-backed contracts.

Final checks, CWD R: `git diff --check` exit 0 after removing an extra EOF blank
line (initial check flagged it). Artifact/scope scanner exit 0: 39 changed/new
files checked, no modified tracked database/build cache/dependencies/rules/UI
components, no generated evidence or common secret markers. Initial documentation
checker failed because verification text named the combined R1–R7 range rather
than each literal R; explicit coverage above corrects the documentation.

Final documentation consistency command, CWD R:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; docs=[Path('docs')/n for n in ['audit.md','verification.md','phase-status.md','plans/0B.md']]; texts=[p.read_text(encoding='utf-8') for p in docs]; assert all(t.count(chr(96)*3)%2==0 for t in texts); assert all(l==l.rstrip() for t in texts for l in t.splitlines()); assert all(all('R'+str(i) in t for i in range(1,8)) for t in texts[:3]); assert all('Step 0B' in t for t in texts[:3]); assert '- [ ]' not in texts[3]; assert all('NOT RUN' in t for t in texts[:3]); print('PASS documentation: R1-R7, separate unavailable outcomes, balanced fences, whitespace, completed plan')"
```

Actual result: exit 0, PASS.

## Phase 0C current verification — 2026-09-30

This is the current developer verification recipe. Earlier 0A/0B sections are
historical run records; their shared-database warnings and capability snapshots
do not override the isolated fixtures/current README. R is the repository root.

Setup/start commands and configuration are in README.md. Backend start uses the
existing uvicorn module and Alembic CLI; frontend start uses package.json scripts.
Dependency setup commands are provided for new machines; no installation was
needed or performed in this run. Existing root .venv, frontend/node_modules and
cached Playwright/Chromium were prerequisites.

Backend, CWD R:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```
Final exit 0: **205 passed in 4.07s**. Includes five fresh/legacy migration cases
and all 25 frontend method/path OpenAPI contracts, full incident/evidence/suspect/
timeline APIs, absent-provider fallback and 17 new 0C regression cases.
Session-private temporary SQLite/evidence are automatically managed by conftest.

Failures retained honestly:
- Before implementation, same command restricted to backend/tests/test_phase0c_truth.py:
  exit 1, 15 failed in 0.33s.
- Targeted command with test_phase0c_truth.py, test_action_rules.py,
  test_action_plan.py, test_triage.py and test_incidents_api.py: exit 0,
  173 passed in 1.35s.
- First full run: exit 1, 204 passed / 1 failed in 4.53s; remaining legacy
  complaint test still required amount-based fraud-desk escalation. Updated that
  test to require absence; final identical full command passes all 205.
Approved execution was required for Windows temporary-file access.

Frontend, CWD R/frontend:
```powershell
node --test __tests__/api-contract.test.cjs
npm run lint
npm run build
```
All exit 0: **4 contract tests passed**, lint no warnings/errors, production
compilation/types/lint/static generation/build traces completed.

Standalone fresh database CLI migration, CWD R:
```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,subprocess,sys; from pathlib import Path; root=Path.cwd(); tmp=tempfile.TemporaryDirectory(prefix='cybersos-0C-fresh-'); env=dict(os.environ,DATABASE_URL='sqlite:///'+(Path(tmp.name)/'fresh.sqlite').as_posix(),LOCAL_STORAGE_ROOT=str(Path(tmp.name)/'evidence')); result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env); tmp.cleanup(); raise SystemExit(result.returncode)"
```
Exit 0; all three tracked revisions applied, ending 20260930_evidence_contract;
temporary database removed. Upgrade migration is covered by the full suite's
test_migrations.py against frozen current schema unversioned and stamped at either
prior revision, including original incident/evidence/file preservation.
SQLite verified; PostgreSQL execution NOT RUN. No existing user database upgraded.

Synthetic real-browser journey, CWD R:
```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```
Approved local servers/headless browser, final exit 0, PASS. Uses real migrated
temporary DB/storage and production frontend. create -> triage -> action plan ->
safe PNG upload -> list/original preview -> suspect -> timeline -> delete all
pass. Also verifies manual correction, description/template summary persistence,
204 responses, backend-origin preview and mobile load. Added null recovery field,
no bank-desk action and no recovery-window UI assertions. No live government or
provider requests; no fabricated extraction success.

Hygiene commands, CWD R:
```powershell
git rm --cached -- test.db frontend/tsconfig.tsbuildinfo
git diff --check
git diff --cached --check
git status --short --untracked-files=all
git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.tsbuildinfo' '.env' 'backend/.env' 'frontend/.env.local'
git check-ignore test.db frontend/tsconfig.tsbuildinfo backend/evidence/synthetic-proof.png
```
All exit 0. Generated files removed from index, local bytes preserved. Tracked
artifact listing empty; ignore check identifies all three. Existing 0B and AGENTS
changes preserved. No dependency/legitimate migration/synthetic fixture removed.
Review includes common secret-marker scan of changed/new source and documentation;
local .env/databases/evidence contents are not read or exposed.

### Manual smoke to perform (NOT RUN by agent)

1. Start the backend and frontend using README commands with synthetic local
   SQLite/storage. Open the frontend and choose the existing financial flow.
2. Use synthetic amount 2500, UPI and a recent time; create/triage and view the
   action plan. Confirm no recovery prediction, FIR amount gate or outcome promise.
3. Open the evidence vault, upload a harmless synthetic PNG/text file, list it,
   open its original preview and verify metadata.
4. If extraction is unavailable, enter synthetic corrections and confirm them.
5. Add a synthetic suspect phone/UPI identifier and timeline event.
6. Reload to check persistence; delete the evidence and confirm it disappears.
   Check the linked original is unavailable after deletion.
7. Repeat keyboard-only and on a mobile viewport. Do not submit anything to an
   official service or use real citizen data.

| Outcome | Result |
| --- | --- |
| Local automated | PASS: full backend, frontend contracts/lint/build, fresh/legacy SQLite migration, synthetic browser |
| Live-provider | NOT RUN: cloud AI/storage and PostgreSQL |
| Manual | NOT RUN: checklist above is for the user |
| Phase 1 | NOT STARTED |

No blockers for the requested local Phase 0 baseline. Production/real-data use
still requires authorization/retention and separately verified provider/PostgreSQL
paths. No commit/push/merge/deploy performed.

Final source/document review: PASS, 66 changed/new text files; common secret
markers absent, canonical links/fences/legacy labels valid, dependencies preserved.
Initial scanner included the intentionally preserved local copies of untracked
generated files; corrected scan excludes them. Passing hygiene regression and
git ls-files separately verify they are untracked. No local DB/env contents read.

## Phase 1 current verification

Executed 2026-10-01, branch phase-0. R = repository root
C:/Users/Ishan Chennupati/Downloads/cybersos. Prerequisite: recorded passing Phase
0C baseline. No commit/push/deploy or Phase 2. Current head migration is
20261001_response_foundation. Setup/start commands are in README (including
CASE_COOKIE_SECURE=false for synthetic HTTP localhost only). Existing root .venv,
frontend node_modules, Node/Next and browser package from Phase 0 were reused;
no dependency installation or cloud/government API call was made.

### Final exact commands and results

Backend, CWD R:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```
Exit 0: **288 passed in 19.65s**. Includes all golden playbooks, typed/unknown
facts, no-provider critical actions, valid source references, immutable history,
self-report completion, credential/policy checks, startup/OpenAPI/frontend
contracts, fresh metadata parity and Phase 0 -> Phase 1 migration preservation.
Cross-case matrix covers all 29 private route operations with missing and Case A
credentials against Case B (58 denials), plus route-gate coverage, owner-positive
cookie/header requests, expiry, locked legacy capability and Origin checks.
Session-private migrated SQLite and per-test temporary evidence automatically
replace shared/local database/storage; no user database is touched. Windows temp
access required approved execution. PostgreSQL execution remains NOT RUN.

Frontend, CWD R/frontend:
```powershell
node --test __tests__/api-contract.test.cjs
npm run lint
npm run build
```
All exit 0: **5 contract tests passed**, lint no warnings/errors; production
compilation, types, static generation and traces completed. Build uses existing
ignored .env.local; contents not read. Node's first sandboxed test attempt failed
with spawn EPERM; approved identical command passed. Final build includes action
instructions, cookie credentials and authorized-scam resume preservation.

Standalone fresh migration, CWD R:
```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,subprocess,sys; from pathlib import Path; root=Path.cwd(); tmp=tempfile.TemporaryDirectory(prefix='cybersos-1-fresh-'); env=dict(os.environ,DATABASE_URL='sqlite:///'+(Path(tmp.name)/'fresh.sqlite').as_posix(),LOCAL_STORAGE_ROOT=str(Path(tmp.name)/'evidence')); result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env); tmp.cleanup(); raise SystemExit(result.returncode)"
```
Exit 0: all four tracked revisions applied to 20261001_response_foundation,
then temporary database removed. Upgrade verification in the full command above:
test_phase1_migrations.py creates/stamps 20260930_evidence_contract, inserts a
synthetic incident and upgrades to head; ID/amount/description/legacy fields
survive; facts/ownership are not invented; legacy_unversioned remains locked.
test_migrations.py additionally verifies audited older schemas and original files.

Final financial synthetic browser, CWD R:
```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```
Exit 0: **PASS**. Owns disposable backend/production frontend servers and fresh
migrated SQLite/evidence, uses localhost for SameSite cookie compatibility and
CASE_COOKIE_SECURE=false. Real browser performs create -> triage -> versioned
financial action plan -> safe PNG upload -> list/view original -> suspect ->
timeline -> evidence delete. Also checks honest extraction fallback/manual verify,
description/template summary, reload persistence, 204 deletion and mobile load.
No real data/providers; processes stopped and temporary data removed. A Windows
Proactor ConnectionResetError was emitted during server shutdown after PASS;
runner exit remains 0. This is automated browser verification, NOT human manual.

Hygiene, CWD R:
```powershell
git diff --check
git diff --cached --check
git status --short --untracked-files=all
git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.tsbuildinfo' '.env' 'backend/.env' 'frontend/.env.local'
```
Normal Git checks exit 0, artifact listing empty. Changed/new text scan: 83 files,
common private-key/API-token markers and bell control characters absent. Existing
Phase 0/AGENTS work and ignored local files preserved. Diagnostic diff with
core.autocrlf=false reported CRLF as whitespace; normal repository configuration
passes, and no line-ending normalization was applied. No secret/env/database
contents inspected. No dependencies/lockfiles removed or unrelated fixes added.

### Failed/red runs retained

- Initial targeted playbook/access command: 58 failed / 8 passed (7.21s), proving
  missing domain and cross-case access leaks; some absent new routes returned 404
  before implementation, so later owner-positive tests and route coverage were added.
- Initial persistence/policy command: collection import error, then 9 failed
  after correcting the test import. Targeted implemented foundation: 80 passed.
- First full Phase 1 command: 18 failed / 262 passed; legacy tests expected removed
  recovery fields, duplicate financial rules, old gating and old action IDs. Updated
  those intentional contracts; full run then 280 passed.
- Extended full run: 1 failed / 285 passed; route enumeration incorrectly included
  public database health. Excluded health explicitly; private route gate still checked.
- Independent focused code review reproduced pending triage-field loss caused by
  populate_existing with autoflush disabled. Regression first had invalid missing
  incident_type, then reproduced transaction_status=None for a valid request.
  Fixed flush-before-refresh and status synchronization; full run 287 passed.
- Added category-change regression initially failed with invalid legacy category
  fixture (missing subcategory/details/date/location); corrected using existing
  validation requirements. Final complete run above passes all 288.

### Manual tests for the user (NOT RUN)

1. Start backend/frontend from README with synthetic SQLite/evidence, HTTP cookie
   override and BOTH hosts localhost. Open http://localhost:3000.
2. Create an approved scam-transfer case through the existing guided flow. Confirm
   bank wording says payment approved after deception; no recovery prediction.
3. Open evidence vault, upload harmless synthetic PNG/text, list and preview it,
   correct/verify extraction if unavailable, add synthetic suspect/timeline, reload
   and delete evidence. Confirm the deleted original is unavailable.
4. Open that case URL in incognito/new browser without its cookie. Private case,
   evidence and other resources must be unavailable (backend 404). A UUID link must
   not restore access. Repeat in mobile/keyboard use.
5. Same-browser reload should retain access until cookie/server expiry. Clearing
   cookies loses access; there is no implemented account/capability recovery.
6. API owner clients can PUT /api/v1/incidents/{id}/facts with kind
   financial_scam_transfer, unauthorized_financial_transaction or
   financial_authorization_unknown. Keep the capability in cookie/header only.
   Check plans/revision history; POST plan/action completion and confirm
   meaning=user_self_report. This API foundation has no new chat/completion UI.

| Result category | Outcome |
| --- | --- |
| Local automated | PASS: backend/contract/lint/build/fresh/Phase 0 upgrade/private matrix/financial browser |
| Live-provider | NOT RUN: AI/cloud storage/PostgreSQL; official web source review is not provider verification |
| Manual | NOT RUN: user checklist above |
| Phase 2 | NOT STARTED |

Remaining limitations: legacy cases stay locked without owner-verified recovery;
capabilities expire; no returning-user authentication/retention readiness; evidence
policy is not semantic image moderation or complete credential detection. No
blocker remains for this local synthetic Phase 1 acceptance scope.

## Phase 1 live-development follow-up: missing playbook_id

2026-10-01: user reported live POST /api/v1/incidents -> 500, SQLite
OperationalError: incidents has no column named playbook_id. The terminal's
DATABASE_URL override used backend/local.sqlite at 20260930_evidence_contract;
a separate shell defaulted to PostgreSQL. Only read-only schema inspection was
performed on that PostgreSQL connection; it was not migrated or changed.

R1 diagnosis DONE: read traceback, checked running health and local SQLite schema.
R2 fix DONE: SQLite backup saved under ignored backend/tmp/migration-backups/
local-before-phase1-20261001-012002.sqlite; applied existing tracked revision to
20261001_response_foundation. Before/after comparison confirmed every pre-existing
incident field unchanged. No application code, new migration or data reset.

Execution CWD backend: root .venv interpreter invoked as
..\.venv\Scripts\python.exe - with a Python stdin wrapper that used sqlite3.backup,
set DATABASE_URL to the absolute backend/local.sqlite path, cleared Settings cache,
and called alembic.command.upgrade(Config('alembic.ini'), 'head'). Exit 0.
Equivalent developer migration command (use the same DATABASE_URL as the server):
```powershell
$env:DATABASE_URL='sqlite:///./local.sqlite'
..\.venv\Scripts\python.exe -m alembic upgrade head
```

R3 verification DONE: CWD root, .\.venv\Scripts\python.exe - with urllib live
synthetic probes: create 201, authorized financial triage 200, typed action plan
200 with financial_scam_transfer/contact_bank_scam, anonymous case GET 404. Exit 0.
Only the generated synthetic verification incident and its cascading plans were
removed afterwards; existing cases untouched. Live server stayed running; no
restart required. Existing legacy cases remain locked under the Phase 1 policy.

Local live automated PASS. Human manual NOT RUN. Live-provider/PostgreSQL migration
NOT RUN. This is a runtime database upgrade fix, not Phase 2. No commit/push/deploy.

## Repository cleanup and structure follow-up

2026-10-01, branch phase-0, plan docs/plans/repository-cleanup.md. User authorized
cleanup/reorganization and asked to avoid unnecessary tests; no commit or push.

| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 hygiene | done | Two unreferenced category/redirect components removed; obsolete root/backend test.db, old build metadata, caches and empty docs/docs removed; .gitignore covers .swc/.next-check and SQLite sidecars. Active local.sqlite/evidence/backup/env/dependencies preserved |
| R2 backend structure | done | incident_service.py reduced 536 -> 259 lines; complaint labels/formatting in incident_presentation.py; legacy nonfinancial behavior in legacy_incident_service.py; direct formatting imports avoid summary/evidence coupling |
| R3 frontend structure | done | Intake page reduced 490 -> 148 lines; existing controller logic in features/incident-intake/use-incident-flow.ts; duplicate time callbacks consolidated; no behavior/UI/API or Phase 2 change |
| R4 tests/verification | done | Duplicate 48-case legacy matrix merged, retaining both sets of assertions: 288 -> 240 passing cases. Access, migration, golden rules and smoke coverage retained. Existing claim scan extended to feature modules; no extra test cases added |

Targeted intermediate checks passed: 17 hygiene tests, 67 complaint/compatibility/
versioned API tests; frontend lint and TypeScript checks. Final commands:

CWD repository root:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```
Exit 0: **240 passed in 15.43s**, including migration/private-route matrices.

CWD frontend:
```powershell
npm run lint
node node_modules/typescript/bin/tsc --noEmit --incremental false
node --test __tests__/api-contract.test.cjs
```
All exit 0: no lint/type errors; five API contracts passed.

Isolated production build, CWD frontend, exact wrapper:
```powershell
$taskTsconfig = [IO.File]::ReadAllBytes((Join-Path (Get-Location).Path 'tsconfig.json')); $env:CYBERSOS_BUILD_DIR='.next-check'; $env:NEXT_PUBLIC_API_URL='http://localhost:8001'; try { npm run build; $taskBuildExit = $LASTEXITCODE } finally { [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path 'tsconfig.json'), $taskTsconfig) }; exit $taskBuildExit
```
Exit 0, compiled/types/lint/static generation/traces completed. Initial isolated
build with default API port also passed (nonblocking existing Newsreader fallback
metrics warning); rebuilt for alternate smoke port. Next's generated tsconfig
include change was restored byte-for-byte. Live .next/development servers untouched.

Final synthetic browser, CWD root:
```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```
Exit 0, PASS create/triage/versioned actions/upload/list/preview/extraction fallback/
verify/description/suspect/timeline/summary/reload/delete/mobile. Fresh temporary
migrations pass; synthetic DB/evidence and owned alternate-port servers removed.
Runner ports configurable; refuses occupied ports and never stops/reuses user servers.

Final source eligibility scan: no generated/private files eligible for Git and no
common secret markers; public .env.example credentials are explicitly examples.
An initial scanner wrongly flagged legitimate frontend evidence components and
sample DSNs; corrected to runtime directory prefixes and actual token patterns.
Caches/build metadata may regenerate during tools; they remain ignored. Git diff
and staged diff checks pass. Source/docs links/fences reviewed. No unrelated source
or real data removed; legitimate migrations/fixtures/locks/history retained.

Local automated PASS. Manual/live providers NOT RUN. No Phase 2, commit or push.
Manual check: repeat the existing synthetic financial flow and evidence operations;
incognito private-case access must still be denied. No new product behavior to test.

## Phase 2 current verification

Executed 2026-10-01 on the existing main branch, without branch creation, commit,
push or deployment. Synthetic temporary SQLite/evidence only. Phase 2 acceptance
is complete locally; no Phase 3 or live understanding work was started.

Final backend command, CWD repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```

Exit 0: **254 passed in 11.47s**. Includes ten Phase 2 tests: progression,
known-fact suppression, unknown answers, correction/history/branch changes, early
actions, duplicate/reused IDs, simultaneous/stale replies, completion retry,
refresh, rollback/retry, unsupported input and frontend/backend shape contracts.
The private-resource matrix includes both new endpoints with missing and wrong-case
authority. Fresh metadata parity and prior Phase 1 upgrade tests pass.

Targeted commands actually run during development, CWD root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_phase2_conversation.py -c backend/pytest.ini -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest backend/tests/test_phase2_conversation.py backend/tests/test_migrations.py -c backend/pytest.ini -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest backend/tests/test_evidence_contract.py backend/tests/test_phase1_access.py -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```

Latest targeted results: 10, 12 (before later test additions), and 81 passed,
respectively. Initial tests failed with missing conversation routes, then passed
after implementation. The first full run reported 246 passed / two old inventory
assertions failed; inventories now cover the new endpoints and single/double-quoted
frontend methods. New fixture assertions were corrected for numeric Decimal
equivalence and existing nonfinancial create validation before the final full run.

Frontend checks, CWD frontend:

```powershell
npm run lint
node node_modules/typescript/bin/tsc --noEmit --incremental false
node --test __tests__/api-contract.test.cjs
```

Exit 0: no lint/type errors; **7 API contracts passed**, including preserved turn
IDs, revision, unknown values, cookie authority and failure/timeout/stale errors.
The final build after review fixes also runs lint/type checks:

```powershell
$taskTsconfig = [IO.File]::ReadAllBytes((Join-Path (Get-Location).Path 'tsconfig.json')); $env:CYBERSOS_BUILD_DIR='.next-check'; $env:NEXT_PUBLIC_API_URL='http://localhost:8001'; try { npm run build; $taskBuildExit = $LASTEXITCODE } finally { [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path 'tsconfig.json'), $taskTsconfig) }; exit $taskBuildExit
```

Exit 0: compile, lint, types, static generation and traces completed. Original
tsconfig restored. First build warned about existing Newsreader font override
metrics; final rebuild passed. Existing development build/server left untouched.

Browser commands, CWD root, using the already installed Playwright:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; $env:SMOKE_JOURNEY='__tests__/conversation-journey.cjs'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; $env:SMOKE_JOURNEY='__tests__/smoke-journey.cjs'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```

Both exit 0. Phase 2 passes shortcut-save failure/recovery to canonical URL, early
actions before amount/reference/upload, keyboard/focus, one active question,
unknown, disconnected save/retry, server commit with lost response/idempotent
retry, stale second tab, financial progression, correction, completion persistence,
refresh, draft/edit return, narrow viewport and unauthorized API reads/writes.
The existing journey passes conversation intake -> actions/draft -> upload/private
preview -> honest extraction failure/manual verification -> description/suspect/
timeline/template summary -> reload -> deletion/mobile. No page errors.
Initial browser harness failures were an ambiguous Next route-announcer selector
and an immediate checkbox assertion before server save; corrected to specific
error text and server-confirmed completion. No fake successful save was added.

OS temporary-directory and child-process operations initially failed under the
sandbox; the same checks were rerun with approved escalation. Isolated migration
and browser servers were disposed. Final git status/diff inspected for generated
data, secrets and unrelated changes; only intended source/tests/docs remain.

Manual checks (NOT RUN by a human): migrate an existing local database with
`alembic upgrade head` from backend, start local services, select Money is gone,
answer Not sure, correct payment approval, check an action and refresh. Open the
same case in two tabs and verify stale replies require review. Disconnect/retry a
reply. Verify draft edit links return to that case; test keyboard/screen reader and
incognito access denial. Use synthetic data.

PostgreSQL execution, human screen-reader checks, live providers and external
official actions: **not run**. Existing case authority/cookie expiry assumptions
are retained. Unsaved drafts are in memory and do not survive refresh; saved turns
do. Retention/deletion/account recovery readiness for real citizen data remains
outside Phase 2. No free-text AI/Gemini/voice or Phase 3 was added.

## Phase 2 UX repair verification

Executed 2026-10-01 on the existing main branch and uncommitted Phase 2 working
tree. Scope: action/question presentation and interaction hierarchy only. No
controller, API, playbook or migration changes. The existing backend critical
field is now represented in the frontend ActionItem type. No LLM or Phase 3.

Compared HEAD's result-screen.tsx with the current conversation: the old large
urgency banner, numbered rows and compact call/source controls were clearer than
Phase 2's flat unnumbered cards. The repair adapts those patterns into a dedicated
ACT NOW panel, quieter later-phase disclosures and a separate active question.
Desktop is two-column/sticky; mobile is single-column/actions-first with sticky
actions/question links. History is available through a disclosure. Completion
keeps focus and retains the existing self-report boundary.

Commands actually run (PowerShell), CWD repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_phase2_conversation.py backend/tests/test_phase1_playbooks.py backend/tests/test_phase1_access.py -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```

Exit 0: **84 passed in 6.84s**. Full backend suite was **not rerun** for this UI
repair; relevant conversation, deterministic playbook and authority checks passed.

CWD frontend:

```powershell
npm run lint
node node_modules/typescript/bin/tsc --noEmit --incremental false
node --test __tests__/action-panel.test.cjs __tests__/api-contract.test.cjs
```

Exit 0: lint/type checks passed; **9 tests passed** (two new presentation tests,
seven existing API contracts). Presentation tests render actual ResponseActions
from existing golden backend scenarios, checking distinct action sections, server
order/numbering, one card per action, self-report completion and official sources.
Initial new tests failed because the panel was absent, then passed after repair.

Final isolated production build, CWD frontend:

```powershell
$taskTsconfig = [IO.File]::ReadAllBytes((Join-Path (Get-Location).Path 'tsconfig.json')); $env:CYBERSOS_BUILD_DIR='.next-check'; $env:NEXT_PUBLIC_API_URL='http://localhost:8001'; try { npm run build; $taskBuildExit = $LASTEXITCODE } finally { [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path 'tsconfig.json'), $taskTsconfig) }; exit $taskBuildExit
```

Exit 0: compile, lint, types, static generation and traces passed. Rebuilt after
review fixes for stale input and sticky-nav scroll offset. tsconfig restored;
existing development build/services untouched.

Final browser/API journey, CWD root:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; $env:SMOKE_JOURNEY='__tests__/conversation-journey.cjs'; $env:SMOKE_SCREENSHOT_DIR=Join-Path (Get-Location).Path 'tmp/phase2-ux'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```

Exit 0. Passed ACT NOW visible on initial mobile screen; action IDs/order/numbers
match the current API plan; cards are outside conversation history; no duplicates;
early actions persist into reporting questions; keyboard jumps and heading offset;
live action announcements; completion focus/state; unknown/correction/refresh;
320px single-column and 1280px sticky-panel layout; disconnect/idempotent retry,
lost response, stale-tab and stale text-field protection; draft edit return; authority.
No page errors. Existing broader evidence journey was **not rerun** for this repair.

Browser regression reproduced stale amount text carrying into the transaction
reference after 409. Resetting text on active-field changes fixed it without moving
completion focus. Review also caught heading scroll margin missing on the element
targeted by the mobile shortcut; heading offset is now tested with history expanded.

Two browser runs passed their application checks but exited 1 during Windows
temporary SQLite cleanup. A temporary diagnostic showed zero usable connections;
garbage collection of remaining objects released the lock and exited 0. The runner
now collects leftover migration objects after disposing its engine; final normal
runner exits 0. No application backend changes were made for cleanup. Diagnostic
script removed. Synthetic screenshots under ignored tmp/ were visually inspected:
ACT NOW and numbered first step are prominent; active question uses a separate
calm card; mobile shortcuts remain visible while answering.

Manual repeat, using synthetic data: start Money is gone; check the prominent
ACT NOW and numbered steps before answering. On desktop compare the question and
sticky response plan. On mobile scroll to the question, then use actions/question
shortcuts. Choose Not sure, mark a step done, correct payment approval and refresh.
Verify current plan updates and completion persists; test keyboard focus after
completion, expand explanation/source and saved history, and check at 320px.

Human screen-reader testing, user study with frightened citizens and live providers
were **not run**. The renderer retains the existing approved instructions verbatim,
so some cards remain longer than the illustrative mockup. Later phases/history are
collapsed by default. Existing synthetic-data, cookie expiry and in-memory unsaved
draft limitations remain. No claim of government action or recovery is made.

## Final response-plan grouping requirement (2026-10-01)

Exactly four supported action groups: ACT NOW (server CONTAIN phase and server
critical REPORT actions), PRESERVE, remaining REPORT actions, FOLLOW THROUGH
(server FOLLOW_UP phase). No CONTAIN or UNDERSTAND section; empty groups omitted.
Existing action.order retained within each group. Completed applicable actions
stay visible. Questions now use neutral surface/border styling rather than green.
No API, playbook, persistence or migration changes. The current financial playbook
returns all four groups initially; later-group disclosures do not create new
applicability gates or withhold approved actions. Truly later applicability
requires a separately scoped playbook change.

New component regression uses subsets of real ResponseActions to check progressive
groups, empty plan, completed actions and shuffled-input ordering. Expanded real
browser assertions compare each group's IDs/order to the API and check neutral
question styling through turns, correction and refresh.

Commands run from frontend, all exit 0:

```powershell
node --test __tests__/action-panel.test.cjs __tests__/api-contract.test.cjs
npm run lint
$taskTsconfig = [IO.File]::ReadAllBytes((Join-Path (Get-Location).Path 'tsconfig.json')); $env:CYBERSOS_BUILD_DIR='.next-check'; $env:NEXT_PUBLIC_API_URL='http://localhost:8001'; try { npm run build; $taskBuildExit = $LASTEXITCODE } finally { [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path 'tsconfig.json'), $taskTsconfig) }; exit $taskBuildExit
```

10 tests passed (3 component, 7 API contract); lint clean; build includes successful
lint/type validation and static-page generation. Initial regression failed before
the grouping fix, then passed.

Real browser journey from repository root, exit 0:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; $env:SMOKE_JOURNEY='__tests__/conversation-journey.cjs'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```

Backend unit suite not rerun for this frontend-only follow-up. Human screen-reader
testing not run. Manual check: start a synthetic financial case; verify ACT NOW and
expand PRESERVE, REPORT and FOLLOW THROUGH, each with only applicable steps. Mark
done, correct payment approval and refresh: completion and current actions remain.
Unanswered question should be neutral. Repeat at 320px using sticky shortcuts.
