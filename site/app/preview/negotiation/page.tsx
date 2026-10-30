import type { Metadata } from 'next';
import { NegotiationArticle } from '@/components/negotiation/article';
export const metadata: Metadata = {title:'How AI negotiates | Review draft',description:'An interactive study of 2,160 synthetic negotiations: instructions, opponents, and the division of gains.',robots:{index:false,follow:false}};
export default function Page(){return <NegotiationArticle/>;}
