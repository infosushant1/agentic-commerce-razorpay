from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE / "agentic_commerce.db"))
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", BASE.parent / "frontend" / "dist"))

app = FastAPI(title="Agentic Commerce — Razorpay Growth Agent", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)

# Demo merchant catalog: deliberately broad enough to demonstrate that the
# agent can discover categories other than laptops.
PRODUCTS = [
    {"id":"LAP-001","name":"AeroBook 14","category":"laptops","price":62999,"inventory":18,"rating":4.7,"description":"14-inch lightweight laptop for college, coding and productivity.","tags":["college","coding","portable","student"],"related":["ACC-001","ACC-002"]},
    {"id":"LAP-002","name":"AeroBook Pro 15","category":"laptops","price":74999,"inventory":9,"rating":4.8,"description":"15-inch performance laptop for development, design and heavier workloads.","tags":["coding","performance","developer","design"],"related":["MON-001","ACC-003"]},
    {"id":"LAP-003","name":"CloudLite 13","category":"laptops","price":49999,"inventory":25,"rating":4.5,"description":"Compact everyday laptop for study, browsing and office work.","tags":["college","study","portable","budget"],"related":["ACC-002","ACC-003"]},
    {"id":"MON-001","name":"27-inch QHD Monitor","category":"monitors","price":21999,"inventory":12,"rating":4.8,"description":"QHD monitor for development, spreadsheets and creative work.","tags":["monitor","coding","developer","design","desk"],"related":["ACC-001","ACC-003"]},
    {"id":"MON-002","name":"24-inch FHD Monitor","category":"monitors","price":12999,"inventory":24,"rating":4.5,"description":"Affordable full-HD monitor for study, office work and home setups.","tags":["monitor","study","office","budget","desk"],"related":["ACC-001"]},
    {"id":"MON-003","name":"UltraWide 34 Monitor","category":"monitors","price":38999,"inventory":7,"rating":4.7,"description":"34-inch ultrawide display for multitasking, development and editing.","tags":["monitor","ultrawide","developer","editing","desk"],"related":["ACC-001","ACC-003"]},
    {"id":"ACC-001","name":"USB-C Dock","category":"accessories","price":4999,"inventory":40,"rating":4.6,"description":"Multi-port dock for a cleaner desk setup.","tags":["dock","usb-c","desk","productivity","coding"],"related":[]},
    {"id":"ACC-002","name":"Laptop Sleeve 14\"","category":"accessories","price":1499,"inventory":55,"rating":4.7,"description":"Protective sleeve for daily campus travel.","tags":["sleeve","college","portable","protection"],"related":[]},
    {"id":"ACC-003","name":"Wireless Mouse","category":"accessories","price":1999,"inventory":31,"rating":4.6,"description":"Low-noise wireless mouse for long work sessions.","tags":["mouse","wireless","coding","desk","productivity"],"related":[]},
    {"id":"ACC-004","name":"Mechanical Keyboard","category":"accessories","price":4499,"inventory":20,"rating":4.8,"description":"Tactile mechanical keyboard designed for programming and long typing sessions.","tags":["keyboard","mechanical","coding","typing","desk"],"related":["ACC-003"]},
    {"id":"ACC-005","name":"65W GaN Charger","category":"accessories","price":2999,"inventory":33,"rating":4.6,"description":"Compact fast charger for laptops, tablets and phones.","tags":["charger","gan","usb-c","portable","travel"],"related":[]},
    {"id":"AUD-001","name":"QuietPods ANC","category":"audio","price":6999,"inventory":22,"rating":4.7,"description":"Noise-cancelling wireless earbuds for focus, calls and travel.","tags":["earbuds","headphones","audio","anc","travel","calls"],"related":["ACC-005"]},
    {"id":"AUD-002","name":"StudioMax Headphones","category":"audio","price":8999,"inventory":14,"rating":4.8,"description":"Over-ear headphones with detailed sound for work and entertainment.","tags":["headphones","audio","music","studio","focus"],"related":["ACC-005"]},
    {"id":"AUD-003","name":"DeskSound Mini Speaker","category":"audio","price":3499,"inventory":28,"rating":4.4,"description":"Compact desktop Bluetooth speaker for music and calls.","tags":["speaker","audio","bluetooth","desk","calls"],"related":[]},
    {"id":"TAB-001","name":"NoteTab 11","category":"tablets","price":28999,"inventory":16,"rating":4.6,"description":"11-inch tablet for reading, note-taking, streaming and study.","tags":["tablet","study","notes","college","portable"],"related":["ACC-005"]},
    {"id":"TAB-002","name":"NoteTab Pro 12","category":"tablets","price":41999,"inventory":8,"rating":4.8,"description":"Premium tablet for note-taking, drawing, productivity and media.","tags":["tablet","notes","drawing","productivity","portable"],"related":["ACC-005"]},
    {"id":"NET-001","name":"AirMesh Wi-Fi 6 Router","category":"networking","price":5999,"inventory":19,"rating":4.5,"description":"Wi-Fi 6 router for stable home-office and gaming connectivity.","tags":["router","wifi","network","home","gaming"],"related":[]},
    {"id":"NET-002","name":"Gigabit Ethernet Adapter","category":"networking","price":1799,"inventory":36,"rating":4.6,"description":"USB-C gigabit adapter for fast wired network access.","tags":["ethernet","network","usb-c","adapter","coding"],"related":[]},
]

