CLAUDE.md — ScanBite

A food label scanner for India. Scan a packed food's barcode and get a 0–100 score, a verdict word (Great · Good · Limit · Avoid), personal alerts for the user's health profile, and better choices. Android first; iOS comes later. Owner: Rakesh (solo founder, cloud/SRE background).

Repo layout
backend/ — Python 3.11+ FastAPI API
app/scoring/ — scoring engine (engine.py), all numbers in thresholds.py, INS additive table in data/additives.json, ingredient signals in ingredients.py
app/sources/off.py — Open Food Facts fallback client + field mapping
app/repository.py — storage (SQLite for now; Postgres in week 2 behind the same methods)
app/service.py — lookup order: our DB → Open Food Facts → cache the result
app/main.py — HTTP routes; app/models.py — Pydantic models shared by everything
app/data/sample_products.json — 8 fictional demo products
mobile/ — React Native + Expo app, TypeScript strict
src/screens/ — Onboarding, Home, Scanner, Result, Search
src/profile/alerts.ts — personal alerts, computed on the phone
src/api/client.ts — API client with demo-mode fallback; src/api/types.ts mirrors backend/app/models.py
src/demo/demoData.json — generated, never edit by hand
src/theme.ts — colours from the design canvas
docs/scoring-method.md — the draft method for the dietitian
Commands
bash
# Backend (from backend/)
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
pytest -q                                   # all backend tests
ruff check app tests scripts                # lint
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # API at :8000, docs at /docs
python scripts/export_demo.py               # regenerate mobile/src/demo/demoData.json

# Mobile (from mobile/)
./setup.sh                                  # first time only; installs SDK-matched packages
npm start                                   # Expo dev server; open in Expo Go on Android
npm run typecheck                           # tsc --noEmit
npm run test:logic                          # alerts + API client tests (node:test via tsx)

mobile/.env: empty EXPO_PUBLIC_API_URL = demo mode (no backend needed). To use the local API, set it to the laptop's Wi-Fi IP, e.g. http://192.168.1.20:8000, and restart npm start.

Ground rules (do not break without asking Rakesh)
Health data never leaves the phone. The profile (conditions, allergies, diet) lives in expo-secure-store. Never send it to the API, logs or analytics. Alerts stay in alerts.ts on the device.
No brand money. No ads, sponsored products, paid ranking or affiliate "buy" links. Alternatives are ranked by score only.
The scoring method is a DRAFT under dietitian review. Don't change numbers in thresholds.py or risk levels in additives.json unless asked. When they do change, update docs/scoring-method.md, re-run scripts/export_demo.py, and fix the tests that pin expected scores.
Information, not medical advice. App copy says "watch your sugar", never "manage your diabetes" or anything that diagnoses or treats. This keeps the Play listing out of Google's "medical app" class.
Honest data labels. Every product shows its status: verified, community (Open Food Facts), provisional (user photos) or demo. Never present community or provisional data as verified.
Demo products stay fictional. They use barcode prefix 200 (GS1 in-store range), brand "Sample Foods/Drinks". Never add real brand names or real products to demo data.
Open Food Facts is ODbL (share-alike). Keep its records marked community and separate from our verified catalogue. Send a real OFF_USER_AGENT.
Android package ID com.scanbite.app is permanent after the first Play upload. Rename (app.json name/slug/package, EXPO_PUBLIC_APP_NAME, API APP_NAME) only before week 4.
Conventions
Keep mobile/src/api/types.ts in sync with backend/app/models.py whenever a model changes.
Every behaviour change comes with a test: pytest for backend, node:test for app logic. Keep alerts.ts and client.ts free of React Native imports so they stay testable in Node.
Backend: type hints everywhere, ruff clean, line length 120. Sodium is stored in mg; nutrient values are per 100 g (food) or 100 ml (drinks).
Mobile: TypeScript strict, functional components, StyleSheet with colours from theme.ts. Touch targets at least 44 px; real accessibilityRole and labels on buttons.
User-facing text: short, plain English, no jargon; Hindi and Telugu arrive in week 6, so keep strings easy to extract.
Don't add a dependency without saying why. Install app packages with npx expo install.
Current state (sprint 1)
Done: scoring engine v0.1-draft, additive table, Open Food Facts fallback, SQLite storage, API routes, onboarding, home, scanner (camera + manual entry), result screen, search, on-phone alerts, scan history, demo mode, CI workflow.
Not yet verified on real devices: the FastAPI routes and the app screens were written without being run. Expect small fixes on the first setup.sh / npm start / pytest.
Known gaps: system fonts (canvas fonts Bricolage Grotesque + Instrument Sans to be added), no app icon or splash, SQLite only, no auth, English only.
Roadmap (build plan)
Week 2: Postgres repository, deploy API to AWS Mumbai (ap-south-1), CI/CD, fonts, icon.
Week 3: label-photo capture → Claude vision reads ingredients/nutrition → validation rules → provisional score (POST /v1/score already exists).
Week 4: review tool, contributions + points, seed 500 products; open Play Console and start the 14-day / 12-tester closed test.
Week 5: better alternatives polish, claim check ("multigrain" vs maida first, etc.).
Week 6: share card, Hindi + Telugu, public scoring-method page, dietitian review.
Week 7: speed (scan to verdict < 2 s), offline cache, budget-phone testing, store listing, release.