// Explicit entry point only. Never import or execute the sibling runner.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {BOUNDS,Accounting,need,admit,validateSelection,makeTransport,closureVerified} from './runtime-controls.mjs';
import {freshPreflight,checkPrices,validateProjection} from './preflight.mjs';
import {generate,requestBody} from './model-client.mjs';
import {runInteraction,emptyResult,sanitizeReport} from './interaction.mjs';
export const HOME=path.dirname(fileURLToPath(import.meta.url));
export const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const PILOT='../econ-tool-error-recovery-20261027/';
const SDK='../eval-budget-allocation-pilot-20261017/sandbox-client/';
export const REQUIRED_FILES=Object.freeze(['runner.mjs','model-client.mjs','billing-scoped.mjs','runtime-controls.mjs','preflight.mjs','interaction.mjs',
 'PROTOCOL.md','AUTHORIZATION.json',PILOT+'AMENDMENT-APPROVAL-v1.json',PILOT+'CONTINUE-APPROVAL-v1.json',PILOT+'MAIN-COST-PROJECTION-v1.json',PILOT+'MAIN-PRICE-CHECK-v1.json',
 'TASKS.json','SCHEDULE.json','PROMPTS.json','PLACEHOLDERS.json','DATA-PINS.json','bootstrap.sh','worker.py','test_worker.py','requirements.txt',
 SDK+'client.mjs',SDK+'node_modules/@vercel/sandbox/dist/index.js',SDK+'node_modules/@vercel/sandbox/dist/auth/file.js',SDK+'node_modules/@vercel/sandbox/dist/auth/oauth.js',SDK+'node_modules/@vercel/sandbox/package.json']);
function filesUnder(home,rel){return fs.readdirSync(path.join(home,rel),{withFileTypes:true}).flatMap(e=>{
 need(!e.isSymbolicLink(),'symlink in packaged tree');const p=path.posix.join(rel,e.name);
 return e.isDirectory()?(e.name==='__pycache__'?[]:filesUnder(home,p)):[p];});}
