const data=JSON.parse(document.querySelector('#chart-data').textContent);
const labels={overall:'Overall',clean:'Clean','test-tool execution error':'Testing-tool error','misleading success':'Misleading success','stale test report':'Stale report'};
const names={A:'Baseline',B:'Warning',C:'Verification'}, colors={A:'#737c6b',B:'#bf6347',C:'#287565'};
const comparisons={'C-A':'Verification − baseline','C-B':'Verification − warning','B-A':'Warning − baseline'};
const state={condition:'misleading success',contrast:'C-A',resource:'api_settled_usd',step:0,flowCondition:'misleading success',flowArm:'C'};
const fmt=(x,d=2)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const signed=(x)=>`${x>=0?'+':'−'}${fmt(Math.abs(x))}`;
const table=(caption,head,rows)=>`<table><caption>${caption}</caption><thead><tr>${head.map(s=>`<th scope="col">${s}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map((s,i)=>i===0?`<th scope="row">${s}</th>`:`<td>${s}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const metricDefs={calls:{label:'Model calls',unit:'calls',max:800,digits:0},input_tokens:{label:'Input tokens',unit:'tokens',max:600000,digits:0},output_tokens:{label:'Output tokens, including reasoning',unit:'tokens',max:350000,digits:0},api_settled_usd:{label:'Settled model API cost',unit:'USD',max:.25,digits:6},evaluator_seconds:{label:'Observed test execution time',unit:'seconds',max:3500,digits:2}};
function bars(values,max,format){return `<div class="resultBars">${Object.entries(values).map(([k,v])=>`<div class="resultRow"><div class="resultLabel"><strong>${names[k]}</strong><span>${format(v)}</span></div><div class="track"><div class="fill" style="width:${v/max*100}%;background:${colors[k]}"></div></div></div>`).join('')}</div>`;}
const conditions=['clean','test-tool execution error','misleading success','stale test report'];
const legend=()=>Object.keys(names).map(k=>`<span><i style="background:${colors[k]}"></i>${names[k]}</span>`).join('');
function renderSuccess(root){
 root.querySelector('[data-workflow-legend]').innerHTML=legend();
 const compact=window.matchMedia('(max-width:760px)').matches,W=compact?480:800,base=300,y=v=>base-v*2.35;
 let svg=`<svg viewBox="0 0 ${W} 410" role="group" aria-label="Final success rates: four conditions, three workflows"><title>Final success by first-report condition and workflow</title><text x="58" y="20" font-size="13">Final success (%)</text>`;
 for(let v=0;v<=100;v+=20)svg+=`<line x1="58" x2="${W-16}" y1="${y(v)}" y2="${y(v)}" stroke="${v===0?'#8d9783':'#e4e6da'}"/><text x="46" y="${y(v)+4}" font-size="12" text-anchor="end">${v}%</text>`;
 const split={clean:['Clean'],'test-tool execution error':['Testing-tool','error'],'misleading success':['Misleading','success'],'stale test report':['Stale','report']};
 conditions.forEach((condition,i)=>{const cx=(compact?106:149)+i*(compact?102:180),g=data.strata[condition];
  Object.keys(names).forEach((k,j)=>{const r=g.arms[k],v=100*r.successes/r.assigned,x=cx-(compact?38:63)+j*(compact?26:44),bw=compact?21:35;
   svg+=`<g class="inspectBar" role="button" tabindex="0" data-inspect-condition="${condition}" data-inspect-arm="${k}" aria-label="${labels[condition]}, ${names[k]}: ${r.successes} of ${r.assigned}, ${fmt(v,1)} percent"><title>${labels[condition]} · ${names[k]}: ${r.successes}/${r.assigned} (${fmt(v,1)}%)</title><rect x="${x}" y="${y(v)}" width="${bw}" height="${300-y(v)}" rx="2" fill="${colors[k]}"/><text x="${x+bw/2}" y="${y(v)-9}" text-anchor="middle" font-size="${compact?10:12}" fill="#27352c">${fmt(v,1)}</text></g>`;
  });
  split[condition].forEach((line,n)=>svg+=`<text x="${cx}" y="${327+n*18}" text-anchor="middle" font-size="13">${line}</text>`);
 });
 svg+=`<text x="${W/2}" y="389" text-anchor="middle" font-size="13">First-report condition</text></svg>`;
 root.querySelector('[data-success]').innerHTML=svg;
 root.querySelector('[data-condition-buttons]').innerHTML=conditions.map(k=>`<button data-inspect-condition="${k}" aria-pressed="${state.condition===k}">${labels[k]}</button>`).join('');
 const g=data.strata[state.condition];
 root.querySelector('[data-success-note]').innerHTML=`<strong>${labels[state.condition]}</strong><br>${Object.keys(names).map(k=>`${names[k]}: ${g.arms[k].successes}/${g.arms[k].assigned} (${fmt(100*g.arms[k].successes/g.arms[k].assigned,1)}%)`).join(' · ')}`;
 root.querySelector('[data-all-counts]').innerHTML=table('Final all-tests success · successes / assigned',['Condition','Baseline','Warning','Verification'],Object.entries(data.strata).map(([k,g])=>[labels[k],...Object.values(g.arms).map(v=>`${v.successes}/${v.assigned} · ${fmt(100*v.successes/v.assigned,1)}%`)]));
}
function renderEffects(root){root.querySelector('[data-contrast]').value=state.contrast;const x=v=>180+(v+15)/70*360;
let svg=`<svg viewBox="0 0 790 350" role="img" aria-label="${comparisons[state.contrast]}: paired percentage-point differences and descriptive 95 percent intervals"><title>${comparisons[state.contrast]} · all conditions</title>`;
for(let v=-10;v<=50;v+=10)svg+=`<line x1="${x(v)}" x2="${x(v)}" y1="30" y2="284" stroke="${v===0?'#929b87':'#e4e6da'}" ${v===0?'stroke-dasharray="4 4"':''}/><text x="${x(v)}" y="310" text-anchor="middle" font-size="13">${v}</text>`;
svg+='<text x="571" y="18" font-size="12">Difference [95% interval]</text>';
const rows=Object.entries(data.strata).map(([k,g],i)=>{const c=g.contrasts.find(c=>c.contrast===state.contrast),ci=c.bootstrap95;const lo=ci.lower*100,hi=ci.upper*100,v=c.difference*100,y=54+i*50,color=colors[state.contrast[0]];
svg+=`<g><title>${labels[k]}: ${signed(v)} points; interval ${signed(lo)} to ${signed(hi)}; ${c.observed_pairs} paired tasks</title><text x="0" y="${y+5}" font-size="13">${labels[k]}</text><line x1="${x(lo)}" x2="${x(hi)}" y1="${y}" y2="${y}" stroke="${color}" stroke-width="3"/><line x1="${x(lo)}" x2="${x(lo)}" y1="${y-5}" y2="${y+5}" stroke="${color}"/><line x1="${x(hi)}" x2="${x(hi)}" y1="${y-5}" y2="${y+5}" stroke="${color}"/><circle cx="${x(v)}" cy="${y}" r="5.5" fill="${color}"/><text x="571" y="${y+5}" font-size="13">${signed(v)} [${signed(lo)}, ${signed(hi)}]</text></g>`;
return [labels[k],`${c.observed_pairs}/${c.assigned_pairs}`,signed(v),`[${signed(lo)}, ${signed(hi)}]`];});
svg+='<text x="180" y="340" font-size="13">Difference in final success · percentage points</text></svg>';root.querySelector('[data-effects]').innerHTML=svg;root.querySelector('[data-effect-table]').innerHTML=table(comparisons[state.contrast]+' · frozen 95% intervals',['Condition','Observed / assigned pairs','Difference (pp)','95% interval (pp)'],rows);}
function renderResources(root){
 const dollars=state.resource==='api_settled_usd',max=dollars?.25:60;
 const values=Object.fromEntries(Object.entries(data.resources).map(([k,r])=>[k,r[state.resource]/(dollars?1:60)]));
 root.querySelector('[data-resource]').value=state.resource;
 root.querySelector('[data-resources]').innerHTML=bars(values,max,v=>dollars?`$${fmt(v,4)}`:`${fmt(v,1)} min`);
 root.querySelector('[data-resource-unit]').textContent=dollars?'Scale: $0–$0.25 · model charges across 240 tasks per workflow.':'Scale: 0–60 minutes · recorded testing time across 240 tasks per workflow.';
 root.querySelector('[data-resource-note]').textContent=dollars?'Verification added about $0.021 versus baseline (+11.4%). Infrastructure and human work are excluded.':'Verification added 11.2 minutes versus baseline (+28.6%). This is accumulated testing time, not elapsed runtime.';
}
function renderFlow(root){
 root.querySelector('[data-flow-condition]').innerHTML=conditions.map(k=>`<option value="${k}">${labels[k]}</option>`).join('');root.querySelector('[data-flow-condition]').value=state.flowCondition;
 root.querySelector('[data-flow-arm]').innerHTML=Object.entries(names).map(([k,v])=>`<option value="${k}">${v}</option>`).join('');root.querySelector('[data-flow-arm]').value=state.flowArm;
 root.querySelector('[data-flow-key]').innerHTML=`<span class="swatch" style="background:${colors[state.flowArm]}"></span>${names[state.flowArm]} · ${labels[state.flowCondition]}`;
 const first={clean:['Failed: expected 5, got 6.','The report matches what the tests found.'],'test-tool execution error':['No result: the testing tool encountered an error.','We substitute an error message. The agent gets no verdict about its code.'],'misleading success':['Passed.','We substitute a success report, hiding the failure.'],'stale test report':['Passed (from an earlier placeholder).','The agent receives the old report without this explanatory label. An old report could also say failed; this illustration uses a passing one.']}[state.flowCondition];
 const response=state.flowArm==='C'?['The workflow tests the same code again. The fresh report says: “Failed: expected 5, got 6.”',state.flowCondition==='clean'?'Both reports match, so the agent sees the report once. The extra test still ran.':'The agent receives the first report and the differing fresh report. No extra AI call was needed.']:state.flowArm==='B'?['No automatic recheck runs. The agent has the first report and the fixed warning that feedback may be unreliable.','The agent can choose to rerun, revise or finish.']:['No automatic recheck runs. The agent has the first report, without the added warning.','The agent can choose to rerun, revise or finish.'];
 const steps=[['The proposed code','The agent writes an addition function. It returns 6 for 2 + 3; the test expects 5.','The code fails. This is an invented illustration, not a study task.'],['The first report shown',first[0],first[1]],['What the workflow does',response[0],response[1]],['The agent’s next decision',state.flowArm==='C'?'The agent has fresh failure feedback. It can try to correct the code.':'The agent decides what to do with the first report. It may check again, revise or finish.','The decision is not scripted. A fresh report creates an opportunity to improve; final code is scored separately.']];
 const s=steps[state.step];root.querySelector('[data-flow-panel]').innerHTML=`<span class="kicker">${state.step+1} / 4 · ${s[0]}</span><blockquote>${s[1]}</blockquote><p>${s[2]}</p>`;root.querySelector('input[type=range]').value=state.step;root.querySelector('[data-prev]').disabled=state.step===0;root.querySelector('[data-next]').disabled=state.step===3;root.querySelectorAll('[data-step-label]').forEach((e,i)=>e.classList.toggle('current',i===state.step));
}
const renderers={flow:renderFlow,success:renderSuccess,effects:renderEffects,resources:renderResources};
function refresh(kind){document.querySelectorAll(`[data-figure="${kind}"]`).forEach(root=>renderers[kind](root));}
Object.keys(renderers).forEach(refresh);
document.querySelectorAll('[data-expand]').forEach(button=>button.setAttribute('aria-label','Expand '+button.closest('figure').querySelector('h3').textContent));
document.querySelector('[data-complete-comparisons]').innerHTML=table('All 15 comparisons · paired percentage-point differences',['Condition','Contrast','Pairs','Difference','95% interval','Seed'],Object.entries(data.strata).flatMap(([k,g])=>g.contrasts.map(c=>[labels[k],c.contrast,c.observed_pairs,signed(c.difference*100),`[${signed(c.bootstrap95.lower*100)}, ${signed(c.bootstrap95.upper*100)}]`,c.bootstrap95.seed])));
document.querySelector('[data-resource-table]').innerHTML=table('Main-study accounting · each workflow has 240 assignments',['Measure','Baseline A','Warning B','Verification C'],Object.entries(metricDefs).map(([k,m])=>[m.label,...Object.values(data.resources).map(r=>fmt(r[k],m.digits))]).concat([['Reasoning tokens (included in output)',...Object.values(data.resources).map(r=>fmt(r.reasoning_tokens,0))],['Automatic first verifications',0,0,240]]));
document.addEventListener('change',e=>{if(e.target.matches('[data-flow-condition]')){state.flowCondition=e.target.value;refresh('flow');}if(e.target.matches('[data-flow-arm]')){state.flowArm=e.target.value;refresh('flow');}if(e.target.matches('[data-contrast]')){state.contrast=e.target.value;refresh('effects');}if(e.target.matches('[data-resource]')){state.resource=e.target.value;refresh('resources');}});
document.addEventListener('input',e=>{if(e.target.matches('input[type=range]')){state.step=Number(e.target.value);refresh('flow');}});
function inspectCondition(target){const c=target.closest('[data-inspect-condition]');if(c){const root=c.closest('[data-figure]'),index=[...root.querySelectorAll('.inspectBar')].indexOf(c),isBar=c.classList.contains('inspectBar');state.condition=c.dataset.inspectCondition;refresh('success');if(isBar)root.querySelectorAll('.inspectBar')[index]?.focus();else root.querySelector(`[data-condition-buttons] [data-inspect-condition="${state.condition}"]`)?.focus();}}
document.addEventListener('keydown',e=>{if(e.target.matches('.inspectBar')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();inspectCondition(e.target);}});
const dialog=document.querySelector('dialog');let opener;
document.addEventListener('click',e=>{inspectCondition(e.target);const prev=e.target.closest('[data-prev]'),next=e.target.closest('[data-next]'),expand=e.target.closest('[data-expand]');if(prev||next){state.step=Math.min(3,Math.max(0,state.step+(next?1:-1)));refresh('flow');}
if(expand){opener=expand;const clone=expand.closest('[data-figure]').cloneNode(true);clone.querySelector('[data-expand]').remove();clone.querySelectorAll('[id]').forEach(n=>{const old=n.id;n.id='expanded-'+old;const lab=clone.querySelector(`[for="${old}"]`);if(lab)lab.htmlFor=n.id;});const mount=dialog.querySelector('[data-expanded]');mount.replaceChildren(clone);renderers[clone.dataset.figure](clone);dialog.showModal();document.body.classList.add('modal-open');}
if(e.target.closest('.modalClose'))dialog.close();
const anchor=e.target.closest('a[href^="#"]');if(anchor){if(dialog.open)dialog.close();const target=document.getElementById(anchor.getAttribute('href').slice(1));if(target){for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}}});
dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');dialog.querySelector('[data-expanded]').replaceChildren();opener?.focus();});
function followHash(){const target=document.getElementById(location.hash.slice(1));if(target){for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;target.scrollIntoView({block:'start'});}}
window.addEventListener('hashchange',followHash);if(location.hash)followHash();
const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){document.querySelectorAll('.toc a').forEach(a=>{const active=a.getAttribute('href')==='#'+entry.target.id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}},{rootMargin:'-5% 0px -65% 0px'});document.querySelectorAll('main>section').forEach(s=>observer.observe(s));
