"use client";
import {useEffect,useRef} from 'react';
import {ArticleIndex} from '@/components/article/article-index';
import {ArticleNavigation} from '@/components/article/article-navigation';
import content from './content.json';
import {initializeArticle} from './interactions';
import './article.css';
const entries=[{id:'question',title:'01 · The question'},{id:'design',title:'02 · The mirror test'},{id:'mirror',title:'03 · The lead changes sides'},{id:'starter',title:'04 · Who starts?'},{id:'conclusion',title:'05 · What changed'},{id:'appendix',title:'06 · Appendix'}];
export function NegotiationPartTwo(){const root=useRef<HTMLDivElement>(null);useEffect(()=>{if(root.current)return initializeArticle(root.current);},[]);return <div className="negotiationPartTwo" data-research-article="" ref={root}><ArticleNavigation/><a href="#story" className="skip">Skip to article</a><div dangerouslySetInnerHTML={{__html:content.header}}/><div data-article-layout=""><ArticleIndex entries={entries}><a href="/research-assets/negotiation-part2/chart-data.json" download>Download chart data ↓</a><a href="/research/how-ai-negotiates">Read Part 1</a></ArticleIndex><main id="story" className="article" data-article-body="" dangerouslySetInnerHTML={{__html:content.body}}/></div><div dangerouslySetInnerHTML={{__html:content.footer}}/></div>}
