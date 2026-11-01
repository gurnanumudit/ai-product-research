// Adapted from confirmation harness: one POST per exclusive call directory.
// Pilot runner owns global 480-call/$30 admission. No generation retry/replay.
import fs from 'node:fs';
import path from 'node:path';
import {parseEnv} from 'node:util';
import {createHash} from 'node:crypto';
import {CONFIG, reconcile, generationId} from './billing-scoped.mjs';

export const LIMITS = Object.freeze({inputBytes:60000, outputTokens:8192,
  reserveNanoUSD:50000000, requestMarginNanoUSD:10000000,
  inputTokensReserved:124096, modelTimeoutMs:180000, receiptWindowMs:90000});
export const ENDPOINT = 'https://ai-gateway.vercel.sh/v1/responses';
const KEY_FILE = '/Users/muditgurnani/Documents/AI Projects/frontier-model-value-observatory/.env';
const hash = b => createHash('sha256').update(b).digest('hex');
export class ClientHold extends Error {
  constructor(code, details={}) { super(code); this.name='ClientHold'; Object.assign(this,details); }
}
const need = (ok, code) => { if(!ok) throw new ClientHold(code); };
function loadKey() {
  const key=parseEnv(fs.readFileSync(KEY_FILE,'utf8')).AI_GATEWAY_API_KEY;
  need(typeof key==='string'&&key.length>0,'missing_gateway_key'); return key;
}

export function requestBody(input) {
  need(typeof input==='string'||(Array.isArray(input)&&input.length>0&&input.every(x=>
    x&&['system','developer','user','assistant'].includes(x.role)&&typeof x.content==='string'
    &&Object.keys(x).every(k=>['role','content'].includes(k)))),'invalid_input');
  const body={model:CONFIG.model,input,reasoning:{effort:'medium'},service_tier:'default',
    max_output_tokens:LIMITS.outputTokens,store:false,stream:false,truncation:'disabled',
    tools:[],providerOptions:{gateway:{only:['openai']}}};
  need(Buffer.byteLength(JSON.stringify(body))<=LIMITS.inputBytes,'serialized_input_limit');
  return body;
}

export function extract(response) {
  if(response.status==='incomplete')return {code:'',text:'',output_status:'incomplete'};
  if(response.status!=='completed'||!Array.isArray(response.output))
    return {code:'',text:'',output_status:'malformed'};
  const messages=response.output.filter(x=>x?.type==='message');
  if(messages.length!==1||response.output.some(x=>!['message','reasoning'].includes(x?.type)))
    return {code:'',text:'',output_status:'malformed'};
  const m=messages[0];
  if(m.role!=='assistant'||m.status!=='completed'||!Array.isArray(m.content)||!m.content.length
    ||m.content.some(x=>x?.type!=='output_text'||typeof x.text!=='string'))
    return {code:'',text:'',output_status:'malformed'};
  const text=m.content.map(x=>x.text).join(''),trimmed=text.trim();
  const fenced=trimmed.match(/^```(?:python|py)?\s*\n([\s\S]*?)\n```$/);
  const code=(fenced?fenced[1]:trimmed).trim();
  if(!code||code.includes('```'))return {code:'',text,output_status:'malformed'};
  // No Python import/execution/syntax inference here. The grader handles invalid Python.
  return {code:code+'\n',text,output_status:'ok'};
}

