# 🤖 Agentic Commerce — Razorpay AI Growth Agent

> **Razorpay Buildathon · Track 01 — AI Growth & Agentic Commerce**

**Make merchants discoverable, recommendable, and transactable by AI.**

Agentic Commerce is a full-stack AI commerce prototype that connects **AI-driven product discovery, bounded upselling, merchant growth campaigns, and a safety-first Razorpay Test Mode checkout** into one end-to-end flow.

The system is designed around a simple principle:

> **An AI agent may recommend and prepare a transaction — but it must not silently move money.**

---

## 🌐 Live Demo

### 👉 [Open Agentic Commerce — Live Demo](https://agentic-commerce-track01.onrender.com)

Experience the complete flow:

**Discover → Recommend → Upsell → Confirm → Checkout → Audit**

> **Environment:** Razorpay Test Mode  
> No real money is charged.

---

## 🎥 Project Presentation

### 📄 Pitch Deck

[View the Project Presentation](./docs/track1.pdf)



---

# 🎯 The Problem

AI is becoming a new interface for commerce, but traditional merchant stores are primarily designed for human shoppers.

An AI buyer needs more than a product search box.

It needs to be able to:

- Understand natural-language shopping intent
- Discover machine-readable products
- Compare relevant products
- Recommend useful add-ons
- Prepare a transaction
- Respect spending boundaries
- Require explicit user approval
- Create a trusted payment action
- Leave an auditable decision trail

At the same time, merchants need AI to do more than answer product questions.

They need it to identify **growth opportunities** such as:

- Cross-sell opportunities
- Product bundles
- Inventory-driven campaigns
- Bounded promotional ideas

Agentic Commerce connects these two sides.

---

# 💡 The Solution

Agentic Commerce provides an **agentic commerce layer** between the merchant catalog, the AI buyer and the payment provider.

```text
                    ┌─────────────────────┐
                    │     AI Buyer        │
                    │ Natural-language    │
                    │ shopping intent     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Agentic Commerce    │
                    │     Engine          │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       Product Agent     Growth Engine      Safety Layer
             │                 │                 │
             ▼                 ▼                 ▼
        Recommend          Campaigns       Confirmation
        Upsell/Cross-sell  Bundles         Amount checks
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Razorpay Test Mode  │
                    │   Payment Link      │
                    └──────────┬──────────┘
                               │
                               ▼
                       Audit Trail

```
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



## Razorpay amount handling

The catalog and UI store INR prices in **rupees** (for example, `10498` means ₹10,498). Razorpay Payment Links require `amount` in the smallest currency unit, so the backend converts the confirmed total to **paise** before calling Razorpay (`10498 * 100 = 1049800`). The backend also verifies that Razorpay returns the exact expected amount before reporting the checkout as created.
