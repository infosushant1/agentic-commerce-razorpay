# Agentic Commerce — Razorpay AI Growth Agent

A judge-ready Razorpay Buildathon Track 01 project.

## 🌐 Live Demo
### 👉 [Open LedgerIQ Live Demo](https://agentic-commerce-track01.onrender.com)

## What it demonstrates

1. **Agent-readable catalog** — 18 structured products across laptops, monitors, accessories, audio, tablets and networking, with inventory, pricing and related-product graph.
2. **Conversational commerce agent** — understands shopping intent and recommends products.
3. **Upsell / cross-sell** — recommends bounded add-ons with an explicit reason.
4. **Gated money action** — the agent never silently creates a payment. It prepares a checkout and requires confirmation.
5. **Razorpay Test Mode** — creates a real Razorpay Test Mode Payment Link when API credentials are configured.
6. **Campaign orchestrator** — generates a bounded campaign plan from catalog/inventory signals.
7. **Audit trail** — every recommendation and money action is recorded.
8. **Graceful failure** — Razorpay API errors fall back to a safe demo checkout state; the agent does not pretend payment succeeded.
9. **Agent-readable merchant feed** — `/api/agent/catalog` exposes machine-readable commerce data.

## Stack

- FastAPI + Pydantic
- React + Vite
- SQLite
- Razorpay REST API
- No LLM is required for the core demo: the agent policy is deterministic, explainable and bounded.
- Optional LLM can be added later without changing the payment safety layer.

## Run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Razorpay Test Mode

Create Test Mode API keys in the Razorpay Dashboard and put them in `backend/.env`:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
```

The backend uses the Razorpay REST API. Payment Links are created only after the user confirms the proposed checkout.

Razorpay documents Payment Links at:
https://razorpay.com/docs/api/payments/payment-links/

The app intentionally does **not** report a payment as successful merely because a Payment Link was created. Payment success should be verified through Razorpay's payment flow/webhooks.

## Production build

```powershell
cd frontend
npm run build

cd ..
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

FastAPI serves `frontend/dist` automatically when it exists.

## Docker

```powershell
docker build -t agentic-commerce .
docker run -p 8000:8000 --env-file backend/.env agentic-commerce
```

Then open:

`http://localhost:8000`

## UI behavior

The AI Buyer now returns up to 6 relevant products and prioritizes exact product/category/tag matches over generic rating. The Catalog tab includes search and category filters. The Growth tab always shows a **Generate campaign** button and then changes it to **Regenerate campaign** after generation.

## Demo script

1. Ask: **"I need a laptop for college under 70000"**
2. Agent returns a primary recommendation and explains why.
3. Ask: **"What should I add?"**
4. Agent suggests a bounded cross-sell.
5. Click **Prepare checkout**.
6. Review the item, total, reason and safety gate.
7. Click **Confirm & create Razorpay test checkout**.
8. The app opens the generated Test Mode payment link.
9. Open **Audit Trail** and show the complete decision trail.
10. Open **Campaigns** and show the revenue-growth plan.
11. Demonstrate graceful failure by temporarily using invalid Razorpay credentials: the UI reports that payment creation failed and does not claim success.

## Architecture

```text
Customer / AI Buyer
        |
        v
React Commerce UI
        |
        v
FastAPI Agent Orchestrator
  |       |        |
  |       |        +--> Audit DB
  |       |
  |       +----------> Growth / Campaign Engine
  |
  +------------------> Catalog / Recommendation Engine
  |
  +------------------> Razorpay Test API
                           |
                           v
                    Payment Link
```

## Safety model

Every money action follows:

`intent -> recommendation -> quote -> explicit confirmation -> payment-link creation -> audit`

Hard bounds:
- Maximum cart quantity per SKU: 5
- Maximum automatic discount suggestion: 15%
- No automatic payment capture
- No claim of payment success after link creation
- High-value orders require an extra confirmation state
- Razorpay failures are surfaced, not hidden

## API

- `GET /api/health`
- `GET /api/agent/catalog`
- `POST /api/agent/chat`
- `POST /api/checkout/prepare`
- `POST /api/checkout/confirm`
- `GET /api/audit`
- `GET /api/campaigns`

## Razorpay amount handling

The catalog and UI store INR prices in **rupees** (for example, `10498` means ₹10,498). Razorpay Payment Links require `amount` in the smallest currency unit, so the backend converts the confirmed total to **paise** before calling Razorpay (`10498 * 100 = 1049800`). The backend also verifies that Razorpay returns the exact expected amount before reporting the checkout as created.
