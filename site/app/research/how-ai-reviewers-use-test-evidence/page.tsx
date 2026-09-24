import type { Metadata } from "next";
import { EvidenceReviewArticle } from "@/components/article/page";
import { localReview, publicOrigin } from "@/lib/research-release";
export const metadata: Metadata = {
  title: "How AI reviewers use test evidence",
  description: "How three AI reviewers responded to five test-evidence scenarios across 60 software tasks.",
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: publicOrigin + "/research/how-ai-reviewers-use-test-evidence" },
  openGraph: { title: "How AI reviewers use test evidence", description: "How three reviewers interpreted test evidence—and why avoiding faulty approvals is only half the story.", images: [] },
  twitter: { card: "summary", title: "How AI reviewers use test evidence", description: "How three reviewers interpreted test evidence—and why avoiding faulty approvals is only half the story.", images: [] },
};
export default function Article() { return <EvidenceReviewArticle review={false} />; }
