import {levelFor} from "../api/data.js";
import {CATALOG,PARTNERS,CATEGORIES as CATALOG_CATEGORIES,CATALOG_SOURCE} from "./reselling-brain-catalog.js";

// Read-only Orbit data tools for the Reselling Brain. Each tool checks the
// caller's own module access, so the Brain never shows more than the person
// could already open in Orbit. Nothing here writes.
// module null = reference data every Brain user may read (only Owner and approved employees reach the Brain).
const canView=(ctx,module)=>ctx.owner||module===null||["view","edit"].includes(levelFor(ctx,module));
const CURRENCY={SA:"SAR",KSA:"SAR",AE:"AED",UAE:"AED",KW:"KWD",KWT:"KWD",JO:"JOD",JOR:"JOD",EG:"EGP",EGT:"EGP",INT:"USD",USD:"USD"};
const norm=s=>String(s||"").toLowerCase().replace(/[^a-z0-9]/g,"");
function findPartner(name){
 const n=norm(name);
 if(!n)return null;
 return Object.keys(PARTNERS).find(p=>norm(p)===n)||Object.keys(PARTNERS).find(p=>norm(p).startsWith(n)||n.startsWith(norm(p)))||null;
}
function linesFor(name,cur){
 return (CATALOG[name]||[]).map(l=>({name:l.name,type:l.t,billing:l.f,...(l.desc?{description:l.desc}:{}),...(l.flag?{warning:l.flag}:{}),
  ...(cur?{price:l.p[cur]??null,currency:cur}:{prices:l.p})}));
}
function entryPrice(name,cur){
 const mains=(CATALOG[name]||[]).filter(l=>l.t==="Main"&&l.p[cur]!=null);
 const pool=mains.filter(l=>l.f==="Annual").length?mains.filter(l=>l.f==="Annual"):mains;
 if(!pool.length)return null;
 const best=pool.reduce((a,b)=>a.p[cur]<=b.p[cur]?a:b);
 return {line_item:best.name,price:best.p[cur],currency:cur};
}
const CATEGORIES=["new_business","renewal","expansion","reactivation","churn"];
const isDate=s=>typeof s==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(s);

async function partnerIdByName(ctx,name){
 if(typeof name!=="string"||!name.trim())return null;
 const row=await ctx.db.prepare("SELECT id FROM partners WHERE lower(name)=lower(?) OR id=? LIMIT 1").bind(name.trim(),name.trim()).first();
 return row?row.id:undefined;
}