// Injection exists solely for offline tests; default generate uses raw native fetch.
export function createClient({fetcher=(...a)=>globalThis.fetch(...a),keyLoader=loadKey,
  now=()=>performance.now(),delay=ms=>new Promise(r=>setTimeout(r,ms))}={}) {
  return async function generate({input,outputDir,callId}) {
    need(typeof callId==='string'&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$/.test(callId),'invalid_call_id');
    need(typeof outputDir==='string'&&outputDir.length>0,'invalid_output_dir');
    const body=requestBody(input),bodyText=JSON.stringify(body);
    fs.mkdirSync(outputDir,{recursive:true,mode:0o700});
    const directory=path.resolve(outputDir,callId);
    // EEXIST is a consumed call; never overwrite or reuse it, even after an unknown charge.
    try{fs.mkdirSync(directory,{mode:0o700});}catch{throw new ClientHold('call_directory_unavailable');}
    let key='',dispatched=false,settled=null,stage='key';
    const clean=x=>key?x.split(key).join('[REDACTED]'):x;
    const write=(name,bytes)=>{
      const fd=fs.openSync(path.join(directory,name),'wx',0o600);
      try{fs.writeFileSync(fd,clean(bytes));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
      const dir=fs.openSync(directory,'r');try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}
    };
    const save=(name,value)=>write(name,JSON.stringify(value,null,2)+'\n');
    try {
      key=keyLoader();need(typeof key==='string'&&key.length>0,'missing_gateway_key');
      const pricedBound=LIMITS.inputTokensReserved*(100+125)+LIMITS.outputTokens*500+LIMITS.requestMarginNanoUSD;
      need(pricedBound<=LIMITS.reserveNanoUSD,'reserve_insufficient');
      save('request.json',{call_id:callId,endpoint:ENDPOINT,body,request_sha256:hash(bodyText),
        reserve_nano_usd:LIMITS.reserveNanoUSD,priced_bound_nano_usd:pricedBound,
        serialized_bytes:Buffer.byteLength(bodyText),input_tokens_reserved:LIMITS.inputTokensReserved});
      const headers={'Content-Type':'application/json',Authorization:`Bearer ${key}`};
      stage='model_transport';
      save('DISPATCH.json',{call_id:callId,at_utc:new Date().toISOString(),model_request_attempts:1,
        reserve_nano_usd:LIMITS.reserveNanoUSD,no_model_retry:true});
      dispatched=true;
      const http=await fetcher(ENDPOINT,{method:'POST',headers,body:bodyText,redirect:'error',
        signal:AbortSignal.timeout(LIMITS.modelTimeoutMs)});
      const raw=await http.text();
      save('response.http.json',{status:http.status,body:raw});
      need(http.status>=200&&http.status<300,'model_http_hold');
      need(Buffer.byteLength(raw)<=8*1024*1024,'response_size_hold');
      stage='response_parse';const response=JSON.parse(raw);
      need(response&&typeof response==='object'&&!Array.isArray(response),'response_shape_hold');
      save('response.json',response);
      stage='generation_identity';const id=generationId(response);
      stage='receipt_lookup';const deadline=now()+LIMITS.receiptWindowMs;
      let receipt=null;
      for(let attempt=0;now()<deadline&&attempt<31;attempt++) {
        const remaining=Math.floor(deadline-now());if(remaining<=0)break;
        const res=await fetcher(`https://ai-gateway.vercel.sh/v1/generation?id=${encodeURIComponent(id)}`,
          {method:'GET',headers,redirect:'error',signal:AbortSignal.timeout(Math.max(1,Math.min(30000,remaining)))});
        const text=await res.text();
        save(`receipt-${attempt}.http.json`,{status:res.status,body:text});
        need(now()<=deadline,'receipt_deadline_hold');
        if(res.status===200){receipt=JSON.parse(text);break;}
        need(res.status===404,'receipt_http_hold');
        const wait=Math.min(3000,Math.max(0,deadline-now()));if(wait)await delay(wait);
      }
      need(receipt!==null,'receipt_deadline_hold');save('receipt.json',receipt);
      stage='reconcile';const charge=reconcile(response,receipt,id);
      save('charge.json',charge);settled=charge.cost_nano_usd;
      need(settled<=LIMITS.reserveNanoUSD,'call_cost_exceeds_reserve');
      const output=extract(response);
      write('output.txt',output.text);
      const result={...output,cost:settled/1e9,costUSD:settled/1e9,cost_nano_usd:settled,
        responseid:response.id??id,response_id:response.id??id,generation_id:id,call_id:callId,
        call_consumed:true,model_request_attempts:1,pending_nano_usd:0,usage:charge.usage};
      save('result.json',result);return result;
    } catch(error) {
      const code=error instanceof ClientHold?error.message:`${stage}_hold`;
      const details={call_id:callId,stage,request_dispatched:dispatched,
        model_request_attempts:dispatched?1:0,settled_nano_usd:settled,
        pending_nano_usd:dispatched&&settled===null?LIMITS.reserveNanoUSD:0,no_retry:true};
      try{save('HOLD.json',{code,...details});}catch{/* Preserve directory and propagate hold even if disk is unavailable. */}
      throw new ClientHold(code,details);
    }
  };
}
export const generate=createClient();
