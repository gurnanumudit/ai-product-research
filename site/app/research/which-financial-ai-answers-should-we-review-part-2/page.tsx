import type { Metadata } from 'next';
import { PartTwo } from '@/components/financial-answer-review-part-2/page';
import { localReview, publicOrigin } from '@/lib/research-release';
const title = 'Which financial AI answers should we review? Part 2';
const description = 'Across four AI configurations and two financial datasets, confidence and rule-based verification selected different mistakes for review.';
const url = `${publicOrigin}/research/which-financial-ai-answers-should-we-review-part-2`;
const image = `${publicOrigin}/research-assets/financial-answer-review-part-2/cover-v1.png`;
export const metadata: Metadata = {
  title, description, robots:{index:!localReview,follow:!localReview}, alternates:{canonical:url},
  openGraph:{title,description,type:'article',url,publishedTime:'2026-10-21',modifiedTime:'2026-10-21',authors:['Mudit Gurnani'],images:[{url:image,width:1774,height:887,type:'image/png',alt:'Terracotta and teal trays select different paper cards from the same answers.'}]},
  twitter:{card:'summary_large_image',title,description,images:[image]},
};
export default function Page(){return <PartTwo/>;}
