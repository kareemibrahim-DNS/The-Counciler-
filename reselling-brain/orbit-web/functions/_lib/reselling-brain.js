import {BRAIN_DOCS} from "./reselling-brain-knowledge.js";

// Reselling Brain: answers reseller-program questions from the shared knowledge
// files. Audience layers are a placeholder until the Owner defines them:
// Owner sees everything, approved employees see "team" files, partners get nothing.
export const BRAIN_MODEL_DEFAULT="claude-sonnet-5-5";
export const BRAIN_DAILY_LIMIT_DEFAULT=200;
export const MAX_QUESTION=2000;
export const MAX_HISTORY_TURNS=10;

export function brainLevel(ctx){
 if(!ctx||!ctx.ok)return null;
 if(ctx.owner)return "owner";
 if(ctx.principal?.kind==="employee"&&ctx.principal.status==="approved"&&ctx.assignment?.role&&!ctx.assignment.removed)return "team";
 return null; // partners and anyone else: no access (fail closed)
}

// Layers (Kareem, 14 Nov 2026): "base" is the common layer every level sees (resellers, list prices,
// quotes, comparisons, merchant fit, flows, unified billing). Owner sees owner+team+base; team sees
// team+base; sales sees its instructions+base. The sales doc is never shown to owner or team.
const SEES={owner:new Set(["owner","team","base"]),team:new Set(["team","base"]),sales:new Set(["sales","base"])};
const KNOWN=new Set(["owner","team","sales","base"]);

export function visibleDocs(level,docs=BRAIN_DOCS){
 const sees=SEES[level];
 if(!sees)return [];
 // Fail closed: a doc with an unknown audience is treated as owner-only.
 return docs.filter(d=>sees.has(KNOWN.has(d.audience)?d.audience:"owner"));
}

export function buildSystem(level,docs=BRAIN_DOCS){
 const parts=visibleDocs(level,docs).map(d=>`<knowledge id="${d.id}">\n${d.body}\n</knowledge>`);
 let footer=`\n\nThe person asking is at level: ${level}. They are using Orbit.`;
 footer+="\nOrbit has no `escalate` tool: when part of a question is locked, say \"This part I can't answer here\" and name who to ask (confidential data, calculations and decisions: Kareem, or Hatem Ashour when Kareem is away; operational details: Althurayyaa Alsaad; deep cycle questions: Kareem or Hatem).";
 if(level!=="owner")footer+="\nThis person cannot see owner-only material (cost prices, markups, targets, strategy, negotiations). If asked for it, say it is restricted and to ask Kareem.";
 return parts.join("\n\n")+footer;
}

// Returns {question, history} or {error}.
export function validateAsk(body){
 if(!body||typeof body!=="object"||Array.isArray(body))return {error:"invalid_body"};
 const question=typeof body.question==="string"?body.question.trim():"";
 if(!question)return {error:"question_required"};
 if(question.length>MAX_QUESTION)return {error:"question_too_long"};
 const raw=Array.isArray(body.history)?body.history.slice(-MAX_HISTORY_TURNS*2):[];
 const history=[];
 for(const t of raw){
  if(!t||!["user","assistant"].includes(t.role)||typeof t.content!=="string")return {error:"invalid_history"};
  const content=t.content.slice(0,8000);
  if(history.length&&history[history.length-1].role===t.role)history[history.length-1].content+="\n"+content;
  else history.push({role:t.role,content});
 }
 while(history.length&&history[0].role!=="user")history.shift();
 while(history.length&&history[history.length-1].role!=="assistant")history.pop();
 return {question,history};
}

export function anthropicRequest(level,{question,history},model=BRAIN_MODEL_DEFAULT){
 return {
  model,
  max_tokens:1500,
  system:[{type:"text",text:buildSystem(level),cache_control:{type:"ephemeral"}}],
  messages:[...history,{role:"user",content:question}]
 };
}

export const MAX_TOOL_TURNS=5;
export const TOOL_GUIDE="\n\n## Orbit tools\nYou have read-only tools over Orbit's own data. Use them when the answer depends on current Orbit numbers (ARR, partners, tickets) instead of guessing, and say the figure came from Orbit. For any line item, list price, quote structure or partner comparison, call brain_catalog and quote exact Salesforce line-item names. If a tool fails or returns nothing, say so. Tools never change anything.";

// Runs the Claude tool loop. callClaude(body) must return the parsed Messages API response.
export async function askBrain({level,ask,toolNames,toolSchemas,runTool,callClaude,model=BRAIN_MODEL_DEFAULT}){
 const body=anthropicRequest(level,ask,model);
 if(toolNames.length){
  body.system[0].text+=TOOL_GUIDE;
  body.tools=toolNames.map(n=>toolSchemas[n]);
 }
 for(let turn=0;turn<=MAX_TOOL_TURNS;turn++){
  const data=await callClaude(body);
  const content=Array.isArray(data?.content)?data.content:[];
  const uses=content.filter(b=>b.type==="tool_use");
  if(!uses.length||data.stop_reason!=="tool_use")
   return content.filter(b=>b.type==="text").map(b=>b.text).join("").trim();
  body.messages.push({role:"assistant",content});
  const results=[];
  for(const u of uses){
   const r=toolNames.includes(u.name)?await runTool(u.name,u.input):{content:`Tool '${u.name}' is not available to you.`,is_error:true};
   results.push({type:"tool_result",tool_use_id:u.id,content:r.content,is_error:Boolean(r.is_error)});
  }
  body.messages.push({role:"user",content:results});
 }
 return "I needed too many lookups for this one. Please narrow the question.";
}