STOP_WORDS = {"i","need","want","a","an","the","for","my","me","please","can","you","show","give","some","something","with","under","below","less","than","budget","around","upto","up","to","and","or","is","of","on","in","what","should","add","buy","get"}
CATEGORY_ALIASES = {
    "laptop":"laptops","laptops":"laptops","notebook":"laptops","notebooks":"laptops",
    "monitor":"monitors","monitors":"monitors","screen":"monitors","display":"monitors",
    "mouse":"accessories","mice":"accessories","keyboard":"accessories","keyboards":"accessories",
    "charger":"accessories","chargers":"accessories","dock":"accessories","sleeve":"accessories",
    "headphone":"audio","headphones":"audio","earbuds":"audio","earbud":"audio","speaker":"audio","speakers":"audio","audio":"audio",
    "tablet":"tablets","tablets":"tablets","ipad":"tablets",
    "router":"networking","wifi":"networking","network":"networking","ethernet":"networking",
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS audit (
        id TEXT PRIMARY KEY, ts TEXT, event TEXT, actor TEXT,
        action TEXT, decision TEXT, reason TEXT, amount INTEGER, metadata TEXT
    )""")
    conn.commit(); conn.close()

def audit(event: str, actor: str, action: str, decision: str, reason: str,
          amount: int = 0, metadata: dict[str, Any] | None = None):
    conn = db()
    conn.execute("INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (str(uuid.uuid4()), now(), event, actor, action, decision,
                  reason, amount, json.dumps(metadata or {})))
    conn.commit(); conn.close()

init_db()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    cart: dict[str, int] = Field(default_factory=dict)

class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=5)

class CheckoutRequest(BaseModel):
    items: list[CheckoutItem]
    customer_name: str = "Demo Customer"
    customer_email: str = "demo@example.com"
    confirm: bool = False

def find_product(pid: str):
    return next((p for p in PRODUCTS if p["id"] == pid), None)

def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP_WORDS and len(t) > 1}

def recommend(message: str, cart: dict[str, int] | None = None):
    q = message.lower()
    qt = tokens(q)
    budget = None
    m = re.search(r"(?:under|below|less than|budget|upto|up to)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)", q)
    if m:
        budget = int(m.group(1).replace(",", ""))

    # If the user says “what should I add?”, recommend relevant add-ons to the cart.
    cart_products = [find_product(pid) for pid, qty in (cart or {}).items() if qty > 0 and find_product(pid)]
    if any(phrase in q for phrase in ["what should i add", "what can i add", "suggest an add", "add-on", "addon", "accessory"]) and cart_products:
        related_ids = {rid for p in cart_products for rid in p.get("related", [])}
        candidates = [p for p in PRODUCTS if p["id"] in related_ids and p["inventory"] > 0]
        if candidates:
            return sorted(candidates, key=lambda p: (-p["rating"], p["price"]))[:6]

    scored = []
    for p in PRODUCTS:
        name_tokens = tokens(p["name"])
        tag_tokens = set(p["tags"])
        desc_tokens = tokens(p["description"])
        score = 0
        exact_hits = qt & name_tokens
        tag_hits = qt & tag_tokens
        desc_hits = qt & desc_tokens
        category = CATEGORY_ALIASES.get(next((x for x in qt if x in CATEGORY_ALIASES), ""))

        # Exact product/name/category intent must dominate generic popularity.
        score += len(exact_hits) * 14
        score += len(tag_hits) * 8
        score += len(desc_hits) * 2
        if category and p["category"] == category:
            score += 12
        if p["category"] in qt:
            score += 12
        if any(w in qt for w in {"laptop","notebook"}) and p["category"] == "laptops":
            score += 10

        if budget is not None:
            score += 8 if p["price"] <= budget else -18

        # Rating is only a small tie-breaker now, so a 4.6 mouse cannot be
        # outranked by a 4.8 laptop for a mouse query.
        score += p["rating"] * 0.25
        if score <= 0 and qt:
            continue
        scored.append((score, p))

    if not scored:
        # Generic discovery fallback: deliberately diversify categories instead of
        # returning six laptops just because they have the highest ratings.
        diverse = []
        seen_categories = set()
        for p in sorted(PRODUCTS, key=lambda p: (-p["rating"], p["price"])):
            if p["category"] not in seen_categories:
                diverse.append(p)
                seen_categories.add(p["category"])
            if len(diverse) >= 6:
                break
        return diverse
    scored.sort(key=lambda x: (-x[0], -x[1]["rating"], x[1]["price"]))
    return [p for _, p in scored[:6]]

def upsells(product):
    out = []
    for rid in product.get("related", []):
        p = find_product(rid)
        if p and p["inventory"] > 0:
            out.append({"product": p, "reason": "A relevant add-on that complements the primary purchase."})
    return out[:3]

def quote(items: list[CheckoutItem]):
    lines, total = [], 0
    for item in items:
        p = find_product(item.product_id)
        if not p: raise HTTPException(400, f"Unknown product: {item.product_id}")
        if p["inventory"] < item.quantity:
            raise HTTPException(409, f"Only {p['inventory']} units of {p['name']} are available.")
        line = p["price"] * item.quantity; total += line
        lines.append({"product_id":p["id"],"name":p["name"],"quantity":item.quantity,"unit_price":p["price"],"line_total":line})
    if not lines: raise HTTPException(400, "Cart is empty.")
    return lines, total

@app.get("/api/health")
def health():
    return {"ok":True,"service":"agentic-commerce","mode":"test","catalog_size":len(PRODUCTS)}

@app.get("/api/agent/catalog")
def catalog():
    categories = sorted({p["category"] for p in PRODUCTS})
    return {"merchant":{"name":"NovaTech Store","currency":"INR"},"categories":categories,
            "capabilities":["recommend","upsell","checkout","campaigns"],"products":PRODUCTS,
            "policy":{"max_quantity_per_sku":5,"max_suggested_discount_percent":15,
                       "payment_requires_confirmation":True,"payment_success_requires_provider_verification":True}}

@app.post("/api/agent/chat")
def chat(req: ChatRequest):
    recs = recommend(req.message, req.cart)
    top = recs[0]
    suggestions = upsells(top)
    audit("recommendation","agent","recommend","allowed","Recommendation generated from product name, category, tags, budget and rating.",
          metadata={"query":req.message,"product_id":top["id"],"result_count":len(recs)})
    text = f"I’d recommend {top['name']} at ₹{top['price']:,}. {top['description']}"
    if suggestions:
        text += f" A useful add-on is {suggestions[0]['product']['name']} because it complements the purchase."
    return {"message":text,"recommendations":recs,"upsells":suggestions,
            "explainability":{"primary_reason":"Exact product/category/tag matches are weighted above popularity; budget is enforced as a strong constraint.","money_action":"No money action was taken."}}

@app.post("/api/checkout/prepare")
def prepare_checkout(req: CheckoutRequest):
    lines,total=quote(req.items); high_value=total>100000
    audit("checkout_prepare","customer","prepare_checkout","gated","Quote prepared; payment creation requires explicit confirmation.",total,{"items":lines})
    return {"status":"confirmation_required","currency":"INR","items":lines,"total":total,
            "gate":{"requires_confirmation":True,"high_value":high_value,"message":"Review the exact amount and explicitly confirm before creating the Razorpay Test Mode checkout."}}

@app.post("/api/checkout/confirm")
async def confirm_checkout(req: CheckoutRequest):
    if not req.confirm: raise HTTPException(400,"Explicit confirmation is required.")
    lines,total=quote(req.items)
    key_id=os.getenv("RAZORPAY_KEY_ID","").strip(); key_secret=os.getenv("RAZORPAY_KEY_SECRET","").strip()
    if not key_id or not key_secret:
        audit("payment_attempt","customer","create_payment_link","blocked","Razorpay Test credentials are not configured; no money action executed.",total)
        return {"status":"blocked","reason":"Razorpay Test Mode credentials are not configured.","safe_demo":True,
                "message":"No payment was created. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to enable Test Mode checkout."}
    # Razorpay expects INR amounts in the smallest currency unit (paise).
    # Our catalog/UI store prices in whole rupees, so ₹10,498 must be sent as
    # 1,049,800 paise — not 10,498. Sending the rupee value directly would
    # make Razorpay display ₹104.98.
    razorpay_amount = total * 100
    payload={"amount":razorpay_amount,"currency":"INR","accept_partial":False,
             "description":f"NovaTech Agentic Commerce order {uuid.uuid4().hex[:10]}",
             "reference_id":f"AGENT-{uuid.uuid4().hex[:18]}",
             "customer":{"name":req.customer_name[:100],"email":req.customer_email[:100]},
             "notify":{"sms":False,"email":True},"reminder_enable":False}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response=await client.post("https://api.razorpay.com/v1/payment_links",auth=(key_id,key_secret),json=payload)
        if response.status_code>=400:
            detail=response.text[:500]
            audit("payment_attempt","customer","create_payment_link","failed","Razorpay rejected the Test Mode request; payment was not reported as successful.",total,{"status_code":response.status_code,"detail":detail})
            return {"status":"failed","message":"Razorpay Test Mode rejected the payment-link request.","provider_status":response.status_code,"detail":detail,"payment_success":False}
        data=response.json()
        provider_amount = data.get("amount")
        if provider_amount != razorpay_amount:
            audit("payment_attempt","customer","create_payment_link","failed",
                  "Provider returned an amount different from the confirmed quote; checkout was not reported as valid.",
                  total,{"expected_provider_amount":razorpay_amount,"provider_amount":provider_amount,"payment_link_id":data.get("id")})
            return {"status":"failed","message":"Razorpay returned an unexpected checkout amount. No payment success was assumed.",
                    "payment_success":False,"expected_amount":total,"provider_amount":provider_amount}
        audit("payment_link_created","customer","create_payment_link","allowed",
              "Explicit confirmation received and Razorpay Test Mode payment link created with the exact confirmed amount.",
              total,{"payment_link_id":data.get("id"),"short_url":data.get("short_url"),"provider_amount":provider_amount})
        return {"status":"created","payment_success":False,"message":"Razorpay Test Mode checkout created for the exact confirmed amount. Payment is not yet confirmed.",
                "payment_link_id":data.get("id"),"short_url":data.get("short_url"),"amount":total,"currency":"INR","provider_amount":provider_amount}
    except Exception as exc:
        audit("payment_attempt","customer","create_payment_link","failed","Network/provider error; payment success was not assumed.",total,{"error":str(exc)[:300]})
        return {"status":"failed","message":"Could not reach Razorpay. No payment success was assumed.","payment_success":False}

@app.get("/api/audit")
def get_audit():
    conn=db(); rows=conn.execute("SELECT * FROM audit ORDER BY ts DESC LIMIT 100").fetchall(); conn.close()
    return [dict(r)|{"metadata":json.loads(r["metadata"] or "{}")} for r in rows]

@app.get("/api/campaigns")
def campaigns():
    low_stock=sorted([p for p in PRODUCTS if p["inventory"]<=12],key=lambda x:x["inventory"])
    top=sorted(PRODUCTS,key=lambda x:x["rating"],reverse=True)[:3]
    campaign={"name":"AI Buyer Ready Week","objective":"Increase qualified conversion using agent-readable offers and bounded bundles.",
              "audience":"High-intent shoppers discovered through AI buyer queries across laptops, monitors, accessories and audio.",
              "actions":["Expose structured catalog metadata to AI buyers.",f"Lead with {top[0]['name']} as the highest-rated anchor product.",
                         "Bundle each anchor with one relevant accessory; never exceed a 15% suggested discount.",
                         "Prioritise low-stock products for urgency messaging without changing the hard inventory bounds.",
                         "Use explicit checkout confirmation before every payment-link creation."],
              "inventory_watch":[{"id":p["id"],"name":p["name"],"inventory":p["inventory"]} for p in low_stock],
              "expected_signal":"Higher attach rate, broader AI-buyer discovery and measurable conversion events."}
    audit("campaign_plan","agent","campaign_orchestrate","allowed","Campaign generated from catalog, ratings and inventory signals.")
    return campaign

@app.get("/")
def root():
    index=FRONTEND_DIST/"index.html"
    if index.exists(): return FileResponse(index)
    return {"service":"Agentic Commerce API","docs":"/docs"}

if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets",StaticFiles(directory=FRONTEND_DIST/"assets"),name="assets")

@app.get("/{path:path}")
def spa(path:str):
    index=FRONTEND_DIST/"index.html"
    if index.exists() and not path.startswith("api/"): return FileResponse(index)
    raise HTTPException(404,"Not found")
