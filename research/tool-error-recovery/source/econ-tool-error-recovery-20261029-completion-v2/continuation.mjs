import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {Accounting,need} from './accounting.mjs';
import {createRemoteHost} from './host.mjs';
import {freshPreflight,checkPrices} from '../econ-tool-error-recovery-20261027-main-v1/preflight.mjs';
import {generate,requestBody,extract} from './model-client.mjs';
import {reconcile,generationId} from '../econ-tool-error-recovery-20261027-main-v1/billing-scoped.mjs';
import {runInteraction} from '../econ-tool-error-recovery-20261027-main-v1/interaction.mjs';
import {closureVerified} from '../econ-tool-error-recovery-20261027-main-v1/runtime-controls.mjs';
export const HOME=path.dirname(fileURLToPath(import.meta.url));
export const SOURCE=path.resolve(HOME,'../econ-tool-error-recovery-20261027-main-v1');
export const PREVIOUS=path.resolve(HOME,'../econ-tool-error-recovery-20261029-continuation-v1');
export const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=(dir,n)=>JSON.parse(fs.readFileSync(path.join(dir,n)));
export function writeNew(dir,n,v){const f=fs.openSync(path.join(dir,n),'wx',0o600);try{fs.writeFileSync(f,typeof v==='string'?v:JSON.stringify(v,null,2)+'\n');fs.fsyncSync(f);}finally{fs.closeSync(f);}const d=fs.openSync(dir,'r');try{fs.fsyncSync(d);}finally{fs.closeSync(d);}}
export function verifyRelease(home=HOME){const r=read(home,'RELEASE.json');need(r.accepted===true&&r.phase==='completion-v2'&&r.independent_review_accepted===true,'continuation release absent');for(const [p,h]of Object.entries(r.files))need(sha(fs.readFileSync(p))===h,'release pin changed: '+p);return sha(fs.readFileSync(path.join(home,'RELEASE.json')));}
export function buildPlan(original,schedule){
 need(original.results.length===720&&schedule.length===240,'assignment shape');
 const by=new Map(original.results.map(r=>[r.task_id+'|'+r.arm,r]));need(by.size===720,'duplicate arm');
 const ordered=schedule.flatMap(row=>row.arms.map(arm=>({row,arm,old:by.get(row.task_id+'|'+arm)})));
 need(ordered.every(x=>x.old&&x.old.condition===x.row.condition&&x.old.block===x.row.block),'assignment binding');
 need(ordered.slice(0,628).every(x=>x.old.observation==='observed'&&x.old.completion==='complete'),'preserved628 prefix');
 const todo=ordered.slice(628);need(todo.length===92&&todo.every(x=>x.old.observation==='missing'),'missing92 suffix');
 const partial=todo.filter(x=>x.old.completion==='incomplete');need(partial.length===1&&partial[0]===todo[0]&&partial[0].old.task_id==='BigCodeBench/533'&&partial[0].arm==='C','savedresponse identity');
 const r=partial[0].old;
 need(r.calls===1&&r.actions.length===1&&r.actions[0].call_id==='task-533-C-call-1'&&r.actions[0].action==='pending'&&r.evaluations.length===0&&r.candidate_count===0&&r.final_candidate_path===null,'savedresponse unconsumed');
 need(todo.slice(1).every(x=>x.old.completion==='not_started'&&x.old.calls===0),'untouched remainder');
 need([11,12].map(n=>todo.filter(x=>x.row.block===n).length).join(',')==='32,60','block workload');
 return todo;
}
export function recoverSavedResponse({input,previous=PREVIOUS,write,emit,expected}){
 const callId='task-533-C-call-1',dir=path.join(previous,'calls',callId);
 const responseBytes=fs.readFileSync(path.join(dir,'response.json'));
 need(sha(responseBytes)===expected.source_response_sha256,'savedresponse hash');
 const req=read(dir,'request.json');need(JSON.stringify(req.body)===JSON.stringify(requestBody(input)),'savedrequest exact reconstruction');
 need(!fs.existsSync(path.join(previous,callId+'.action.json')),'savedresponse already consumed');
 const response=JSON.parse(responseBytes),late=read(previous,'POSTHOLD-RECEIPT-CHECK-v1.json');need(late.status===200,'late receipt status');
 const id=generationId(response);need(id===expected.saved_response_generation_id&&id===late.generation_id,'late receipt identity');
 const charge=reconcile(response,JSON.parse(late.body),id);need(charge.cost_nano_usd===expected.late_charge_nano_usd,'late charge');
 const output=extract(response),m={...output,cost:charge.cost_nano_usd/1e9,costUSD:charge.cost_nano_usd/1e9,cost_nano_usd:charge.cost_nano_usd,responseid:response.id??id,response_id:response.id??id,generation_id:id,call_id:callId,call_consumed:true,model_request_attempts:1,pending_nano_usd:0,usage:charge.usage};
 const pins=Object.fromEntries(['request.json','response.json','DISPATCH.json','HOLD.json'].map(n=>[path.join(dir,n),sha(fs.readFileSync(path.join(dir,n)))]));
 for(const n of ['POSTHOLD-RECEIPT-CHECK-v1.json','POSTHOLD-CHARGE-ADDENDUM-v1.json'])pins[path.join(previous,n)]=sha(fs.readFileSync(path.join(previous,n)));
 write('SAVED-RESPONSE-RECOVERY.json',{call_id:callId,generation_id:id,source_response_sha256:sha(responseBytes),charge,files:pins,no_new_post:true,prior_request_counts_toward_four:true,result_path:'recovered-task-533-C-call-1.result.json'});
 write('recovered-task-533-C-call-1.result.json',m);emit({kind:'saved_response_consumed',call_id:callId,new_model_posts:0,provenance_path:'SAVED-RESPONSE-RECOVERY.json'});return m;
}
export async function runContinuation({home=HOME,source=SOURCE,previous=PREVIOUS,preflight=freshPreflight,prices=checkPrices,client=generate,hostFactory=createRemoteHost}={}){
 need(!fs.existsSync(path.join(home,'CLAIM.json')),'continuation already claimed; do not restart');
 const release=verifyRelease(home),original=read(previous,'RESULTS.json'),schedule=read(source,'SCHEDULE.json'),tasks=read(source,'TASKS.json').selected_rows,prompts=read(source,'PROMPTS.json'),stale=read(source,'STALE-CACHE-COMPLETE.json').reports;
 const todo=buildPlan(original,schedule);need(Object.keys(stale).length===60,'original stale cache');
 need(read(source,'ROOT-RESOURCE-CLOSURE-ADDENDUM-v1.json').all_launched_hosts_verified_closed===10,'original resource closure');
 need(original.calls===137&&original.settled_nano_usd===36419125&&original.pending_nano_usd===50000000,'previous finances');
 const amendment=read(home,'AMENDMENT.json');need(sha(fs.readFileSync(path.join(previous,'RESULTS.json')))===amendment.source_results_sha256,'previous results pin');
 need(original.resource_closures.length===2&&original.resource_closures.every(closureVerified),'previous closure');
 const pre=await preflight({allowRefresh:true});need(pre.account.status==='active'&&['pro','enterprise'].includes(pre.account.plan),'paid account');need(Date.now()-Date.parse(pre.prices.at)<60000,'fresh prices');need(verifyRelease(home)===release,'release changed');
 writeNew(home,'CLAIM.json',{at:new Date().toISOString(),pid:process.pid,phase:'completion-v2',release_sha256:release,previous_results_sha256:sha(fs.readFileSync(path.join(previous,'RESULTS.json'))),assigned_arms:720,retained_observed:628,missing_to_complete:92,no_restart:true});
 const write=(n,v)=>{if(n==='task-533-C-call-1.action.json'&&v.model_path)v={...v,model_path:'recovered-task-533-C-call-1.result.json'};writeNew(home,n,v);};let sequence=0;const emit=v=>{const e={sequence:++sequence,at:new Date().toISOString(),...v};const f=fs.openSync(path.join(home,'EVENTS.jsonl'),'a',0o600);try{fs.writeSync(f,JSON.stringify(e)+'\n');fs.fsyncSync(f);}finally{fs.closeSync(f);}};
 const accounting=new Accounting(),results=structuredClone(original.results),closures=[];let held=null,created=0,activeOperation="launch",activeTask=null;
 write('LAUNCH-PREFLIGHT.json',{account:pre.account,prices:pre.prices});emit({kind:'claim',...accounting.snapshot()});
 try{
 for(const number of [11,12]){
  activeOperation="host_preflight";
  need(verifyRelease(home)===release,'release changed');accounting.admit();
  const fresh=number===11?pre:await preflight({allowRefresh:true});write(`block-${number}-PREFLIGHT.json`,{account:fresh.account,prices:fresh.prices});
  const host=await hostFactory({home:source,number,credentials:fresh.credentials,write,emit});let blockError=null;
  try{
   need(++created<=2,'continuation host limit');accounting.admit();activeOperation='host_create';await host.open();activeOperation='host_setup';await host.prepare(schedule.filter(r=>r.block===number));
   for(const {row,arm,old}of todo.filter(x=>x.row.block===number)){
    activeTask={task_id:row.task_id,arm,block:number};activeOperation='interaction';
    const event=v=>emit({block:number,task_id:row.task_id,condition:row.condition,arm,...v});let r;
    const model=async({input,callId,round})=>{
     if(old.completion==='incomplete'&&round===1)return recoverSavedResponse({input,previous,write,emit:event,expected:amendment});
     need(!fs.existsSync(path.join(source,'calls',callId))&&!fs.existsSync(path.join(previous,'calls',callId)),'old modelcall collision');
     try{
      try{requestBody(input);}catch(e){if(e.message==='serialized_input_limit'){event({kind:'input_limit',call_id:callId,call_consumed:false});return {admission:'input_limit'};}throw e;}
      await host.beforeCall();accounting.admit(host.elapsed());write(callId+'.price.json',await prices());accounting.admit(host.elapsed());accounting.reserve(callId,host.elapsed());
     }catch(e){
      if(!accounting.entries.has(callId)){
       const artifact=callId+'.predispatch.json';
       write(artifact,{call_id:callId,request_dispatched:false,financial_reserved:false,stage:'pre_reserve',error_name:e.name});
       event({kind:'model_pre_dispatch_hold',call_id:callId,artifact_path:artifact,...accounting.snapshot()});
      }
      throw e;
     }
     event({kind:'model_intent',call_id:callId,request_path:`calls/${callId}/request.json`,...accounting.snapshot()});
     try{const m=await client({input,outputDir:path.join(home,'calls'),callId});accounting.settle(callId,m.cost_nano_usd);event({kind:'model_settled',call_id:callId,output_status:m.output_status,usage:m.usage??null,...accounting.snapshot()});return m;}catch(e){accounting.hold(callId,e);event({kind:'model_hold',call_id:callId,...accounting.snapshot()});throw e;}
    };
    try{r=await runInteraction({row,arm,task:tasks.find(t=>t.task_id===row.task_id),prompts,staleReport:stale[row.task_id],model,grade:a=>host.grade(a),write,emit:event});}
    catch(e){if(e.partialResult){if(old.completion==='incomplete')e.partialResult.actions[0].model_path='recovered-task-533-C-call-1.result.json';results[results.findIndex(x=>x.task_id===row.task_id&&x.arm===arm)]=e.partialResult;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,e.partialResult);}throw e;}
    if(old.completion==='incomplete')r.actions[0].model_path='recovered-task-533-C-call-1.result.json';
    results[results.findIndex(x=>x.task_id===row.task_id&&x.arm===arm)]=r;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,r);event({kind:'arm_complete',result_path:`result-${row.task_id.split('/')[1]}-${arm}.json`,passed:r.passed});
   }
   write(`block-${number}-COMPLETE.json`,{task_arms:todo.filter(x=>x.row.block===number).length,...accounting.snapshot()});
  }catch(e){blockError=e;throw e;}finally{let c;try{c=await host.close();}catch{c={block:number,closure_unknown:true,infrastructure_reserve_usd:2};}closures.push(c);write(`block-${number}-RESOURCE-CLOSURE.json`,c);emit({kind:'resource_closure',block:number,closure_path:`block-${number}-RESOURCE-CLOSURE.json`});if(!closureVerified(c)&&!blockError)throw Error('continuation resource closure unresolved');}
 }
 need(results.every(r=>r.observation==='observed')&&closures.length===2&&accounting.pendingNano===0,'completion invariant');
 }catch(e){held={at:new Date().toISOString(),reason_code:'continuation_hold',error_name:e.name,stage:e.stage??activeOperation,call_id:e.call_id??null,active_task:activeTask,client_code:e.name==='ClientHold'?e.message:null,no_restart:true,...accounting.snapshot()};write('HOLD.json',held);emit({kind:'hold',...held});}
 const summary={schema:1,phase:'completion-v2',source_main:source,source_previous:previous,assigned_tasks:240,assigned_arms:720,planned_per_arm:240,planned_per_condition_arm:60,collection_status:held?'held':'complete',original_calls:1647,previous_calls:137,prior_known_api_including_pilot_nano_usd:598602940,original_settled_nano_usd:469631345,results,...accounting.snapshot(),resource_closures:closures,actual_infrastructure_usd:null,human_codex_costs:'unmeasured'};write('RESULTS.json',summary);
 if(!held){write('COLLECTION-COMPLETE.json',{assigned_arms:720,observed_arms:720,retained_original_observed:628,continued:91,recovered_saved_response:1,...accounting.snapshot(),resources_verified_closed:true});emit({kind:'collection_complete',...accounting.snapshot()});}return summary;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){need(process.argv.includes('--actual'),'explicit --actual required');runContinuation().then(r=>{console.log(JSON.stringify({status:r.collection_status,observed:r.results.filter(x=>x.observation==='observed').length,new_calls:r.calls}));if(r.collection_status!=='complete')process.exitCode=1;}).catch(e=>{console.error(JSON.stringify({error_name:e.name,stage:'preclaim_or_persistence',no_restart:true}));process.exitCode=1;});}
