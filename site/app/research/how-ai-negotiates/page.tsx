import type { Metadata } from 'next';
import { NegotiationArticle } from '@/components/negotiation/article';
import { localReview, publicOrigin } from '@/lib/research-release';
const title = 'How AI negotiates';
const description = 'We tested different buyer instructions in 2,160 synthetic negotiations and measured what both sides earned.';
const url = `${publicOrigin}/research/how-ai-negotiates`;
const image = `${publicOrigin}/research-assets/negotiation/negotiation-hero-v1.png`;
export const metadata: Metadata = {
 title, description, robots:{index:!localReview,follow:!localReview}, alternates:{canonical:url},
 openGraph:{title,description,type:'article',url,publishedTime:'2026-10-29',modifiedTime:'2026-10-29',authors:['Mudit Gurnani'],images:[{url:image,type:'image/png',alt:'A buyer and seller consider a contract across a table.'}]},
 twitter:{card:'summary_large_image',title,description,images:[image]},
};
export default function Page(){return <NegotiationArticle published/>;}
