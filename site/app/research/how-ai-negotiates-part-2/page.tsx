import type {Metadata} from 'next';
import {NegotiationPartTwo} from '@/components/negotiation-part2/article';
import {localReview,publicOrigin} from '@/lib/research-release';
const title='How AI negotiates Part 2';const description='Does the buyer’s lead survive when economic opportunities are reversed? A study of 960 assigned negotiations, with both starting roles.';
const url=`${publicOrigin}/research/how-ai-negotiates-part-2`;const image=`${publicOrigin}/research-assets/negotiation-part2/negotiation-hero-v1.png`;
export const metadata:Metadata={title,description,robots:{index:!localReview,follow:!localReview},alternates:{canonical:url},openGraph:{title,description,type:'article',url,publishedTime:'2026-11-04',modifiedTime:'2026-11-04',authors:['Mudit Gurnani'],images:[{url:image,type:'image/png',alt:'Ochre and indigo negotiators exchange positions across a stone table'}]},twitter:{card:'summary_large_image',title,description,images:[image]}};
export default function Page(){return <NegotiationPartTwo/>;}
