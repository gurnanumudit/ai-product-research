import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {Accounting,need} from './accounting.mjs';
import {createRemoteHost} from './host.mjs';
import {freshPreflight,checkPrices} from '../econ-tool-error-recovery-20261027-main-v1/preflight.mjs';
import {generate,requestBody} from '../econ-tool-error-recovery-20261027-main-v1/model-client.mjs';
import {runInteraction,sanitizeReport} from '../econ-tool-error-recovery-20261027-main-v1/interaction.mjs';
import {closureVerified} from '../econ-tool-error-recovery-20261027-main-v1/runtime-controls.mjs';
export const HOME=path.dirname(fileURLToPath(import.meta.url));
export const SOURCE=path.resolve(HOME,'../econ-tool-error-recovery-20261027-main-v1');
export const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=(dir,n)=>JSON.parse(fs.readFileSync(path.join(dir,n)));
export function writeNew(dir,n,v){const f=fs.openSync(path.join(dir,n),'wx',0o600);try{fs.writeFileSync(f,typeof v==='string'?v:JSON.stringify(v,null,2)+'\n');fs.fsyncSync(f);}finally{fs.closeSync(f);}const d=fs.openSync(dir,'r');try{fs.fsyncSync(d);}finally{fs.closeSync(d);}}
export function verifyRelease(home=HOME){const r=read(home,'RELEASE.json');need(r.accepted===true&&r.phase==='continuation'&&r.independent_review_accepted===true,'continuation release absent');for(const [p,h]of Object.entries(r.files))need(sha(fs.readFileSync(p))===h,'release pin changed: '+p);return sha(fs.readFileSync(path.join(home,'RELEASE.json')));}
export function buildPlan(original,schedule){
 need(original.results.length===720&&schedule.length===240,'assignment shape');
 const by=new Map(original.results.map(r=>[r.task_id+'|'+r.arm,r]));need(by.size===720,'duplicate arm');
 const ordered=schedule.flatMap(row=>row.arms.map(arm=>({row,arm,old:by.get(row.task_id+'|'+arm)})));
 need(ordered.every(x=>x.old&&x.old.condition===x.row.condition&&x.old.block===x.row.block),'assignment binding');
 need(ordered.slice(0,576).every(x=>x.old.observation==='observed'&&x.old.completion==='complete'),'original completed prefix');
 const todo=ordered.slice(576);need(todo.length===144&&todo.every(x=>x.old.observation==='missing'),'missing suffix');
 const partial=todo.filter(x=>x.old.completion==='incomplete');need(partial.length===1&&partial[0]===todo[0]&&partial[0].old.task_id==='BigCodeBench/131'&&partial[0].arm==='B','partial identity');
 need(partial[0].old.calls===2&&partial[0].old.actions.at(-1).action==='finish'&&partial[0].old.final_candidate_path==='task-131-B-call-1.candidate.py','partial finish binding');
 need(todo.slice(1).every(x=>x.old.completion==='not_started'&&x.old.calls===0),'untouched remainder');
 need([10,11,12].map(n=>todo.filter(x=>x.row.block===n&&x.old.completion==='not_started').length).join(',')==='23,60,60','block workload');
 return todo;
}
export async function recoverFinal({old,source=SOURCE,grade,write,emit}){
 const candidate=fs.readFileSync(path.join(source,old.final_candidate_path));
 need(sha(candidate)==='e455718d03f9fa9fe897af7efa27d702c5499d9e6ac892dcafbda5a14742a816','saved candidate mismatch');
 need(read(source,'task-131-B-call-2.action.json').action==='finish','finish action required');
 const r=structuredClone(old),label='recovery-task-131-B-final',entry={index:3,kind:'final_recovery',round:2,candidate_path:old.final_candidate_path,grade_path:label+'.grade.json',report_path:label+'.report.json',status:'intent',elapsed_seconds:null};
 r.evaluator_count++;r.evaluations.push(entry);r.recovery_original_stop_reason=old.stop_reason;r.recovery_policy='Single fresh final grade determines amended outcome regardless of prior command summary; no new model call';
 write('RECOVERY-PROVENANCE.json',{source_task:old.task_id,arm:old.arm,candidate_path:old.final_candidate_path,candidate_sha256:sha(candidate),original_final_command_sha256:sha(fs.readFileSync(path.join(source,'task-131-B-eval-2-final.command.json'))),finish_action_sha256:sha(fs.readFileSync(path.join(source,'task-131-B-call-2.action.json'))),old_ambiguous_grade_intent_retained:true,policy:r.recovery_policy});
 emit({kind:'evaluation_intent',...entry,private:true,recovery:true});
 try{const g=await grade({task_id:old.task_id,code:candidate.toString(),label,kind:'final_recovery',round:2,fresh_process:true});need(Number.isFinite(g.elapsed_seconds)&&g.elapsed_seconds>=0,'recovery elapsed');write(entry.report_path,sanitizeReport(g));entry.status=g.status;entry.elapsed_seconds=g.elapsed_seconds;r.evaluator_seconds+=g.elapsed_seconds;r.final_grade_path=entry.grade_path;r.final_grade_reason=g.reason??null;r.passed=g.status==='pass';r.final_code_syntactically_valid=g.reason==='syntax_error'?false:g.status==='pass'||['test_failure','import_error'].includes(g.reason)?true:null;r.observation='observed';r.completion='complete';r.stop_reason='finish';r.recovery_prior_command_status=JSON.parse(read(source,'task-131-B-eval-2-final.command.json').stdout).status;r.recovery_disagrees_with_command=r.recovery_prior_command_status!==g.status;emit({kind:'evaluation',...entry,private:true,recovery:true});return r;}catch(e){e.partialResult=r;throw e;}
}
export async function runContinuation({home=HOME,source=SOURCE,preflight=freshPreflight,prices=checkPrices,client=generate,hostFactory=createRemoteHost}={}){
 need(!fs.existsSync(path.join(home,'CLAIM.json')),'continuation already claimed; do not restart');
 const release=verifyRelease(home),original=read(source,'RESULTS.json'),schedule=read(source,'SCHEDULE.json'),tasks=read(source,'TASKS.json').selected_rows,prompts=read(source,'PROMPTS.json'),stale=read(source,'STALE-CACHE-COMPLETE.json').reports;
 const todo=buildPlan(original,schedule);need(Object.keys(stale).length===60,'original stale cache');
 need(read(source,'ROOT-RESOURCE-CLOSURE-ADDENDUM-v1.json').all_launched_hosts_verified_closed===10,'original resource closure');
 need(original.calls===1647&&original.settled_nano_usd===469631345&&original.pending_nano_usd===0,'original finances');
 const pre=await preflight({allowRefresh:true});need(pre.account.status==='active'&&['pro','enterprise'].includes(pre.account.plan),'paid account');need(Date.now()-Date.parse(pre.prices.at)<60000,'fresh prices');need(verifyRelease(home)===release,'release changed');
 writeNew(home,'CLAIM.json',{at:new Date().toISOString(),pid:process.pid,phase:'continuation',release_sha256:release,original_results_sha256:sha(fs.readFileSync(path.join(source,'RESULTS.json'))),assigned_arms:720,retained_observed:576,missing_to_complete:144,no_restart:true});
 const write=(n,v)=>writeNew(home,n,v);let sequence=0;const emit=v=>{const e={sequence:++sequence,at:new Date().toISOString(),...v};const f=fs.openSync(path.join(home,'EVENTS.jsonl'),'a',0o600);try{fs.writeSync(f,JSON.stringify(e)+'\n');fs.fsyncSync(f);}finally{fs.closeSync(f);}};
 const accounting=new Accounting(),results=structuredClone(original.results),closures=[];let held=null,created=0;
 write('LAUNCH-PREFLIGHT.json',{account:pre.account,prices:pre.prices});emit({kind:'claim',...accounting.snapshot()});
 try{
 for(const number of [10,11,12]){
  need(verifyRelease(home)===release,'release changed');accounting.admit();
  const fresh=number===10?pre:await preflight({allowRefresh:true});write(`block-${number}-PREFLIGHT.json`,{account:fresh.account,prices:fresh.prices});
  const host=await hostFactory({home:source,number,credentials:fresh.credentials,write,emit});let blockError=null;
  try{
   need(++created<=3,'continuation host limit');accounting.admit();await host.open();await host.prepare(schedule.filter(r=>r.block===number));
   for(const {row,arm,old}of todo.filter(x=>x.row.block===number)){
    const event=v=>emit({block:number,task_id:row.task_id,condition:row.condition,arm,...v});let r;
    const model=async({input,callId})=>{
     need(old.completion==='not_started','model calls forbidden for partial');need(!fs.existsSync(path.join(source,'calls',callId)),'old modelcall collision');
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
    try{r=old.completion==='incomplete'?await recoverFinal({old,source,grade:a=>host.grade(a),write,emit:event}):await runInteraction({row,arm,task:tasks.find(t=>t.task_id===row.task_id),prompts,staleReport:stale[row.task_id],model,grade:a=>host.grade(a),write,emit:event});}
    catch(e){if(e.partialResult){results[results.findIndex(x=>x.task_id===row.task_id&&x.arm===arm)]=e.partialResult;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,e.partialResult);}throw e;}
    results[results.findIndex(x=>x.task_id===row.task_id&&x.arm===arm)]=r;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,r);event({kind:'arm_complete',result_path:`result-${row.task_id.split('/')[1]}-${arm}.json`,passed:r.passed});
   }
   write(`block-${number}-COMPLETE.json`,{task_arms:todo.filter(x=>x.row.block===number).length,...accounting.snapshot()});
  }catch(e){blockError=e;throw e;}finally{let c;try{c=await host.close();}catch{c={block:number,closure_unknown:true,infrastructure_reserve_usd:2};}closures.push(c);write(`block-${number}-RESOURCE-CLOSURE.json`,c);emit({kind:'resource_closure',block:number,closure_path:`block-${number}-RESOURCE-CLOSURE.json`});if(!closureVerified(c)&&!blockError)throw Error('continuation resource closure unresolved');}
 }
 need(results.every(r=>r.observation==='observed')&&closures.length===3&&accounting.pendingNano===0,'completion invariant');
 }catch(e){held={at:new Date().toISOString(),reason_code:'continuation_hold',error_name:e.name,no_restart:true,...accounting.snapshot()};write('HOLD.json',held);emit({kind:'hold',...held});}
 const summary={schema:1,phase:'continuation',source_main:source,assigned_tasks:240,assigned_arms:720,planned_per_arm:240,planned_per_condition_arm:60,collection_status:held?'held':'complete',original_calls:1647,original_settled_nano_usd:469631345,results,...accounting.snapshot(),resource_closures:closures,actual_infrastructure_usd:null,human_codex_costs:'unmeasured'};write('RESULTS.json',summary);
 if(!held){write('COLLECTION-COMPLETE.json',{assigned_arms:720,observed_arms:720,retained_original_observed:576,continued:143,recovered_final_only:1,...accounting.snapshot(),resources_verified_closed:true});emit({kind:'collection_complete',...accounting.snapshot()});}return summary;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){need(process.argv.includes('--actual'),'explicit --actual required');runContinuation().then(r=>{console.log(JSON.stringify({status:r.collection_status,observed:r.results.filter(x=>x.observation==='observed').length,new_calls:r.calls}));if(r.collection_status!=='complete')process.exitCode=1;}).catch(e=>{console.error(JSON.stringify({error_name:e.name,stage:'preclaim_or_persistence',no_restart:true}));process.exitCode=1;});}
