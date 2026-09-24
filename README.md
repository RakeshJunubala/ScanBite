# ScanBite — food label scanner for India

Scan a packed food's barcode and get a straight answer: a 0–100 score, one verdict word
(Great · Good · Limit · Avoid), alerts for your own health profile, and better choices.
Android first. This is **sprint 1** of the MVP build plan: scan → product → score → result.

```
scanbite/
├── backend/            Python API (FastAPI): product lookup + scoring engine
│   ├── app/scoring/    the scoring engine, thresholds and the INS additive table
│   ├── app/sources/    Open Food Facts fallback client
│   ├── tests/          pytest suite
│   └── Dockerfile
├── mobile/             Android app (React Native + Expo, TypeScript)
│   └── src/            screens, API client, on-phone health alerts, demo data
└── docs/
    └── scoring-method.md   the draft method for the dietitian to review
```

## 1. Try the app on your Android phone (demo mode, no backend)

You need Node.js 20+ on your laptop and the **Expo Go** app on your phone (Play Store).

```bash
cd mobile
./setup.sh              # installs Expo and the packages that match its SDK
cp .env.example .env    # leave EXPO_PUBLIC_API_URL empty for demo mode
npm start               # shows a QR code
```

Open Expo Go on your phone and scan the QR code (phone and laptop on the same Wi-Fi).
In demo mode the app serves 8 **fictional** products. They use barcode prefix 200, which is
reserved for in-store use, so they never match a real product. Tap **Try a demo product**, or use
**Type barcode** on the scanner screen:

| Barcode | Demo product | Score |
| --- | --- | --- |
| 2000000000022 | Jowar & Millet Thins | 100 Great |
| 2000000000084 | Rolled Oats | 100 Great |
| 2000000000046 | Roasted Makhana, Peri Peri | 91 Great |
| 2000000000039 | Ragi Oat Cookies | 54 Good |
| 2000000000077 | Zero Sugar Cola | 47 Limit |
| 2000000000060 | Cola | 16 Avoid |
| 2000000000015 | Multigrain Digestive Biscuits | 14 Avoid |
| 2000000000053 | Instant Masala Noodles | 10 Avoid |

## 2. Run the backend and scan real products

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                                    # 73 tests
export OFF_USER_AGENT="ScanBite/0.1 (your-email@example.com)"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs to try the API in your browser. Then point the app at it:
in `mobile/.env` set `EXPO_PUBLIC_API_URL=http://<your laptop's Wi-Fi IP>:8000` and restart `npm start`.
Real barcodes we don't have are fetched from Open Food Facts and cached. Indian coverage there
is thin, so many products will show "Not in our database yet" until the week-3 photo flow lands.

With Docker instead:

```bash
docker build -t scanbite-api backend
docker run -p 8000:8000 -e OFF_USER_AGENT="ScanBite/0.1 (you@example.com)" -v scanbite-data:/data scanbite-api
```

### API

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Status, method version, product count |
| GET | `/v1/products/{barcode}` | Product + score (our database, then Open Food Facts). 404 `not_found` |
| GET | `/v1/products/{barcode}/alternatives` | Same category, higher score |
| GET | `/v1/search?q=` | Search by name or brand |
| POST | `/v1/score` | Score any product JSON (used by the photo flow later) |
| GET | `/v1/additives/{code}` | INS additive details, e.g. `E150d` |

## 3. Tests

| What | Command | Status when delivered |
| --- | --- | --- |
| Scoring engine, additives, ingredients, Open Food Facts mapping, storage, lookup | `cd backend && pytest -q` | 66 passed here; the 7 HTTP tests run once FastAPI is installed (73 total) |
| On-phone alerts and API client | `cd mobile && npm run test:logic` | 14 passed |
| App type check | `cd mobile && npm run typecheck` (after `setup.sh`) | Passed against stand-in types; run once for real |

**Not yet run for real:** the FastAPI routes and the app screens on a phone. The build workspace
couldn't download packages, so the first real run happens on your machine. If `setup.sh`, `npm start`
or `pytest` shows an error, paste it into our next session.

## Privacy by design

- The health profile (conditions, allergies, diet) is stored encrypted on the phone and never sent to
  the server. Alerts are worked out on the phone (`mobile/src/profile/alerts.ts`).
- The server only sees barcodes.
- Home → Watching for → Edit → "Delete my health choices" wipes the profile.

## Renaming the app

The name lives in three places: `mobile/app.json` (`name`, `slug`, `android.package`),
`EXPO_PUBLIC_APP_NAME` in `mobile/.env`, and `APP_NAME` for the API.
**The Android package ID can't change after the first Play Store upload**, so settle it before week 4.

## Next (from the build plan)

- **Week 2:** Postgres (swap `repository.py`), deploy the API to AWS Mumbai, CI/CD, custom fonts.
- **Week 3:** label-photo capture → Claude reads the label → validation → provisional score.
- **Week 4:** review tool, contributions and points, seed 500 products; open the Play account and
  start the 14-day closed test.

The scoring method is a **draft** (`docs/scoring-method.md`). A registered dietitian must review it
before public release.
