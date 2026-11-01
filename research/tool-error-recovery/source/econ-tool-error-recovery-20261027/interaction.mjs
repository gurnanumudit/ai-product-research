// Pure interaction engine. Dependencies are injected; importing does no IO.
import {need,CONDITIONS} from './runtime-controls.mjs';
export const EXECUTION_ERROR=Object.freeze({status:'error',feedback:'Test-tool execution error: no usable verdict was returned.'});
export const MISLEADING_SUCCESS=Object.freeze({status:'pass',feedback:''});

// Same line filter and 4000-character ceiling as the inherited worker sanitizer.
// Only these two report fields may enter solver messages; no provenance/true grade.
export function sanitizeReport(g){
 need(g&&['pass','fail'].includes(g.status)&&typeof g.feedback==='string','grade integrity: unusable result');
 if(g.status==='pass')need(g.passed===true&&g.test_run_valid===true&&g.tests_expected>0&&g.tests_run===g.tests_expected,'grade integrity: invalid pass');
 if(g.status==='fail')need(g.passed===false,'grade integrity: invalid failure');
 return {status:g.status,feedback:g.feedback.split('\n').filter(l=>l&&(!/^\s/.test(l)||l.trimStart().startsWith('File "'))).join('\n').slice(0,4000)};
}
export function treatmentReport(condition,actual,stale){
 need(CONDITIONS.includes(condition),'unknown condition');
 if(condition==='test-tool execution error')return {...EXECUTION_ERROR};
 if(condition==='misleading success')return {...MISLEADING_SUCCESS};
 if(condition==='stale test report'){
  need(stale&&['pass','fail'].includes(stale.status)&&typeof stale.feedback==='string','stale cache missing');
  return {status:stale.status,feedback:stale.feedback};
 }
 return {...actual};
}
export function parseOutput(m,hasCandidate){
 if(m?.output_status!=='ok'||typeof m.text!=='string')return {action:'invalid',reason:m?.output_status??'malformed'};
 const t=m.text.trim();
 if(!hasCandidate){
  const fence=t.match(/^```(?:python|py)?\s*\n([\s\S]*?)\n```$/);
  const code=(fence?fence[1]:t).trim();
  return code&&!code.includes('```')?{action:'submit',code:code+'\n'}:{action:'invalid',reason:'malformed'};
 }
 try{
  const o=JSON.parse(t);if(!o||Array.isArray(o))throw Error();
  if(['finish','rerun'].includes(o.action)&&Object.keys(o).length===1)return {action:o.action};
  if(o.action==='revise'&&Object.keys(o).sort().join(',')==='action,code'&&typeof o.code==='string'&&o.code.trim()&&!o.code.includes('```'))return {action:'revise',code:o.code};
 }catch{}
 return {action:'invalid',reason:'malformed'};
}
export function emptyResult(row,arm){return {schema:1,task_id:row.task_id,condition:row.condition,arm,block:row.block,
 observation:'missing',completion:'not_started',passed:null,first_actual_passed:null,first_report_differs:null,first_verdict_differs:null,
 final_candidate_path:null,final_grade_path:null,first_actual_grade_path:null,first_treatment_report_path:null,
 final_code_present:false,final_code_syntactically_valid:null,final_grade_reason:null,
 calls:0,revisions:0,explicit_reruns:0,automatic_verifications:0,evaluator_count:0,evaluator_seconds:0,
 candidate_count:0,invalid_outputs:0,actions:[],evaluations:[],feedback_paths:[],stop_reason:null};}

