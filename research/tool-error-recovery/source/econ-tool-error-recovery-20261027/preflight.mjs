// No import-time IO. Routine existing-credential renewal is permitted before CLAIM.
import fs from 'node:fs';
import {parseEnv} from 'node:util';
import {need,BOUNDS} from './runtime-controls.mjs';
const H=new URL('.',import.meta.url);
const SDK='../eval-budget-allocation-pilot-20261017/sandbox-client/';
export async function freshCredentials({allowRefresh=true,auth=null,now=Date.now}={}){
 // Injection is for pure synthetic tests; defaults reuse the approved SDK path.
 const helpers=auth??{...await import(SDK+'node_modules/@vercel/sandbox/dist/auth/file.js'),
  ...await import(SDK+'node_modules/@vercel/sandbox/dist/auth/oauth.js'),...await import(SDK+'client.mjs')};
 let a=helpers.getAuth(),refreshed=false;
 if(!a?.token||!a.expiresAt||a.expiresAt.getTime()<now()+(allowRefresh?5:4.1)*3600000){
  need(allowRefresh,'credential lifetime insufficient after claim; collector stopped');
  need(a?.refreshToken,'cached credential has no renewal token');
  try{
   const oauth=await helpers.OAuth(),n=await oauth.refreshToken(a.refreshToken);
   need(typeof n.access_token==='string'&&n.access_token.length>0&&Number.isFinite(n.expires_in)&&n.expires_in>0,'renewal response shape');
   helpers.updateAuthConfig({token:n.access_token,refreshToken:n.refresh_token??a.refreshToken,expiresAt:new Date(now()+n.expires_in*1000)});refreshed=true;
  }catch{throw Error('existing_credential_renewal_failed');}
 }
 const fresh=helpers.getAuth();need(fresh?.token&&fresh.expiresAt?.getTime()>now()+4.1*3600000,'credential lifetime too short for full host');
 return {...helpers.credentials(),refreshed};
}
function key(){return parseEnv(fs.readFileSync('/Users/muditgurnani/Documents/AI Projects/frontier-model-value-observatory/.env','utf8')).AI_GATEWAY_API_KEY;}
async function get(url,token,fetcher){need(token,'missing configured credential');const r=await fetcher(url,{method:'GET',headers:{Authorization:`Bearer ${token}`},redirect:'error',signal:AbortSignal.timeout(25000)});need(r.ok,`readonly_preflight_http_${r.status}`);return r.json();}
export function priceFields(data){
 const d=data?.data;need(d?.id==='openai/gpt-6-luna'&&Array.isArray(d.endpoints),'model catalog shape');
 const es=d.endpoints.filter(x=>x.provider_name==='openai');need(es.length===1,'OpenAI endpoint count');const e=es[0];
 need(e.status===0&&e.context_length>=124096+8192&&e.max_completion_tokens>=8192,'OpenAI endpoint unavailable');
 return {provider:e.provider_name,model:d.id,pricing:e.pricing};
}
export function validateProjection(p){
 need(p.model==='openai/gpt-6-luna'&&p.provider==='openai'&&p.reasoning==='medium'&&p.service_tier==='standard/default','projection route');
 const a=p.pilot,i=a?.infrastructure;
 need(a?.tasks===40&&a.arms===3&&a.max_model_calls_per_task_arm===4&&a.max_model_calls===480&&Number(a.call_reservation_usd)===.05&&Number(a.cap_usd)===30&&Number(a.planning_total_usd)===28&&Number(a.api_reservation_usd)===24,'projection API limits');
 need(a.input_reservation_tokens_per_call===124096&&a.inclusive_output_ceiling_per_call===8192,'projection token limits');
 need(i?.region==='iad1'&&i.planned_sandboxes_up_to===2&&i.vcpus_per_sandbox===2&&i.gb_per_sandbox===4&&i.aggregate_host_hours_allowance===8&&i.hours_per_sandbox_allowance===4&&i.billable_transfer_allowance_gb===4&&Number(i.reserve_usd)===4&&!i.persistent_drives_snapshots,'projection infrastructure limits');
 const expected={prompt:1e-7,completion:5e-7,input_cache_read:1e-8,input_cache_write:1.25e-7,request:0};
 for(const [k,v] of Object.entries(expected))need(Number(p.pricing_per_token?.[k])===v,'projection price '+k);
 need(Number(i.cpu_usd_vcpu_hour)===.128&&Number(i.memory_usd_gb_hour)===.0212&&Number(i.creation_usd_each)===.0000006&&Number(i.transfer_usd_gb)===.15,'projection infrastructure price');
 return p;
}
export async function checkPrices({fetcher=(...a)=>fetch(...a),keyLoader=key,projection=null}={}){
 const p=validateProjection(projection??JSON.parse(fs.readFileSync(new URL('PILOT-COST-PROJECTION-v1.json',H))));
 const raw=await get('https://ai-gateway.vercel.sh/v1/models/openai/gpt-6-luna/endpoints',keyLoader(),fetcher);
 const selected=priceFields(raw);
 for(const [k,v] of Object.entries(p.pricing_per_token))need(selected.pricing?.[k]!=null&&Number(selected.pricing[k])===Number(v),'route or pricing changed: '+k);
 return {at:new Date().toISOString(),selected,raw,projection_cap_nano_usd:BOUNDS.capNano};
}
export async function accountPreflight(c,{fetcher=(...a)=>fetch(...a)}={}){
 const b=await get(`https://api.vercel.com/v2/teams/${encodeURIComponent(c.teamId)}`,c.token,fetcher);
 need(['pro','enterprise'].includes(b.billing?.plan)&&b.billing?.status==='active','Sandbox account not active paid plan');
 return {at:new Date().toISOString(),credential_source:c.credential_source,refreshed:c.refreshed===true,plan:b.billing.plan,status:b.billing.status};
}
export async function freshPreflight({allowRefresh=true}={}){const credentials=await freshCredentials({allowRefresh});return {credentials,account:await accountPreflight(credentials),prices:await checkPrices()};}
