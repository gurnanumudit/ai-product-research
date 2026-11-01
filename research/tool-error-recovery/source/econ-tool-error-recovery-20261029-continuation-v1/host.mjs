import fs from 'node:fs';
import path from 'node:path';
import {BOUNDS,need,makeTransport} from '../econ-tool-error-recovery-20261027-main-v1/runtime-controls.mjs';
import {sanitizeReport} from '../econ-tool-error-recovery-20261027-main-v1/interaction.mjs';
const SDK='../eval-budget-allocation-pilot-20261017/sandbox-client/';
function filesUnder(home,rel){return fs.readdirSync(path.join(home,rel),{withFileTypes:true}).flatMap(e=>{need(!e.isSymbolicLink(),'symlink');const p=path.posix.join(rel,e.name);return e.isDirectory()?(e.name==='__pycache__'?[]:filesUnder(home,p)):[p];});}
export async function createRemoteHost({home,number,credentials,write,emit,now=Date.now,sdk=null}){
 const {Sandbox}=sdk??await import(SDK+'node_modules/@vercel/sandbox/dist/index.js');
 const name=`econ-tool-recovery-completion-v1-20261029-${number}`,prefix=`block-${number}`;
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
   write(label+'.command.json',r);need(r.exitCode===0,'grader process failure');
   // Retrieve the completed output directly; do not launch another shell command.
   const out=await box.readFileToBuffer({path:op},{signal:AbortSignal.timeout(25000)});
   need(Buffer.isBuffer(out)&&out.length>0,'grader output unreadable');
   write(label+'.retrieval.json',{method:'SDK readFileToBuffer',path:op,bytes:out.length,no_grader_reexecution:true});
   const g=JSON.parse(out.toString('utf8'));write(label+'.grade.json',g);
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
