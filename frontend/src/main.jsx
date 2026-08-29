import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bot, ShoppingCart, ShieldCheck, Sparkles, ReceiptText, Megaphone, ExternalLink, CheckCircle2, AlertTriangle, Search, RefreshCw } from "lucide-react";
import "./styles.css";

const money = n => `₹${Number(n).toLocaleString("en-IN")}`;
async function api(path, options={}) {
  const r = await fetch(path, { headers:{"Content-Type":"application/json"}, ...options });
  const data = await r.json().catch(()=>({}));
  if (!r.ok) throw new Error(data.detail || data.message || "Request failed");
  return data;
}

function App(){
  const [tab,setTab]=useState("agent");
  const [message,setMessage]=useState("I need a laptop for college under 70000");
  const [chat,setChat]=useState([]); const [catalog,setCatalog]=useState([]); const [cart,setCart]=useState([]);
  const [audit,setAudit]=useState([]); const [campaign,setCampaign]=useState(null); const [quote,setQuote]=useState(null);
  const [checkoutResult,setCheckoutResult]=useState(null); const [loading,setLoading]=useState(false);
  const [catalogSearch,setCatalogSearch]=useState(""); const [category,setCategory]=useState("all");

  useEffect(()=>{ api("/api/agent/catalog").then(d=>setCatalog(d.products)).catch(console.error); api("/api/audit").then(setAudit).catch(console.error); },[]);
  const total=useMemo(()=>cart.reduce((s,x)=>s+x.product.price*x.qty,0),[cart]);
  const categories=useMemo(()=>["all",...Array.from(new Set(catalog.map(p=>p.category)))],[catalog]);
  const filteredCatalog=useMemo(()=>catalog.filter(p=>{
    const q=catalogSearch.toLowerCase().trim();
    const text=`${p.name} ${p.category} ${p.description} ${p.tags.join(" ")}`.toLowerCase();
    return (!q||text.includes(q))&&(category==="all"||p.category===category);
  }),[catalog,catalogSearch,category]);

  async function ask(text=message){
    const clean=text.trim(); if(!clean) return; setLoading(true); setChat(c=>[...c,{role:"user",text:clean}]);
    try{
      const d=await api("/api/agent/chat",{method:"POST",body:JSON.stringify({message:clean,cart:Object.fromEntries(cart.map(x=>[x.product.id,x.qty]))})});
      setChat(c=>[...c,{role:"agent",text:d.message,data:d}]);
    }catch(e){setChat(c=>[...c,{role:"agent",text:e.message}]);}finally{setLoading(false)}
  }
  function add(product){setCart(c=>{const f=c.find(x=>x.product.id===product.id);return f?c.map(x=>x.product.id===product.id?{...x,qty:Math.min(5,x.qty+1)}:x):[...c,{product,qty:1}]})}
  async function prepare(){if(!cart.length)return;setLoading(true);try{const d=await api("/api/checkout/prepare",{method:"POST",body:JSON.stringify({items:cart.map(x=>({product_id:x.product.id,quantity:x.qty}))})});setQuote(d);setCheckoutResult(null)}catch(e){alert(e.message)}finally{setLoading(false)}}
  async function confirmCheckout(){setLoading(true);try{const d=await api("/api/checkout/confirm",{method:"POST",body:JSON.stringify({confirm:true,items:cart.map(x=>({product_id:x.product.id,quantity:x.qty})),customer_name:"Demo Customer",customer_email:"demo@example.com"})});setCheckoutResult(d);api("/api/audit").then(setAudit)}catch(e){setCheckoutResult({status:"failed",message:e.message})}finally{setLoading(false)}}
  async function generateCampaign(){setLoading(true);try{setCampaign(await api("/api/campaigns"));api("/api/audit").then(setAudit)}catch(e){alert(e.message)}finally{setLoading(false)}}

  return <div className="app">
    <header><div><div className="eyebrow"><Sparkles size={15}/> RAZORPAY BUILDATHON · TRACK 01</div><h1>Agentic Commerce</h1><p className="subtitle">An AI growth agent that discovers, recommends, upsells and gates every money action.</p></div><div className="status"><span/> TEST MODE · SAFE BY DEFAULT</div></header>
    <nav>
      <button className={tab==="agent"?"active":""} onClick={()=>setTab("agent")}><Bot/> AI Buyer</button>
      <button className={tab==="catalog"?"active":""} onClick={()=>setTab("catalog")}><ShoppingCart/> Catalog</button>
      <button className={tab==="campaign"?"active":""} onClick={()=>setTab("campaign")}><Megaphone/> Growth</button>
      <button className={tab==="audit"?"active":""} onClick={()=>{setTab("audit");api("/api/audit").then(setAudit)}}><ReceiptText/> Audit Trail</button>
    </nav>

    {tab==="agent"&&<main className="grid"><section className="panel"><div className="panelTitle"><Bot/><div><h2>AI Buyer Conversation</h2><span>Intent → recommendation → bounded upsell</span></div></div>
      <div className="quickQueries"><span>Try:</span><button onClick={()=>{setMessage("show me monitors");ask("show me monitors")}}>Monitors</button><button onClick={()=>{setMessage("show me a mouse");ask("show me a mouse")}}>Mouse</button><button onClick={()=>{setMessage("I need headphones under 10000");ask("I need headphones under 10000")}}>Headphones</button><button onClick={()=>{setMessage("show me tablets");ask("show me tablets")}}>Tablets</button></div>
      <div className="chat">{chat.length===0&&<div className="empty"><Bot size={38}/><b>Ask the store agent</b><p>Try laptops, monitors, mouse, headphones, tablets, routers, chargers or “what should I add?”</p></div>}
        {chat.map((m,i)=><div key={i} className={`bubble ${m.role}`}><b>{m.role==="user"?"You":"Agent"}</b><div>{m.text}</div>{m.data?.recommendations?.length>0&&<><div className="resultLabel">{m.data.recommendations.length} relevant products</div><div className="cards">{m.data.recommendations.map(p=><ProductCard key={p.id} p={p} onAdd={()=>add(p)}/>)}</div></>}</div>)}{loading&&<div className="typing">Agent is reasoning from the merchant catalog…</div>}</div>
      <div className="composer"><input value={message} onChange={e=>setMessage(e.target.value)} onKeyDown={e=>e.key==="Enter"&&ask()}/><button onClick={()=>ask()} disabled={loading}>Ask agent</button></div>
    </section>
    <aside className="panel cart"><div className="panelTitle"><ShoppingCart/><div><h2>Checkout</h2><span>Explicit confirmation gate</span></div></div>{cart.length===0?<div className="empty small">Your cart is empty.<br/>Add a recommended product.</div>:cart.map(x=><div className="cartRow" key={x.product.id}><div><b>{x.product.name}</b><small>{x.qty} × {money(x.product.price)}</small></div><b>{money(x.qty*x.product.price)}</b></div>)}<div className="total"><span>Total</span><b>{money(total)}</b></div><button className="primary" onClick={prepare} disabled={!cart.length||loading}>Prepare checkout</button>
      {quote&&<div className="gate"><div className="gateIcon"><ShieldCheck/></div><b>Money action gated</b><p>{quote.gate.message}</p><div className="quote">Exact total: <b>{money(quote.total)}</b></div><button className="confirm" onClick={confirmCheckout} disabled={loading}>Confirm & create Razorpay Test checkout</button></div>}
      {checkoutResult&&<div className={`result ${checkoutResult.status==="created"?"success":"warning"}`}>{checkoutResult.status==="created"?<CheckCircle2/>:<AlertTriangle/>}<div><b>{checkoutResult.message}</b>{checkoutResult.short_url&&<a href={checkoutResult.short_url} target="_blank">Open Razorpay checkout <ExternalLink size={14}/></a>}</div></div>}
    </aside></main>}

    {tab==="catalog"&&<main className="wide"><div className="sectionHead"><div><h2>Agent-readable merchant catalog</h2><p>18 products across multiple categories, searchable by name, category, tags and description.</p></div><div className="pill">{catalog.length} SKUs</div></div>
      <div className="catalogTools"><div className="searchBox"><Search size={16}/><input placeholder="Search mouse, monitor, headphones, tablet…" value={catalogSearch} onChange={e=>setCatalogSearch(e.target.value)}/></div><div className="filters">{categories.map(c=><button key={c} className={category===c?"selected":""} onClick={()=>setCategory(c)}>{c}</button>)}</div></div>
      <div className="catalogCount">Showing <b>{filteredCatalog.length}</b> products</div><div className="productGrid">{filteredCatalog.map(p=><ProductCard key={p.id} p={p} onAdd={()=>add(p)}/>)}</div>
    </main>}

    {tab==="campaign"&&<main className="wide"><div className="campaignToolbar"><div><h2>Campaign Orchestrator</h2><p>Turn catalog, rating and inventory signals into a bounded growth play.</p></div><button className="primary compact" onClick={generateCampaign} disabled={loading}><RefreshCw size={15}/> {campaign?"Regenerate campaign":"Generate campaign"}</button></div>
      {!campaign?<div className="heroCard"><Megaphone size={42}/><h2>Ready to generate a growth campaign</h2><p>Click <b>Generate campaign</b> to analyze the full merchant catalog and inventory.</p><button className="primary compact" onClick={generateCampaign} disabled={loading}><Megaphone size={15}/> Generate campaign</button></div>:
      <div className="campaign"><div className="heroCard compactHero"><Megaphone size={34}/><h2>{campaign.name}</h2><p>{campaign.objective}</p><div className="campaignMeta"><span>Audience: {campaign.audience}</span><span>Expected: {campaign.expected_signal}</span></div></div><div className="two"><div className="panel"><h3>Agent actions</h3>{campaign.actions.map((x,i)=><div className="action" key={i}><CheckCircle2/> {x}</div>)}</div><div className="panel"><h3>Inventory watch</h3>{campaign.inventory_watch.map(x=><div className="stock" key={x.id}><span>{x.name}</span><b>{x.inventory} units</b></div>)}</div></div></div>}
    </main>}

    {tab==="audit"&&<main className="wide"><div className="sectionHead"><div><h2>Explainable audit trail</h2><p>Every recommendation, gate and payment attempt is recorded.</p></div></div><div className="auditList">{audit.length===0?<div className="empty small">No events yet.</div>:audit.map(a=><div className="audit" key={a.id}><div className="dot"/><div><b>{a.event.replaceAll("_"," ")}</b><span>{new Date(a.ts).toLocaleString()}</span><p>{a.reason}</p></div><strong className={a.decision}>{a.decision}</strong></div>)}</div></main>}
    <footer><span>NovaTech Agentic Commerce</span><span>Policy: bounded · explainable · gated</span><span>Razorpay Test Mode</span></footer>
  </div>
}

function ProductCard({p,onAdd}){return <div className="product"><div className="productTop"><span className="category">{p.category}</span><span>★ {p.rating}</span></div><h3>{p.name}</h3><p>{p.description}</p><div className="productBottom"><b>{money(p.price)}</b><button onClick={onAdd}>Add</button></div></div>}
createRoot(document.getElementById("root")).render(<App/>);