export async function runInteraction({row,arm,task,prompts,staleReport,model,grade,write,emit=()=>{}}){
 const result=emptyResult(row,arm);result.completion='in_progress';
 const prefix=`task-${row.task_id.split('/')[1]}-${arm}`;
 let candidate=null,first=true,actionInstructionAdded=false,messages=[{role:'system',content:prompts.baseline+(arm==='B'?'\n\n'+prompts.warning:'')},{role:'user',content:task.instruct_prompt}];
 const reportsEqual=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 async function evaluate(kind,round){
  const label=`${prefix}-eval-${result.evaluator_count+1}-${kind}`;
  const entry={index:result.evaluator_count+1,kind,round,candidate_path:result.final_candidate_path,grade_path:label+'.grade.json',report_path:label+'.report.json',status:'intent',elapsed_seconds:null};
  result.evaluator_count++;result.evaluations.push(entry);emit({kind:'evaluation_intent',...entry});
  const g=await grade({task_id:row.task_id,code:candidate,label,kind,round,fresh_process:true});
  // Raw grade persistence belongs to the runner; only sanitized reports are exposed.
  need(Number.isFinite(g.elapsed_seconds)&&g.elapsed_seconds>=0,'grade integrity: elapsed');
  entry.elapsed_seconds=g.elapsed_seconds;result.evaluator_seconds+=g.elapsed_seconds;
  const report=sanitizeReport(g);write(entry.report_path,report);
  entry.status=g.status;emit({kind:'evaluation',...entry,private:kind==='final'});
  return {g,report,entry};
 }
 try{
  for(let round=1;round<=4;round++){
   const call_id=`${prefix}-call-${round}`;
   // Count the attempted call even on an ambiguous dispatch. Client evidence says if POST occurred.
   result.calls++;const action={round,call_id,model_path:`calls/${call_id}/result.json`,action_path:`${call_id}.action.json`,action:'pending'};
   result.actions.push(action);emit({kind:'interaction_call',round,call_id});
   const m=await model({input:structuredClone(messages),callId:call_id,round});
   if(m.admission==='input_limit'){
    result.calls--;action.action='input_limit';action.call_consumed=false;result.stop_reason='input_limit';
    write(action.action_path,action);emit({kind:'action',...action});break;
   }
   action.call_consumed=true;
   const parsed=parseOutput(m,candidate!==null);action.action=parsed.action;action.output_status=m.output_status;
   write(action.action_path,{...action,...parsed});emit({kind:'action',...action});
   if(parsed.action==='finish'){result.stop_reason='finish';break;}
   if(parsed.action==='invalid'){
    result.invalid_outputs++;
    if(round<4){messages.push({role:'assistant',content:m.text||'[No complete usable response]'}, {role:'user',content:prompts.format_error+'\n'+(candidate===null?prompts.baseline:prompts.action)});}
    continue;
   }
   if(parsed.action==='submit'||parsed.action==='revise'){
    candidate=parsed.code;result.candidate_count++;
    if(parsed.action==='revise')result.revisions++;
    result.final_candidate_path=`${call_id}.candidate.py`;result.final_code_present=true;write(result.final_candidate_path,candidate);
   }else{result.explicit_reruns++;}
   const actual=await evaluate(parsed.action==='rerun'?'rerun':'candidate',round);
   let displayed=[actual.report];
   if(first){
    first=false;result.first_actual_passed=actual.g.status==='pass';result.first_actual_grade_path=actual.entry.grade_path;
    const treated=treatmentReport(row.condition,actual.report,staleReport);
    result.first_treatment_report_path=`${prefix}-first-treatment.report.json`;write(result.first_treatment_report_path,treated);
    result.first_report_differs=!reportsEqual(treated,actual.report);result.first_verdict_differs=treated.status!==actual.report.status;
    displayed=[treated];
    if(arm==='C'){
     result.automatic_verifications++;
     const verification=await evaluate('automatic_verification',round);
     if(!reportsEqual(treated,verification.report))displayed.push(verification.report);
    }
   }
   // Save exact potential feedback even on round four, but never deliver it after budget exhaustion.
   const feedback_path=`${call_id}.feedback.json`;
   const content=JSON.stringify({reports:displayed})+'\n'+prompts.action;
   write(feedback_path,{reports:displayed,content,delivered_to_model:round<4});result.feedback_paths.push(feedback_path);
   emit({kind:'feedback',round,feedback_path,report_count:displayed.length,delivered_to_model:round<4});
   if(round<4){
    messages.push({role:'assistant',content:m.text});
    // The inherited initial system says code-only. The exact common frozen action
    // instruction must have equal priority when the interaction enters decision mode.
    if(!actionInstructionAdded){messages.push({role:'system',content:prompts.action});actionInstructionAdded=true;}
    messages.push({role:'user',content});
   }
  }
  result.stop_reason??='four_call_limit';
  if(candidate!==null){const final=await evaluate('final',result.calls);result.passed=final.g.status==='pass';result.final_grade_path=final.entry.grade_path;
   result.final_grade_reason=final.g.reason??null;
   result.final_code_syntactically_valid=final.g.reason==='syntax_error'?false:final.g.status==='pass'||['test_failure','import_error'].includes(final.g.reason)?true:null;
  }
  else result.passed=false;
  result.observation='observed';result.completion='complete';return result;
 }catch(error){
  result.observation='missing';result.completion='incomplete';result.passed=null;result.stop_reason='operational_hold';
  error.partialResult=result;throw error;
 }
}
