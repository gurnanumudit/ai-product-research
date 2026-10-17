import type { Metadata } from "next";
import { EvaluationReliabilityArticle } from "@/components/evaluation-reliability/page";
import { localReview, publicOrigin } from "@/lib/research-release";

const title = "How to avoid false confidence in AI evaluations";
const description = "A higher evaluation score is not always a reason to switch. Simulations show how related questions, repeated checks and missing results affect the decision.";
const url = `${publicOrigin}/research/how-to-avoid-false-confidence-in-ai-evaluations`;
const image = `${publicOrigin}/research-assets/evaluation-reliability/evaluation-confidence-cover.png`;

export const metadata: Metadata = {
  title, description,
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: url },
  openGraph: { title, description, type: "article", url, publishedTime: "2026-09-30", modifiedTime: "2026-10-17",
    authors: ["Mudit Gurnani"], images: [{ url: image, width: 1774, height: 887, type: "image/png", alt: "A magnifying glass reveals gaps in evaluation evidence." }] },
  twitter: { card: "summary_large_image", title, description, images: [image] },
};

export default function Page() { return <EvaluationReliabilityArticle />; }
