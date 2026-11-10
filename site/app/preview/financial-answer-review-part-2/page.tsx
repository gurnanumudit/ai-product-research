import type { Metadata } from 'next';
import { PartTwo } from '@/components/financial-answer-review-part-2/page';
export const metadata: Metadata = {title:'Which financial AI answers should we review? Part 2',robots:{index:false,follow:false}};
export default function Page(){return <PartTwo draft/>;}
