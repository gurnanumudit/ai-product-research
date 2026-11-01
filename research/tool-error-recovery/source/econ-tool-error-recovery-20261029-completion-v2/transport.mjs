import {makeTransport as originalTransport,need} from '../econ-tool-error-recovery-20261027-main-v1/runtime-controls.mjs';
// The SDK implements file reads using POST. Authorize only exact completed-grade
// file paths, with a physical transmission ceiling shared across SDK/host retries.
export function makeTransport(name,{fetcher=(...a)=>fetch(...a),record=()=>{}}={}){
 const original=originalTransport(name,{fetcher,record}),reads=new Map();
 return {get creates(){return original.creates;},allowCompletedRead(file){
  need(/^\/opt\/idea19\/task-\d+-[ABC]-eval-\d+-(candidate|rerun|automatic_verification|final)\.result\.json$/.test(file),'completed-grade read path');
  need(!reads.has(file),'read authorization repeated');reads.set(file,{attempts:0,url:null});
 },async fetch(url,opt={}){
  const u=new URL(url),method=(opt.method??'GET').toUpperCase();
  if(u.origin==='https://vercel.com'&&/^\/api\/v2\/sandboxes\/sessions\/[^/]+\/fs\/read$/.test(u.pathname)&&method==='POST'){
   need(u.searchParams.get('resume')!=='true','resume forbidden');
   need(typeof opt.body==='string','read request body');const b=JSON.parse(opt.body);
   need(b&&Object.keys(b).length===1&&typeof b.path==='string','read exact path body');
   const r=reads.get(b.path);need(r,'file not authorized as completed grade');
   need(r.url===null||r.url===u.href,'completed-file session changed');r.url=u.href;
   need(r.attempts<3,'completed-file physical read ceiling');r.attempts++;
   record({kind:'completed_file_read_attempt',method,path:u.pathname,attempt:r.attempts});
   // Read semantics only. Original transport guards every execution mutation.
   return fetcher(url,{...opt,redirect:'error'});
  }
  return original.fetch(url,opt);
 }};
}
