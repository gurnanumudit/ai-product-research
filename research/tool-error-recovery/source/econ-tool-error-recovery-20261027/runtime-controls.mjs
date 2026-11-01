import crypto from 'node:crypto';
export const BOUNDS=Object.freeze({capNano:30e9,infraNano:4e9,maxCalls:480,callReserveNano:50e6,maxHosts:2,hostTimeoutMs:14400000,admissionHostMs:13680000,transferBytesPerHost:2e9,maxCallsPerArm:4,assignedArms:120});
export const need=(b,m)=>{if(!b)throw Error(m)};
export function projection({calls,settledNano,pendingNano}){
 need(Number.isSafeInteger(calls)&&calls>=0&&calls<=BOUNDS.maxCalls,'invalid call count');
 need([settledNano,pendingNano].every(x=>Number.isSafeInteger(x)&&x>=0),'invalid cost');
 return BOUNDS.infraNano+settledNano+pendingNano+(BOUNDS.maxCalls-calls)*BOUNDS.callReserveNano;
}
export function admit(s,elapsed=0){need(s.calls<BOUNDS.maxCalls,'call limit');need(Number.isFinite(elapsed)&&elapsed>=0&&elapsed<BOUNDS.admissionHostMs,'host time limit');need(projection(s)<=BOUNDS.capNano,'whole completion projection exceeds30USD');}
export const CONDITIONS=Object.freeze(['clean','test-tool execution error','misleading success','stale test report']);
export function validateSelection(tasks,schedule){
 need(tasks.length===40&&new Set(tasks.map(x=>x.task_id)).size===40,'task count');
 need(schedule.length===40&&new Set(schedule.map(x=>x.task_id)).size===40,'schedule count');
 const counts=new Map(),conditions=new Map();
 for(let i=0;i<40;i++){const b=schedule[i];need(/^BigCodeBench\/\d+$/.test(b.task_id)&&b.task_id===tasks[i].task_id&&b.block===Math.floor(i/20)+1,'block schedule');need(Array.isArray(b.arms)&&[...b.arms].sort().join('')==='ABC'&&b.arms.length===3,'arm schedule');need(CONDITIONS.includes(b.condition),'condition');let k=b.arms.join('');counts.set(k,(counts.get(k)||0)+1);conditions.set(b.condition,(conditions.get(b.condition)||0)+1);}
 need(counts.size===6&&[...counts.values()].sort().join(',')==='6,6,7,7,7,7','unbalanced orders');
 need(CONDITIONS.every(c=>conditions.get(c)===10),'condition balance');
}
export class Accounting {
 constructor(){this.calls=0;this.settledNano=0;this.pendingNano=0;this.entries=new Map();this.stopped=false;}
 reserve(id,elapsed=0){need(!this.stopped,'accounting stopped');need(!this.entries.has(id),'duplicate call');admit(this,elapsed);this.entries.set(id,{status:'pending'});this.calls++;this.pendingNano+=BOUNDS.callReserveNano;}
 settle(id,nano){const e=this.entries.get(id);need(e?.status==='pending','duplicate or absent settlement');need(Number.isSafeInteger(nano)&&nano>=0,'unknown charge');e.status='settled';e.cost_nano_usd=nano;this.pendingNano-=BOUNDS.callReserveNano;this.settledNano+=nano;if(nano>BOUNDS.callReserveNano){this.stopped=true;throw Error('call cost exceeds reserve');}need(projection(this)<=BOUNDS.capNano,'cap exceeded');}
 hold(id,error){this.stopped=true;const e=this.entries.get(id);if(e?.status!=='pending')return;
  if(Number.isSafeInteger(error.settled_nano_usd)&&error.settled_nano_usd>=0){this.settle(id,error.settled_nano_usd);}
  else if(error.request_dispatched===false){e.status='undispatched';this.pendingNano-=BOUNDS.callReserveNano;}
  // Uncertain transport/receipt retains the ENTIRE reserve. Never replay.
 }
 snapshot(){return {calls:this.calls,settled_nano_usd:this.settledNano,pending_nano_usd:this.pendingNano,infrastructure_reserve_nano_usd:BOUNDS.infraNano,whole_completion_projection_nano_usd:projection(this)};}
}
export function closureVerified(c){return !!(c.stopped&&c.deleted&&c.verification?.empty&&
 Number.isFinite(c.billable_egress_bytes)&&c.billable_egress_bytes>=0&&c.billable_egress_bytes<=BOUNDS.transferBytesPerHost&&
 Number.isFinite(c.observed_resource_cost_upper_usd)&&c.observed_resource_cost_upper_usd>=0&&c.observed_resource_cost_upper_usd<=2);}
export function makeTransport(expectedName,{fetcher=fetch,record=()=>{}}={}){
 const seen=new Set();let creates=0;
 return {get creates(){return creates},async fetch(url,opt={}){
  const u=new URL(url),method=(opt.method??'GET').toUpperCase();need(u.origin==='https://vercel.com'&&u.pathname.startsWith('/api/'),'SDK origin');need(u.searchParams.get('resume')!=='true','resume forbidden');
  const mutation=!['GET','HEAD'].includes(method);
  if(mutation){
   const raw=typeof opt.body==='string'?opt.body:opt.body==null?'':Buffer.isBuffer(opt.body)||opt.body instanceof Uint8Array?Buffer.from(opt.body):null;
   need(raw!==null,'unfingerprintable SDK body');
   const fp=crypto.createHash('sha256').update(method+u.href).update(raw).digest('hex');need(!seen.has(fp),'mutation replay blocked');seen.add(fp);
   if(method==='POST'&&/\/v[23]\/sandboxes$/.test(u.pathname)){
    need(++creates===1,'second host creation');let b=JSON.parse(opt.body);
    need(b.name===expectedName&&b.timeout===BOUNDS.hostTimeoutMs&&b.persistent===false&&b.resources?.vcpus===2&&b.region==='iad1'&&b.image==='vercel/sandbox/python:3.14','create bounds');
    need(!b.source&&!b.networkId&&!b.failoverRegions?.length&&!b.ports?.length&&!Object.keys(b.mounts??{}).length&&!Object.keys(b.env??{}).length,'host extra resources');
   }
  }
  // Only bounded error metadata; no headers, bodies, query strings, or credentials.
  try{const r=await fetcher(url,{...opt,redirect:'error'});if(mutation&&(r.status===429||r.status>=500)){record({method,path:u.pathname,status:r.status,error:'ambiguous_mutation_response'});await r.body?.cancel();throw new DOMException('Ambiguous mutation response; no replay','AbortError');}return r;}
  catch(e){try{record({method,path:u.pathname,error_name:e.name,cause_code:e.cause?.code??null,signal_aborted:!!opt.signal?.aborted});}catch{}if(mutation)throw new DOMException('Mutation failed; no replay','AbortError');throw e;}
 }};
}
