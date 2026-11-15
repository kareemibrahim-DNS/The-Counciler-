(()=>{
'use strict';
const $=id=>document.getElementById(id);
const errors={forbidden:'The Reselling Brain is available to approved Orbit employees only.',brain_not_configured:'The Reselling Brain is not switched on yet. Ask the Owner.',daily_limit_reached:'You reached today\'s question limit. Try again tomorrow.',question_too_long:'Please shorten your question (2,000 characters max).',brain_unavailable:'The Brain could not answer right now. Try again in a minute.'};
let history=[];
async function api(body){
 const r=await fetch('/api/brain',{credentials:'same-origin',cache:'no-store',...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
 let data;try{data=await r.json();}catch{throw Error('Please sign in again or contact the Owner.');}
 if(!r.ok)throw Error(errors[data.error]||'Unable to complete this request. Please refresh and try again.');
 return data;
}
function add(role,text){
 const div=document.createElement('div');
 div.className='brain-msg '+(role==='user'?'brain-user':'brain-answer');
 div.dir='auto';
 div.textContent=text; // plain text only: answers are never parsed as HTML
 $('log').appendChild(div);div.scrollIntoView({block:'end'});
}
async function init(){
 try{
  const s=await api();
  $('message').textContent=s.configured?'':errors.brain_not_configured;
  $('chatPanel').hidden=!s.configured;
  $('levelNote').textContent=s.level==='owner'?'Owner view: full detail, including pricing and targets.':'Team view: policy, rules, SLAs and processes. Pricing and targets are restricted.';
 }catch(e){$('message').textContent=e.message;}
}
$('askForm').addEventListener('submit',async ev=>{
 ev.preventDefault();
 const q=$('question').value.trim();if(!q)return;
 add('user',q);$('question').value='';$('send').disabled=true;$('message').textContent='Thinking…';
 try{
  const {answer}=await api({question:q,history});
  add('assistant',answer);
  history.push({role:'user',content:q},{role:'assistant',content:answer});
  history=history.slice(-20);
  $('message').textContent='';
 }catch(e){$('message').textContent=e.message;}
 finally{$('send').disabled=false;$('question').focus();}
});
$('clear').addEventListener('click',()=>{history=[];$('log').textContent='';$('question').focus();});
init();
})();
