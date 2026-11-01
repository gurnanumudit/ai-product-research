// No import-time IO. Routine existing-credential renewal is permitted only before each new host (including pre-CLAIM).
import fs from 'node:fs';
import {parseEnv} from 'node:util';
import {need,BOUNDS} from './runtime-controls.mjs';
import {money} from './billing-scoped.mjs';
const H=new URL('.',import.meta.url);
const SDK='../eval-budget-allocation-pilot-20261017/sandbox-client/';
export async function freshCredentials({allowRefresh=true,auth=null,now=Date.now}={}){
 // Injection is for pure synthetic tests; defaults reuse the approved SDK path.
 const helpers=auth??{...await import(SDK+'node_modules/@vercel/sandbox/dist/auth/file.js'),
  ...await import(SDK+'node_modules/@vercel/sandbox/dist/auth/oauth.js'),...await import(SDK+'client.mjs')};
 let a=helpers.getAuth(),refreshed=false;
 if(!a?.token||!a.expiresAt||a.expiresAt.getTime()<now()+(allowRefresh?5:4.1)*3600000){
  need(allowRefresh,'credential lifetime insufficient outside host-boundary renewal; collector stopped');
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
 need(p.model==='openai/gpt-6-luna'&&p.provider==='openai'&&p.reasoning==='medium','projection route');
 need(p.main_tasks===240&&p.main_arms===720&&p.max_new_calls===2880&&p.output_tokens===8192&&p.model_timeout_seconds===180&&p.input_bounds_unchanged===true,'projection API limits');
 need(money(p.combined_cap_usd)===BOUNDS.capNano&&money(p.main_per_dispatch_unknown_charge_reserve_usd)===BOUNDS.callReserveNano&&money(p.forecast_per_call_usd)===BOUNDS.initialForecastNano,'projection accounting limits');
 need(money(p.pilot_settled_api_usd)+money(p.pilot_pending_api_usd)+money(p.pilot_infrastructure_reserve_usd)===BOUNDS.pilotCarryNano,'pilot carry mismatch');
 const i=p.infrastructure;
 need(i?.hosts===12&&i.tasks_per_host===20&&i.vcpus===2&&i.memory_gb===4&&i.hours_per_host===4&&i.aggregate_host_hours===48&&i.region==='iad1'&&i.egress_gb_per_host===2&&money(i.reserve_usd)===BOUNDS.infraNano&&i.persistent_drives_snapshots===false,'projection infrastructure limits');
 need(Number(i.cpu_usd_vcpu_hour)===.128&&Number(i.memory_usd_gb_hour)===.0212&&Number(i.creation_usd_each)===.0000006&&Number(i.egress_usd_gb)===.15,'projection infrastructure prices');
 need(money(p.combined_projection_usd)===BOUNDS.pilotCarryNano+BOUNDS.infraNano+BOUNDS.maxCalls*BOUNDS.initialForecastNano,'initial projection mismatch');
 return p;
}
export async function checkPrices({fetcher=(...a)=>fetch(...a),keyLoader=key,projection=null,priceRecord=null}={}){
 validateProjection(projection??JSON.parse(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/MAIN-COST-PROJECTION-v1.json',H))));
 const saved=priceRecord??JSON.parse(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/MAIN-PRICE-CHECK-v1.json',H)));
 need(saved.selected?.model==='openai/gpt-6-luna'&&saved.selected?.provider==='openai','saved main price route');
 const raw=await get('https://ai-gateway.vercel.sh/v1/models/openai/gpt-6-luna/endpoints',keyLoader(),fetcher);
 const selected=priceFields(raw);
 for(const [k,v] of Object.entries({prompt:1e-7,completion:5e-7,input_cache_read:1e-8,input_cache_write:1.25e-7,request:0})){
  need(saved.selected.pricing?.[k]!=null&&Number(saved.selected.pricing[k])===v,'saved main price '+k);
  need(selected.pricing?.[k]!=null&&Number(selected.pricing[k])===v,'route or pricing changed: '+k);
 }
 return {at:new Date().toISOString(),selected,raw,projection_cap_nano_usd:BOUNDS.capNano};
}
export async function accountPreflight(c,{fetcher=(...a)=>fetch(...a)}={}){
 const b=await get(`https://api.vercel.com/v2/teams/${encodeURIComponent(c.teamId)}`,c.token,fetcher);
 need(['pro','enterprise'].includes(b.billing?.plan)&&b.billing?.status==='active','Sandbox account not active paid plan');
 return {at:new Date().toISOString(),credential_source:c.credential_source,refreshed:c.refreshed===true,plan:b.billing.plan,status:b.billing.status};
}
export async function freshPreflight({allowRefresh=true}={}){const credentials=await freshCredentials({allowRefresh});return {credentials,account:await accountPreflight(credentials),prices:await checkPrices()};}
