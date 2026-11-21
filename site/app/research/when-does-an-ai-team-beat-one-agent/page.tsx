import type {Metadata} from 'next';
import {TeamworkArticle} from '@/components/teamwork/article';
import {StructuredResearchData} from '@/components/article/structured-research-data';
import {localReview,publicOrigin} from '@/lib/research-release';
const title='When does an AI team beat one agent?';
const description='One agent, simple teamwork and structured teamwork across 327 completed coding runs. Solo finished more jobs; structured teams had a small model-cost advantage per success.';
const path='/research/when-does-an-ai-team-beat-one-agent';
const cover='/research-assets/teamwork/teamwork-hero.png';
const url=`${publicOrigin}${path}`;const image=`${publicOrigin}${cover}`;
export const metadata:Metadata={title,description,robots:{index:!localReview,follow:!localReview},alternates:{canonical:url},openGraph:{title,description,type:'article',url,publishedTime:'2026-11-21',modifiedTime:'2026-11-21',authors:['Mudit Gurnani'],images:[{url:image,width:1774,height:887,type:'image/png',alt:'Two figures bring separate pieces together at a shared desk'}]},twitter:{card:'summary_large_image',title,description,images:[image]}};
export default function Page(){return <><StructuredResearchData title={title} description={description} path={path} image={cover} published="2026-11-21"/><TeamworkArticle/></>;}
