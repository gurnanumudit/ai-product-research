import type { Metadata } from "next";
import { FinancialAnswerReviewArticle } from "@/components/financial-answer-review/page";
import { localReview, publicOrigin } from "@/lib/research-release";
const title = "Which financial AI answers should we review?";
const description = "We compared AI confidence with rule-based verification on 1,127 financial answers. Confidence found more answer-key mismatches at smaller review budgets.";
const url = `${publicOrigin}/research/which-financial-ai-answers-should-we-review`;
const image = `${publicOrigin}/research-assets/financial-answer-review/cover-v3.png`;
export const metadata: Metadata = {
  title, description, robots: { index: !localReview, follow: !localReview }, alternates: { canonical: url },
  openGraph: { title, description, type: "article", url, publishedTime: "2026-10-10", authors: ["Mudit Gurnani"], images: [{ url: image, width: 1774, height: 887, type: "image/png", alt: "A small selection of paper tiles placed in a review tray." }] },
  twitter: { card: "summary_large_image", title, description, images: [image] },
};
export default function Page() { return <FinancialAnswerReviewArticle />; }