export function writeNew(home,name,value){
 const f=fs.openSync(path.join(home,name),'wx',0o600);
 try{fs.writeFileSync(f,typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');fs.fsyncSync(f);}finally{fs.closeSync(f);}
 const d=fs.openSync(home,'r');try{fs.fsyncSync(d);}finally{fs.closeSync(d);}
}
export function claim(home,releaseHash){writeNew(home,'CLAIM.json',{schema:1,pid:process.pid,at:new Date().toISOString(),release_sha256:releaseHash,phase:'main',cap_usd:50,pilot_carry_nano_usd:BOUNDS.pilotCarryNano,infrastructure_reserve_usd:24,max_hosts:12,max_model_calls:2880,no_restart:true});}
export function verifyRelease(home){
 const bytes=fs.readFileSync(path.join(home,'RELEASE.json')),release=JSON.parse(bytes);
 need(release.accepted===true&&release.phase==='main'&&release.independent_review_accepted===true,'independent main release required');
 need(release.files&&typeof release.files==='object','release pins missing');
 for(const f of [...REQUIRED_FILES,...filesUnder(home,'vendor')])need(typeof release.files[f]==='string','required release pin missing: '+f);
 for(const [f,pin] of Object.entries(release.files)){need(/^[a-f0-9]{64}$/.test(pin),'invalid pin');need(sha(fs.readFileSync(path.resolve(home,f)))===pin,'freeze mismatch: '+f);}
 return {release,hash:sha(bytes)};
}
export function validateInputs(home,release){
 const read=n=>JSON.parse(fs.readFileSync(path.join(home,n)));
 const tasks=read('TASKS.json').selected_rows,schedule=read('SCHEDULE.json'),prompts=read('PROMPTS.json'),placeholders=read('PLACEHOLDERS.json');
 validateSelection(tasks,schedule);validateProjection(read(PILOT+'MAIN-COST-PROJECTION-v1.json'));
 for(const k of ['baseline','warning','action','format_error'])need(typeof prompts[k]==='string'&&prompts[k].length>0,'missing frozen prompt '+k);
 need(tasks.every(t=>typeof t.instruct_prompt==='string'&&t.instruct_prompt.length>0),'public task shape');
 const stale=schedule.filter(r=>r.condition==='stale test report');
 need(Object.keys(placeholders).length===60&&stale.every(r=>typeof placeholders[r.task_id]==='string'&&/^def [A-Za-z_]\w*\(\*args, \*\*kwargs\):\s*raise NotImplementedError\(["']placeholder candidate["']\)\s*$/.test(placeholders[r.task_id])),'mechanical placeholder mapping');
 for(const row of schedule){const f='private/'+row.task_id.split('/')[1]+'.json';need(release.files[f]===sha(fs.readFileSync(path.join(home,f))),'private file not release pinned');}
 return {tasks,schedule,prompts,placeholders};
}

// Production adapter reuses the inherited sandbox/bootstrap/worker mechanics.
// Tests supply a wholly synthetic host; no SDK or credentials are loaded on import.
export async function createRemoteHost({home,number,credentials,write,emit,now=Date.now}){
 const {Sandbox}=await import(SDK+'node_modules/@vercel/sandbox/dist/index.js');
 const name=`econ-tool-recovery-main-v1-20261027-${number}`,prefix=`block-${number}`;
 const c={token:credentials.token,teamId:credentials.teamId,projectId:credentials.projectId};
 const transport=makeTransport(name,{record:v=>emit({kind:'transport_error',block:number,...v})});
 const options={...c,fetch:transport.fetch.bind(transport)};
 let box=null,started=null,networkSeq=0;
 const elapsed=()=>started===null?0:now()-started;
 async function readonlyList(){return Sandbox.list({...c,namePrefix:name,limit:50,sortBy:'name',fetch:async(u,o={})=>{
  need(['GET','HEAD'].includes((o.method??'GET').toUpperCase()),'readonly mutation');return fetch(u,{...o,redirect:'error'});
 },signal:AbortSignal.timeout(25000)});}
 async function command(cmd,args=[],timeout=120000){
  need(elapsed()<BOUNDS.admissionHostMs,'host time limit before command');
  const r=await box.runCommand({cmd,args,sudo:true,signal:AbortSignal.timeout(timeout)});
  return {exitCode:r.exitCode,stdout:await r.stdout({signal:AbortSignal.timeout(20000)}),stderr:await r.stderr({signal:AbortSignal.timeout(20000)})};
 }
 async function upload(files){await box.writeFiles(files,{signal:AbortSignal.timeout(90000)});}
 async function network(){
  const seq=++networkSeq;const r=await command('bash',['-c',`cat /proc/net/dev # egress-observation-${seq}`]);
  write(`${prefix}-NETWORK-${seq}.json`,r);need(r.exitCode===0,'network accounting failed');
  const egress=r.stdout.split('\n').filter(x=>x.includes(':')&&!x.trim().startsWith('lo:')).reduce((sum,l)=>{
   const a=l.split(':')[1].trim().split(/\s+/).map(Number);need(a.length>=16&&a.every(x=>Number.isFinite(x)&&x>=0),'network counter shape');return sum+a[8];
  },0);
  // Download ingress is free: do not add rx bytes. Reserve 1 MB for final control traffic.
  need(egress<=BOUNDS.transferBytesPerHost-1e6,'host egress allowance');return egress;
 }
 return {elapsed,
  async open(){
   const before=await readonlyList();write(prefix+'-PREHOST.json',{matching:before.sandboxes.map(x=>({name:x.name,status:x.status}))});need(before.sandboxes.length===0,'preexisting study resource');
   started=now();write(prefix+'-DISPATCH.json',{name,at:new Date().toISOString(),timeout_ms:BOUNDS.hostTimeoutMs,infrastructure_reserve_usd:2});
   box=await Sandbox.create({...options,name,image:'vercel/sandbox/python:3.14',region:'iad1',resources:{vcpus:2},timeout:BOUNDS.hostTimeoutMs,persistent:false,
    networkPolicy:{allow:['pypi.org','files.pythonhosted.org','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com','raw.githubusercontent.com','archive.ubuntu.com','security.ubuntu.com']},ports:[],mounts:{},env:{},signal:AbortSignal.timeout(60000)});
   write(prefix+'-HOST.json',{name,sandbox_id:box.sandboxId??null,vcpus:box.vcpus,memory:box.memory});
   need(box.vcpus===2&&box.memory===4096&&box.persistent===false,'host resources');
  },
  async prepare(rows){
   const names=['bootstrap.sh','requirements.txt','worker.py','test_worker.py',...filesUnder(home,'vendor'),...rows.map(r=>'private/'+r.task_id.split('/')[1]+'.json')];
   await upload(names.map(f=>({path:'/vercel/sandbox/idea19/'+f,content:fs.readFileSync(path.join(home,f))})));
   const boot=await command('bash',['/vercel/sandbox/idea19/bootstrap.sh'],900000);write(prefix+'-BOOTSTRAP.json',boot);need(boot.exitCode===0,'environment setup failed');
   await network();const policy=await box.updateNetworkPolicy('deny-all',{signal:AbortSignal.timeout(30000)});need(policy==='deny-all','network seal mismatch');
   const synthetic=await command('/opt/idea19/venv/bin/python',['/opt/idea19/test_worker.py','-q'],180000);write(prefix+'-SYNTHETIC.json',synthetic);
   need(synthetic.exitCode===0&&/Ran 14 tests\b/.test(synthetic.stderr+'\n'+synthetic.stdout),'fourteen synthetic grader checks required');
   emit({kind:'environment_ready',block:number,synthetic_checks:14,network:'deny-all'});
  },
  async beforeCall(){await network();},
  async grade({task_id,code,label,fresh_process}){
   need(fresh_process===true,'fresh worker required');
   const rp='/vercel/sandbox/idea19/'+label+'.request.json',op='/opt/idea19/'+label+'.result.json';
   await upload([{path:rp,content:Buffer.from(JSON.stringify({task_id,solution:code,is_reference:false}))}]);
   const r=await command('/opt/idea19/venv/bin/python',['/opt/idea19/worker.py','--request',rp,'--tasks-dir','/opt/idea19/private','--output',op],110000);
   write(label+'.command.json',r);need(r.exitCode===0,'grader process failure');const out=await command('cat',[op]);need(out.exitCode===0,'grader output unreadable');
   const g=JSON.parse(out.stdout);write(label+'.grade.json',g);
   need(g.task_id===task_id&&Number.isInteger(g.execution_uid)&&g.execution_uid!==0&&g.execution_uid_cleanup_verified===true&&!g.local_synthetic_only,'grade isolation integrity');
   sanitizeReport(g);return g;
  },
  async close(){
   let stopped=false,deleted=false,usage=null,verification=null;
   // An ambiguous creation is never replayed. Recover only for cleanup, with resume:false.
   if(!box&&transport.creates>0){try{box=await Sandbox.get({...options,name,resume:false,signal:AbortSignal.timeout(25000)});}catch{}}
   if(box){try{const s=await box.stop({signal:AbortSignal.timeout(30000)});stopped=s.status==='stopped'&&!s.snapshot;
     usage={active_cpu_ms:s.activeCpuUsageMs,network_transfer:s.networkTransfer,total_duration_ms:s.totalDurationMs,total_egress_bytes:s.totalEgressBytes,total_ingress_bytes:s.totalIngressBytes};}catch{}
    try{await box.delete({signal:AbortSignal.timeout(30000)});deleted=true;}catch{}}
   try{const r=await readonlyList();verification={empty:r.sandboxes.length===0,records:r.sandboxes.map(x=>({name:x.name,status:x.status}))};}catch{}
   const egress=usage?.total_egress_bytes??usage?.network_transfer?.egress;
   const seconds=elapsed()/1000;
   return {name,block:number,creation_dispatched:transport.creates>0,creation_confirmed:!!box,stopped,deleted,verification,elapsed_seconds:seconds,usage,
    billable_egress_bytes:Number.isFinite(egress)&&egress>=0?egress:null,actual_infrastructure_usd:null,infrastructure_reserve_usd:2,
    observed_resource_cost_upper_usd:Number.isFinite(egress)&&egress>=0?Math.ceil(seconds/60)/60*(2*.128+4*.0212)+.0000006+egress/1e9*.15:null};
  }
 };
}

export async function runMain({home=HOME,preflight=freshPreflight,priceCheck=checkPrices,client=generate,hostFactory=createRemoteHost}={}){
 need(!fs.existsSync(path.join(home,'CLAIM.json')),'run already claimed; no restart');
 const release=verifyRelease(home),inputs=validateInputs(home,release.release);
 // Read-only route + account must succeed freshly in THIS runner before exclusive CLAIM.
 const pre=await preflight({allowRefresh:true});need(pre.account?.status==='active'&&['pro','enterprise'].includes(pre.account.plan),'account preflight evidence');
 need(Date.now()-Date.parse(pre.prices?.at)>=0&&Date.now()-Date.parse(pre.prices.at)<60000,'fresh route preflight required');
 need(verifyRelease(home).hash===release.hash,'release changed during preflight');claim(home,release.hash);
 const write=(n,v)=>writeNew(home,n,v);let sequence=0;
 const emit=v=>{const event={schema:1,sequence:++sequence,at:new Date().toISOString(),...v};const fd=fs.openSync(path.join(home,'EVENTS.jsonl'),'a',0o600);try{fs.writeSync(fd,JSON.stringify(event)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}};
 const accounting=new Accounting(),closures=[],staleReports=new Map();
 const {tasks,schedule,prompts,placeholders}=inputs;
 const results=schedule.flatMap(r=>['A','B','C'].map(a=>emptyResult(r,a)));
 const index=(id,arm)=>results.findIndex(r=>r.task_id===id&&r.arm===arm);
 let held=null,createdHosts=0;
 try{
  write('LAUNCH-PREFLIGHT.json',{account:pre.account,prices:pre.prices});emit({kind:'claim',assigned_arms:720,...accounting.snapshot()});
  for(let number=1;number<=12;number++){
   need(verifyRelease(home).hash===release.hash,'release changed after claim');const fresh=number===1?pre:await preflight({allowRefresh:true});write(`block-${number}-PREFLIGHT.json`,{account:fresh.account,prices:fresh.prices});
   const host=await hostFactory({home,number,credentials:fresh.credentials,write,emit});let blockError=null;
   try{
    need(++createdHosts<=12,'host count');admit(accounting);await host.open();
    // First host receives all selected files so all sixty stale reports precede every POST.
    await host.prepare(number===1?schedule:schedule.filter(r=>r.block===number));
    if(number===1){
     for(const row of schedule.filter(r=>r.condition==='stale test report')){
      const label='stale-'+row.task_id.split('/')[1];emit({kind:'stale_cache_intent',task_id:row.task_id,block:1,grade_path:label+'.grade.json'});
      const g=await host.grade({task_id:row.task_id,code:placeholders[row.task_id],label,kind:'stale_placeholder',fresh_process:true});
      need(Number.isFinite(g.elapsed_seconds)&&g.elapsed_seconds>=0,'stale grade elapsed missing');
      const report=sanitizeReport(g);write(label+'.report.json',report);staleReports.set(row.task_id,report);
      emit({kind:'stale_cache',task_id:row.task_id,block:1,grade_path:label+'.grade.json',report_path:label+'.report.json',elapsed_seconds:g.elapsed_seconds});
     }
     need(staleReports.size===60&&accounting.calls===0,'all stale caches must precede experimental calls');
     write('STALE-CACHE-COMPLETE.json',{count:60,host:1,experimental_calls:0,reports:Object.fromEntries(staleReports)});
    }
    for(const row of schedule.filter(r=>r.block===number))for(const arm of row.arms){
     const event=v=>emit({block:number,task_id:row.task_id,condition:row.condition,arm,...v});
     const model=async({input,callId})=>{
      try{requestBody(input);}catch(error){if(error.message==='serialized_input_limit'){event({kind:'input_limit',call_id:callId,call_consumed:false});return {admission:'input_limit'};}throw error;}
      need(staleReports.size===60,'stale cache incomplete');await host.beforeCall();admit(accounting,host.elapsed());
      write(callId+'.price.json',await priceCheck());admit(accounting,host.elapsed());accounting.reserve(callId,host.elapsed());
      event({kind:'model_intent',call_id:callId,request_path:`calls/${callId}/request.json`,...accounting.snapshot()});
      try{const m=await client({input,outputDir:path.join(home,'calls'),callId});accounting.settle(callId,m.cost_nano_usd);
       event({kind:'model_settled',call_id:callId,output_status:m.output_status,usage:m.usage??null,...accounting.snapshot()});return m;
      }catch(error){accounting.hold(callId,error);event({kind:'model_hold',call_id:callId,...accounting.snapshot()});throw error;}
     };
     try{
      const r=await runInteraction({row,arm,task:tasks.find(t=>t.task_id===row.task_id),prompts,staleReport:staleReports.get(row.task_id),model,grade:a=>host.grade(a),write,emit:event});
      results[index(row.task_id,arm)]=r;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,r);event({kind:'arm_complete',passed:r.passed,result_path:`result-${row.task_id.split('/')[1]}-${arm}.json`});
     }catch(error){if(error.partialResult){results[index(row.task_id,arm)]=error.partialResult;write(`result-${row.task_id.split('/')[1]}-${arm}.json`,error.partialResult);}throw error;}
    }
    write(`block-${number}-COMPLETE.json`,{task_arms:60,...accounting.snapshot()});
   }catch(error){blockError=error;throw error;}
   finally{
    let closure;try{closure=await host.close();}catch{closure={block:number,closure_unknown:true,infrastructure_reserve_usd:2};}
    closures.push(closure);write(`block-${number}-RESOURCE-CLOSURE.json`,closure);emit({kind:'resource_closure',block:number,closure_path:`block-${number}-RESOURCE-CLOSURE.json`});
    const ok=closureVerified(closure);
    if(!ok&&!blockError)throw Error('resource closure or infrastructure allowance unresolved');
   }
  }
  need(results.length===720&&results.every(r=>r.observation==='observed')&&accounting.pendingNano===0&&closures.length===12,'completion invariant');
 }catch(error){held={reason_code:error.name==='ClientHold'?error.message:'operational_hold',error_name:error.name,no_restart:true,...accounting.snapshot()};
  // Detailed raw provider errors can contain secrets; artifacts preserve the exact stage instead.
  held.local_reason=error.name==='ClientHold'?error.stage:null;write('HOLD.json',held);emit({kind:'hold',...held});
 }
 const summary={schema:1,phase:'main',assigned_tasks:240,assigned_arms:720,planned_per_arm:240,planned_per_condition_arm:60,
  collection_status:held?'held':'complete',results,...accounting.snapshot(),resource_closures:closures,
  actual_infrastructure_usd:null,infrastructure_status:'reserved_pending_invoice',human_codex_costs:'unmeasured'};
 write('RESULTS.json',summary);
 if(!held){write('COLLECTION-COMPLETE.json',{assigned_arms:720,observed_arms:720,...accounting.snapshot(),resources_verified_closed:true});emit({kind:'collection_complete',...accounting.snapshot()});}
 return summary;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 runMain().then(r=>{console.log(JSON.stringify({collection_status:r.collection_status,assigned_arms:r.assigned_arms,calls:r.calls}));if(r.collection_status!=='complete')process.exitCode=1;}).catch(e=>{console.error(JSON.stringify({error_name:e.name,reason:'preclaim_or_persistence_hold',no_restart:true}));process.exitCode=1;});
}
