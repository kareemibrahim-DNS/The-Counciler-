// Copied from Orbit PR #122 for the project record. In Orbit these ran against the real owner files;
// here the owner values are replaced by placeholders (this repo is shared with other AI assistants).
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {brainLevel,visibleDocs,buildSystem,validateAsk,anthropicRequest} from "../functions/_lib/reselling-brain.js";
import {BRAIN_DOCS} from "../functions/_lib/reselling-brain-knowledge.js";

const owner={ok:true,owner:true,principal:{id:"owner",kind:"owner",status:"approved"},assignment:{}};
const employee={ok:true,owner:false,principal:{id:"e1",kind:"employee",status:"approved"},assignment:{role:"agent"}};
const partner={ok:true,owner:false,principal:{id:"p1",kind:"partner",status:"approved",partner_id:"x"},assignment:{role:"partner"}};

test("only the Owner and approved employees can use the Brain; partners never",()=>{
 assert.equal(brainLevel(owner),"owner");
 assert.equal(brainLevel(employee),"team");
 assert.equal(brainLevel(partner),null);
 assert.equal(brainLevel({...employee,assignment:{role:"agent",removed:true}}),null);
 assert.equal(brainLevel({...employee,assignment:{}}),null);
 assert.equal(brainLevel({ok:false}),null);
});

test("team level never receives owner-only pricing, targets or strategy",()=>{
 const team=buildSystem("team");
 assert.ok(!team.includes("COST-TABLE-ROW"),"markup table must not reach the team");
 assert.ok(!team.includes("TARGET-NUMBER"),"Q4 target must not reach the team");
 assert.ok(buildSystem("owner").includes("COST-TABLE-ROW"));
 assert.ok(team.includes("TEAM-POLICY-MARKER"),"policy reaches the team");
 assert.deepEqual(visibleDocs("partner"),[]);
});

test("layers (14 Nov): team never sees partner contacts, trackers or contract status; nobody but Sales sees the sales scope",()=>{
 const team=buildSystem("team"),owner=buildSystem("owner");
 for(const secret of ["CONTACT-NAME","TRACKER-NAME","CONTRACT-STATUS","CONTRACT-STATUS"])assert.ok(!team.includes(secret),secret);
 assert.ok(owner.includes("CONTACT-NAME"),"owner keeps the contacts");
 assert.ok(!visibleDocs("owner").some(d=>d.id==="sales-scope"));
 assert.ok(!visibleDocs("team").some(d=>d.id==="sales-scope"));
 assert.deepEqual(visibleDocs("sales").map(d=>d.id).sort(),["cycles-at-a-glance","how-to-answer","line-items-and-quotes","program-overview","sales-scope","working-with-resellers"]);
 for(const locked of ["DISCOUNT-BANDS-MARKER","PARTNER-TIER-MARKER","CONTACT-NAME","COST-TABLE-ROW"])assert.ok(!buildSystem("sales").includes(locked),locked);
 assert.ok(team.includes("DISCOUNT-BANDS-MARKER"),"the Partnerships team sees discount eligibility");
 assert.ok(team.includes("Unified billing")&&owner.includes("Unified billing"),"everyone sees the common layer");
});

test("a document with a missing or unknown audience is owner-only",()=>{
 const docs=[{id:"a",audience:"team",body:"A"},{id:"b",audience:"",body:"B"},{id:"c",audience:"everyone",body:"C"}];
 assert.deepEqual(visibleDocs("team",docs).map(d=>d.id),["a"]);
 assert.deepEqual(visibleDocs("owner",docs).map(d=>d.id),["a","b","c"]);
});

test("every generated knowledge doc has an id, audience and body",()=>{
 assert.ok(BRAIN_DOCS.length>=8);
 for(const d of BRAIN_DOCS){assert.ok(d.id&&d.body);assert.ok(["base","team","owner","sales"].includes(d.audience),d.id);}
});

test("questions and history are validated",()=>{
 assert.equal(validateAsk(null).error,"invalid_body");
 assert.equal(validateAsk({question:"  "}).error,"question_required");
 assert.equal(validateAsk({question:"x".repeat(2001)}).error,"question_too_long");
 assert.equal(validateAsk({question:"q",history:[{role:"system",content:"x"}]}).error,"invalid_history");
 const ok=validateAsk({question:"refund?",history:[{role:"assistant",content:"hi"},{role:"user",content:"a"},{role:"assistant",content:"b"},{role:"user",content:"dangling"}]});
 assert.deepEqual(ok.history,[{role:"user",content:"a"},{role:"assistant",content:"b"}]);
 const req=anthropicRequest("team",ok);
 assert.equal(req.messages.at(-1).content,"refund?");
 assert.equal(req.system[0].cache_control.type,"ephemeral");
});

test("the Brain page renders answers as text, never HTML",()=>{
 const js=readFileSync(new URL("../public/reselling-brain.js",import.meta.url),"utf8");
 assert.ok(js.includes("textContent=text"));
 assert.ok(!js.includes("innerHTML"));
});

// ---- Orbit data tools ----
import {askBrain} from "../functions/_lib/reselling-brain.js";
import {BRAIN_TOOLS,toolsFor,runTool} from "../functions/_lib/reselling-brain-tools.js";

function fakeDb(rowsBySql){
 const calls=[];
 return {calls,prepare(sql){const st={args:[],bind(...a){st.args=a;return st;},
  async all(){calls.push({sql,args:st.args});return {results:rowsBySql(sql,st.args)};},
  async first(){calls.push({sql,args:st.args});const r=rowsBySql(sql,st.args);return r[0]||null;}};return st;}};
}
const withDb=(ctx,db)=>({...ctx,db});
const viewer=(mods)=>({ok:true,owner:false,principal:{id:"e2",kind:"employee",status:"approved"},assignment:{role:"agent",ov:mods},roles:{assign:{}}});

