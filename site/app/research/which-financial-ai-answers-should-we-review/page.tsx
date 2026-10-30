import type { Metadata } from "next";
import { FinancialAnswerReviewArticle } from "@/components/financial-answer-review/page";
import { localReview, publicOrigin } from "@/lib/research-release";
const title = "Which financial AI answers should we review? Part 1";
const description = "On 1,127 financial answers, verification selected more answer-key mismatches than AI confidence. A study of how to prioritize limited review capacity.";
const url = `${publicOrigin}/research/which-financial-ai-answers-should-we-review`;
const image = `${publicOrigin}/research-assets/financial-answer-review/cover-v3.png`;
export const metadata: Metadata = {
  title, description, robots: { index: !localReview, follow: !localReview }, alternates: { canonical: url },
  openGraph: { title, description, type: "article", url, publishedTime: "2026-10-10", modifiedTime: "2026-10-21", authors: ["Mudit Gurnani"], images: [{ url: image, width: 1774, height: 887, type: "image/png", alt: "A small selection of paper tiles placed in a review tray." }] },
  twitter: { card: "summary_large_image", title, description, images: [image] },
};
export default function Page() { return <FinancialAnswerReviewArticle />; }
