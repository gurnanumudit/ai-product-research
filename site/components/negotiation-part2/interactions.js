export function initializeArticle(root){
const abort=new AbortController();const cleanups=[];const byId=id=>root.querySelector('#'+id);
function listen(el,type,fn){el.addEventListener(type,fn);cleanups.push(()=>el.removeEventListener(type,fn));}
const dialog=byId('chartDialog');let opener;
root.querySelectorAll('.expand').forEach(button=>listen(button,'click',()=>{opener=button;const copy=button.closest('figure').cloneNode(true);copy.removeAttribute('id');copy.querySelectorAll('.expand').forEach(b=>b.remove());byId('expandedFigure').replaceChildren(copy);dialog.showModal();}));
listen(root.querySelector('.dialogClose'),'click',()=>dialog.close());listen(dialog,'close',()=>opener?.focus());
(async()=>{
const app=byId('uncertaintyApp');
try{
const response=await fetch('/research-assets/negotiation-part2/distribution-data.json',{signal:abort.signal});if(!response.ok)throw Error('Data unavailable');const data=await response.json();if(abort.signal.aborted)return;
const cells=data.cells;let selected=0,chosenGap=null;
const fmt=n=>(n>0?'+':'')+n.toFixed(2).replace('-','−');
const gapText=n=>n>0?`Buyer earned ${n} more`:n<0?`Seller earned ${-n} more`:'Equal gains';
const gapLabel=n=>n===0?'Equal gains':gapText(n)+' points';
const label=c=>(c.category==='tradeoffs'?'Tradeoffs':c.category==='narrow_zone'?'Narrow zone':'No acceptable deal')+' · '+c.starter+' starts';
const color=n=>n>0?'#287565':n<0?'#bf6347':'#8a9182';
const gaps=cells.flatMap(c=>c.outcomes.map(o=>o.gap));
const minGap=Math.floor(Math.min(...gaps)/5)*5,maxGap=Math.ceil(Math.max(...gaps)/5)*5;
const maxCount=Math.max(...cells.flatMap(c=>c.frequency.map(v=>v.count)));
const allBins=Array.from({length:(maxGap-minGap)/5+1},(_,i)=>minGap+i*5);
app.innerHTML=`<div class="groupButtons" role="group" aria-label="Choose bargaining situation and starter">${cells.map((c,i)=>`<button type="button" data-cell="${i}" aria-pressed="${i===selected}">${label(c)}</button>`).join('')}</div><div id="groupSummary" aria-live="polite"></div><div id="outcomeCounts" class="outcomeCounts"></div><p class="uiExplanation">Each bar counts negotiations with that exact gain difference. Select a bar to inspect them. The scales stay the same across groups.</p><div id="spreadChart" class="spreadChart"></div><div id="gapSelection" class="gapSelection" aria-live="polite"></div><details class="individualDetails"><summary>Inspect individual negotiations</summary><div id="individualTable" class="tableScroll"></div></details><details class="missingSensitivity"><summary>What could the unknown outcomes change?</summary><div id="missingExplanation"></div></details>`;
function spread(c){
 const left=52,width=650,baseline=265,plotHeight=220;const step=width/allBins.length,x=g=>left+(g-minGap)/5*step+step/2;
 let svg=`<svg viewBox="0 0 740 355" role="group" aria-label="Individual negotiation gain differences; bar height is number of completed negotiations"><text x="5" y="18">Count</text>`;
 for(let n=0;n<=maxCount;n+=20){const y=baseline-n/maxCount*plotHeight;svg+=`<line x1="52" y1="${y}" x2="702" y2="${y}" stroke="#e1e5da"/><text x="41" y="${y+4}" text-anchor="end">${n}</text>`}
 svg+=`<line x1="${x(0)}" y1="30" x2="${x(0)}" y2="265" stroke="#707b66" stroke-dasharray="3 5"/>`;
 for(const gap of allBins){const count=c.frequency.find(b=>b.gap===gap)?.count||0;const ht=count/maxCount*plotHeight;
  if(count)svg+=`<g role="button" tabindex="0" data-gap="${gap}" aria-pressed="${chosenGap===gap}" aria-label="${gapLabel(gap)}: ${count} negotiations"><title>${gapLabel(gap)}: ${count} negotiations</title><rect x="${x(gap)-step*.38}" y="${baseline-ht}" width="${step*.76}" height="${Math.max(ht,2)}" fill="${color(gap)}" stroke="${chosenGap===gap?'#20291d':'none'}" stroke-width="3"/></g>`;
  if(gap%10===0)svg+=`<text x="${x(gap)}" y="285" text-anchor="middle">${gap}</text>`;
 }
 svg+='<text x="370" y="313" text-anchor="middle">Buyer gain minus seller gain · game points</text><text x="80" y="342">← Seller earned more</text><text x="530" y="342">Buyer earned more →</text></svg>';
 byId('spreadChart').innerHTML=svg;
}
function details(c){
 const rows=c.outcomes.filter(o=>chosenGap===null||o.gap===chosenGap);
 byId('gapSelection').innerHTML=chosenGap===null?`Showing all ${c.completed} completed negotiations. Select a bar for one exact difference.`:`${gapLabel(chosenGap)}: <strong>${rows.length}</strong> negotiations. <button type="button" id="clearGap">Show all differences</button>`;
 byId('individualTable').innerHTML='<table><thead><tr><th>Negotiation</th><th>Economy</th><th>Buyer gain</th><th>Seller gain</th><th>Difference</th><th>Outcome</th></tr></thead><tbody>'+rows.map(r=>`<tr><td>${r.episode_id}</td><td>${r.orientation==='mirror'?'Mirrored':'Original'}</td><td>${r.buyer_gain}</td><td>${r.seller_gain}</td><td>${r.gap}</td><td>${r.terminal_reason==='walkaway'?'Walkaway':'Agreement'}</td></tr>`).join('')+'</tbody></table>';
}
function render(){
 const c=cells[selected];app.querySelectorAll('[data-cell]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.cell)===selected));

 byId('groupSummary').innerHTML=`<h4>${label(c)}</h4><p class="uiExplanation">${c.completed} completed of ${c.assigned} assigned · ${c.unknown} unknown · ${c.families.length} scenario families</p>`;
 const counts=c.comparison_counts;byId('outcomeCounts').innerHTML=`<div class="buyerCount"><strong>${counts.buyer_higher}</strong><span>Buyer earned more</span></div><div class="sellerCount"><strong>${counts.seller_higher}</strong><span>Seller earned more</span></div><div><strong>${counts.equal}</strong><span>Equal gains</span></div><div class="unknownCount"><strong>${c.unknown}</strong><span>Unknown</span></div><p class="equalBreakdown">Equal gains include ${c.equal_walkaways} walkaways and ${c.equal_agreements} equal-gain agreements. Earning more than the other side is different from benefiting relative to walking away.</p>`;
 const target=byId('missingExplanation');
 if(c.category==='no_zone'){target.innerHTML=`<p class="uiExplanation">All ${c.completed} completed negotiations ended in walkaway, with zero gain for both sides. ${c.unknown?`${c.unknown} assigned outcome remains unknown and is not counted as a walkaway.`:'All assigned negotiations completed.'} No confidence interval is reported for this descriptive zero-gain distribution.</p>`;}
 else {const [lo,hi]=c.full_schedule_sample_legal_bounds;target.innerHTML=c.unknown?`<p class="uiExplanation">${c.unknown} outcomes are unknown. The full ${c.assigned}-assignment average could range from ${fmt(lo)} to ${fmt(hi)} points under legal missing-outcome bounds.</p><p class="uiCaveat">This fixed-sample legal range is not a confidence interval. The main figure’s intervals describe completed-outcome means only.</p>`:`<p class="uiExplanation">All ${c.assigned} negotiations completed. There are no missing outcomes in this group; uncertainty across families remains.</p>`;}

 spread(c);details(c);
}
listen(app,'click',e=>{const button=e.target.closest('[data-cell]');if(button){selected=Number(button.dataset.cell);chosenGap=null;render();return}const bin=e.target.closest('[data-gap]');if(bin){chosenGap=Number(bin.dataset.gap);spread(cells[selected]);details(cells[selected]);return}if(e.target.closest('#clearGap')){chosenGap=null;spread(cells[selected]);details(cells[selected]);}});
listen(app,'keydown',e=>{const bin=e.target.closest('[data-gap]');if(bin&&(e.key==='Enter'||e.key===' ')){e.preventDefault();chosenGap=Number(bin.dataset.gap);spread(cells[selected]);details(cells[selected]);const replacement=app.querySelector(`[data-gap="${chosenGap}"]`);replacement?.focus();}});
render();
}catch(error){if(abort.signal.aborted)return;app.textContent='The interactive chart could not load. The exact results remain available in the table below and the downloadable data.';console.error(error)}
})();

return ()=>{abort.abort();cleanups.forEach(fn=>fn());if(dialog.open)dialog.close();};}