export const BRAIN_TOOLS=Object.freeze({
 brain_catalog:{
  module:null,
  schema:{name:"brain_catalog",description:"Reseller catalogue: a partner's profile, quote rules and line items with LIST prices (Salesforce price book), or a side-by-side of all partners in a category. Give a country to get prices in that country's currency (SA, AE, KW, JO, EG, or INT for USD). With no input, lists categories and partners. Never contains cost or margin.",
   input_schema:{type:"object",properties:{partner:{type:"string",description:"partner name, e.g. Grubtech"},category:{type:"string",description:"category id or name, e.g. opm, inventory, loyalty"},country:{type:"string",description:"SA, AE, KW, JO, EG or INT"}},required:[]}},
  async run(_ctx,{partner,category,country}={}){
   const cur=country?CURRENCY[String(country).toUpperCase()]:undefined;
   if(country&&!cur)return {error:`unknown country '${country}'. Use SA, AE, KW, JO, EG or INT.`};
   if(partner){
    const name=findPartner(partner);
    if(!name)return {error:`partner '${partner}' is not in the reseller catalogue`,partners:Object.keys(PARTNERS)};
    const m=PARTNERS[name];
    return {source:CATALOG_SOURCE,partner:name,category:(CATALOG_CATEGORIES.find(c=>c.id===m.cat)||{}).name,inactive:Boolean(m.inactive),
     overview:m.overview,best_for:m.bestFor,edge:m.edge,licensing_unit:m.unit,countries:m.countries,quote_rules:m.rules,watch_out:m.watch,
     submission_form:m.form,ksa_approval_form:m.ksaForm,slack:m.slack,line_items:linesFor(name,cur)};
   }
   if(category){
    const c=CATALOG_CATEGORIES.find(x=>norm(x.id)===norm(category)||norm(x.name).includes(norm(category)));
    if(!c)return {error:`category '${category}' not found`,categories:CATALOG_CATEGORIES.map(x=>({id:x.id,name:x.name}))};
    return {source:CATALOG_SOURCE,category:c.name,how_to_choose:c.pick,partners:c.partners.filter(p=>PARTNERS[p]).map(p=>{const m=PARTNERS[p];
     return {partner:p,inactive:Boolean(m.inactive),best_for:m.bestFor,edge:m.edge,licensing_unit:m.unit,countries:m.countries,watch_out:m.watch,...(cur?{entry_price:entryPrice(p,cur)}:{})};})};
   }
   return {source:CATALOG_SOURCE,categories:CATALOG_CATEGORIES.map(c=>({id:c.id,name:c.name,partners:c.partners}))};
  }
 },
 orbit_partners:{
  module:"partners",
  schema:{name:"orbit_partners",description:"List reseller partners in Orbit with their status.",input_schema:{type:"object",properties:{},required:[]}},
  async run(ctx){
   const r=await ctx.db.prepare("SELECT id,name,status FROM partners ORDER BY name LIMIT 200").all();
   return {partners:r.results||[]};
  }
 },
 orbit_arr:{
  module:"arr",
  schema:{name:"orbit_arr",description:"ARR totals in Orbit by category (new_business, renewal, expansion, reactivation, churn) for a date range, optionally for one partner. Amounts in USD as stored in Orbit.",
   input_schema:{type:"object",properties:{from:{type:"string",description:"YYYY-MM-DD"},to:{type:"string",description:"YYYY-MM-DD"},partner:{type:"string",description:"partner name or id, optional"},by_month:{type:"boolean"}},required:["from","to"]}},
  async run(ctx,{from,to,partner,by_month}){
   if(!isDate(from)||!isDate(to)||from>to)return {error:"from and to must be YYYY-MM-DD with from <= to"};
   const where=["pm.period_date>=?","pm.period_date<=?"],args=[from,to];
   if(partner){
    const id=await partnerIdByName(ctx,partner);
    if(!id)return {error:`partner '${partner}' not found`};
    where.push("pm.partner_id=?");args.push(id);
   }
   const month=by_month?"substr(pm.period_date,1,7) AS month,":"";
   const group=by_month?"GROUP BY month,pm.category ORDER BY month":"GROUP BY pm.category";
   const r=await ctx.db.prepare(`SELECT ${month}pm.category,ROUND(SUM(pm.amount),2) AS amount,COUNT(*) AS rows FROM partner_metrics pm WHERE ${where.join(" AND ")} ${group}`).bind(...args).all();
   return {from,to,partner:partner||"all",categories:CATEGORIES,totals:r.results||[]};
  }
 },
 orbit_tickets:{
  module:"partners",
  schema:{name:"orbit_tickets",description:"Partner Slack ticket counts in Orbit by partner, country and status (open/closed), optionally for one partner.",
   input_schema:{type:"object",properties:{partner:{type:"string"}},required:[]}},
  async run(ctx,{partner}={}){
   const where=[],args=[];
   if(partner){
    const id=await partnerIdByName(ctx,partner);
    if(!id)return {error:`partner '${partner}' not found`};
    where.push("t.partner_id=?");args.push(id);
   }
   const r=await ctx.db.prepare(`SELECT p.name AS partner,t.country_code,t.status,COUNT(*) AS tickets,MIN(t.opened_at) AS oldest_opened FROM partner_slack_tickets t JOIN partners p ON p.id=t.partner_id ${where.length?"WHERE "+where.join(" AND "):""} GROUP BY p.name,t.country_code,t.status ORDER BY p.name LIMIT 300`).bind(...args).all();
   return {tickets:r.results||[]};
  }
 }
});

export function toolsFor(ctx){
 return Object.entries(BRAIN_TOOLS).filter(([,t])=>canView(ctx,t.module)).map(([name])=>name);
}

export async function runTool(ctx,name,input){
 const tool=BRAIN_TOOLS[name];
 // Re-check access on every call: the model may ask for a tool it was not offered.
 if(!tool||!canView(ctx,tool.module))return {content:`Tool '${name}' is not available to you.`,is_error:true};
 try{
  const out=await tool.run(ctx,input&&typeof input==="object"?input:{});
  const text=JSON.stringify(out);
  return {content:text.length>20000?text.slice(0,20000)+"…[truncated]":text,is_error:Boolean(out&&out.error)};
 }catch{return {content:"Tool error: Orbit data is unavailable right now.",is_error:true};}
}
