import type {Metadata} from 'next';
import {LunaRevision} from '@/components/luna-revision/article';
import {StructuredResearchData} from '@/components/article/structured-research-data';
import {localReview,publicOrigin} from '@/lib/research-release';
const title='When does asking AI to revise its answer help?';
const description='A study of structured prompts and one revision on 100 coding problems and 100 planning puzzles. Revision helped coding; planning remained uncertain.';
const path='/research/when-does-asking-ai-to-revise-help';
const cover='/research-assets/luna-revision/revision-cover-v1.png';
const url=`${publicOrigin}${path}`;const image=`${publicOrigin}${cover}`;
export const metadata:Metadata={title,description,robots:{index:!localReview,follow:!localReview},alternates:{canonical:url},openGraph:{title,description,type:'article',url,publishedTime:'2026-11-16',modifiedTime:'2026-11-16',authors:['Mudit Gurnani'],images:[{url:image,width:1774,height:887,type:'image/png',alt:'An indigo figure reviews code and a planning puzzle at a stone desk'}]},twitter:{card:'summary_large_image',title,description,images:[image]}};
export default function Page(){return <><StructuredResearchData title={title} description={description} path={path} image={cover} published="2026-11-16"/><LunaRevision published/></>;}
