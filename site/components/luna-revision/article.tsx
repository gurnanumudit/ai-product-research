"use client";
import {useEffect,useRef} from 'react';
import {ArticleIndex} from '@/components/article/article-index';
import {ArticleNavigation} from '@/components/article/article-navigation';
import content from './content.json';
import './article.css';
const entries=[{id:'question',title:'The question'},{id:'design',title:'Three workflows'},{id:'results',title:'The coding result'},{id:'planning',title:'Planning and regressions'},{id:'cost',title:'The extra call'},{id:'takeaway',title:'What we learned'},{id:'appendix',title:'Appendix (optional)'}];
export function LunaRevision({published=false}:{published?:boolean}){
 const header=published?content.header.replace(' <span class="lunaDraft">Draft · not published</span>','').replace('<span class="lunaPending">Research code: publication pending</span>','<a href="https://github.com/gurnanumudit/ai-product-research/tree/7a1a4b5e4d4facbb7eb234bd525495ce3e097b27/research/luna-revision" target="_blank" rel="noreferrer">Research code ↗</a>'):content.header;
 const footer=published?content.footer.replace('Local article draft · study completed November 13, 2026','Study completed November 13, 2026'):content.footer;
 const root=useRef<HTMLDivElement>(null);
 useEffect(()=>{const el=root.current;if(!el)return;const change=(event:MouseEvent)=>{const button=(event.target as Element).closest<HTMLButtonElement>('button[data-domain]');if(!button||!el.contains(button))return;el.querySelectorAll<HTMLButtonElement>('button[data-domain]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));el.querySelectorAll<HTMLElement>('[data-result-panel]').forEach(panel=>{panel.hidden=button.dataset.domain!=='all'&&button.dataset.domain!==panel.dataset.resultPanel;});};el.addEventListener('click',change);return()=>el.removeEventListener('click',change);},[]);
 return <div className="lunaRevision" data-research-article="" ref={root}><ArticleNavigation/><div dangerouslySetInnerHTML={{__html:header}}/><div data-article-layout=""><ArticleIndex entries={entries}><a href="/research-assets/luna-revision/chart-data.json" download>Download chart data ↓</a>{!published&&<span className="lunaIndexNote">Draft preview<br/>Not published</span>}</ArticleIndex><main data-article-body="" dangerouslySetInnerHTML={{__html:content.body}}/></div><div dangerouslySetInnerHTML={{__html:footer}}/></div>;
}