test("Orbit tools follow the caller's own module access; the catalogue is reference data for every Brain user",()=>{
 assert.deepEqual(toolsFor(owner).sort(),["brain_catalog","orbit_arr","orbit_partners","orbit_tickets"]);
 assert.deepEqual(toolsFor(viewer({arr:"view",partners:"none"})).sort(),["brain_catalog","orbit_arr"]);
 assert.deepEqual(toolsFor(viewer({arr:"own",partners:"none"})),["brain_catalog"],"own-only ARR access does not unlock totals");
});

test("brain_catalog returns Salesforce list prices in the country's currency",async()=>{
 const out=JSON.parse((await runTool(viewer({}),"brain_catalog",{partner:"grubtech",country:"SA"})).content);
 assert.equal(out.partner,"Grubtech");
 const line=out.line_items.find(l=>l.name==="Grubtech - gOnline License [Annual]");
 assert.deepEqual([line.price,line.currency],[1421.1,"SAR"]);
 assert.ok(out.quote_rules.length>0);
});

test("brain_catalog compares partners in one category",async()=>{
 const out=JSON.parse((await runTool(viewer({}),"brain_catalog",{category:"inventory",country:"SA"})).content);
 assert.deepEqual(out.partners.map(p=>p.partner),["ShopBrain","Supy"]);
 assert.ok(out.partners.every(p=>p.entry_price&&p.entry_price.currency==="SAR"));
});

test("brain_catalog never invents a partner or a country",async()=>{
 assert.equal((await runTool(viewer({}),"brain_catalog",{partner:"Acme Delivery"})).is_error,true);
 assert.equal((await runTool(viewer({}),"brain_catalog",{partner:"Grubtech",country:"FR"})).is_error,true);
});

test("the catalogue module holds list prices only: no cost, margin or markup fields",()=>{
 const src=readFileSync(new URL("../functions/_lib/reselling-brain-catalog.js",import.meta.url),"utf8").toLowerCase();
 for(const k of ['"cost"','"margin"','"markup"','"wholesale"','"payout"','"commission"'])assert.ok(!src.includes(k),k);
});

test("runTool re-checks access even when the model asks for a tool it was not offered",async()=>{
 const db=fakeDb(()=>[{id:"p",name:"X",status:"active"}]);
 const r=await runTool(withDb(viewer({arr:"view",partners:"none"}),db),"orbit_partners",{});
 assert.equal(r.is_error,true);assert.equal(db.calls.length,0);
 assert.equal((await runTool(withDb(owner,db),"no_such_tool",{})).is_error,true);
});

test("orbit_arr validates dates, resolves partners and binds every value",async()=>{
 const db=fakeDb(sql=>sql.includes("FROM partners")?[{id:"pid-1"}]:[{category:"new_business",amount:1000,rows:2}]);
 const ctx=withDb(owner,db);
 assert.equal((await runTool(ctx,"orbit_arr",{from:"2026-13",to:"2026-12-31"})).is_error,true);
 assert.equal((await runTool(ctx,"orbit_arr",{from:"2026-12-31",to:"2026-01-01"})).is_error,true);
 const ok=await runTool(ctx,"orbit_arr",{from:"2026-10-01",to:"2026-12-31",partner:"Deliverect'; DROP TABLE x;--"});
 assert.equal(ok.is_error,false);
 const q=db.calls.at(-1);
 assert.ok(!q.sql.includes("Deliverect"),"partner names are bound, never interpolated");
 assert.deepEqual(q.args,["2026-10-01","2026-12-31","pid-1"]);
});

test("askBrain feeds tool results back and refuses tools outside the offered list",async()=>{
 const calls=[];const script=[
  {stop_reason:"tool_use",content:[{type:"tool_use",id:"a",name:"orbit_arr",input:{from:"2026-10-01",to:"2026-12-31"}},{type:"tool_use",id:"b",name:"orbit_partners",input:{}}]},
  {stop_reason:"end_turn",content:[{type:"text",text:"Q4 new business is 1000 USD (Orbit)."}]}];
 const ran=[];
 const answer=await askBrain({level:"team",ask:{question:"Q4?",history:[]},toolNames:["orbit_arr"],
  toolSchemas:Object.fromEntries(Object.entries(BRAIN_TOOLS).map(([n,t])=>[n,t.schema])),
  runTool:async(n)=>{ran.push(n);return {content:"{\"amount\":1000}"};},
  callClaude:async body=>{calls.push(structuredClone(body));return script.shift();}});
 assert.equal(answer,"Q4 new business is 1000 USD (Orbit).");
 assert.deepEqual(ran,["orbit_arr"]);
 assert.deepEqual(calls[0].tools.map(t=>t.name),["orbit_arr"]);
 const results=calls[1].messages.at(-1).content;
 assert.equal(results[0].is_error,false);assert.equal(results[1].is_error,true);
});

test("askBrain stops after a bounded number of tool turns",async()=>{
 const answer=await askBrain({level:"owner",ask:{question:"x",history:[]},toolNames:["orbit_partners"],
  toolSchemas:{orbit_partners:BRAIN_TOOLS.orbit_partners.schema},runTool:async()=>({content:"[]"}),
  callClaude:async()=>({stop_reason:"tool_use",content:[{type:"tool_use",id:"z",name:"orbit_partners",input:{}}]})});
 assert.match(answer,/too many lookups/);
});
