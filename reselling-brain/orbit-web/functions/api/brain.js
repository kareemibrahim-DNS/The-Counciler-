import {getContext,json,mutationGuard} from "../_lib/access.js";
import {brainLevel,validateAsk,askBrain,BRAIN_MODEL_DEFAULT,BRAIN_DAILY_LIMIT_DEFAULT} from "../_lib/reselling-brain.js";
import {BRAIN_TOOLS,toolsFor,runTool} from "../_lib/reselling-brain-tools.js";

// POST /api/brain {question, history?} → {answer, level}
// GET  /api/brain → {level, configured}
// Questions and answers are not stored. Only a count per person per day is audited.
export async function onRequest({request,env}){
 const ctx=await getContext(request,env);
 if(!ctx.ok)return json({error:ctx.error},ctx.status);
 const level=brainLevel(ctx);
 if(!level)return json({error:"forbidden"},403);
 const configured=Boolean(env.ANTHROPIC_API_KEY);
 if(request.method==="GET")return json({level,configured});
 if(request.method!=="POST")return json({error:"method_not_allowed"},405);
 const guard=mutationGuard(request);if(guard)return guard;
 if(!configured)return json({error:"brain_not_configured"},503);
 let body;try{body=await request.json();}catch{return json({error:"invalid_json"},400);}
 const ask=validateAsk(body);
 if(ask.error)return json({error:ask.error},400);

 const limit=Number(env.BRAIN_DAILY_LIMIT)||BRAIN_DAILY_LIMIT_DEFAULT;
 try{
  const used=await ctx.db.prepare(
   "SELECT COUNT(*) AS n FROM audit_events WHERE actor_id=? AND action='brain_ask' AND created_at>=date('now')"
  ).bind(ctx.principal.id).first();
  if(!ctx.owner&&Number(used?.n||0)>=limit)return json({error:"daily_limit_reached"},429);
  await ctx.db.prepare("INSERT INTO audit_events(id,actor_id,action,subject_type,subject_id) VALUES(?,?,?,?,?)")
   .bind(crypto.randomUUID(),ctx.principal.id,"brain_ask","brain",level).run();
 }catch{return json({error:"database_unavailable"},503);}

 const toolSchemas=Object.fromEntries(Object.entries(BRAIN_TOOLS).map(([n,t])=>[n,t.schema]));
 const callClaude=async body=>{
  const r=await fetch("https://api.anthropic.com/v1/messages",{
   method:"POST",
   headers:{"content-type":"application/json","x-api-key":env.ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
   body:JSON.stringify(body)
  });
  if(!r.ok)throw new Error("upstream");
  return r.json();
 };
 let answer;
 try{
  answer=await askBrain({level,ask,toolNames:toolsFor(ctx),toolSchemas,runTool:(n,i)=>runTool(ctx,n,i),callClaude,model:env.BRAIN_MODEL||BRAIN_MODEL_DEFAULT});
 }catch{return json({error:"brain_unavailable"},502);}
 return json({answer:answer||"Not in the Reselling Brain yet — ask Kareem.",level});
}
