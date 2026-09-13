import type { Metadata } from "next";
import { EvidenceReviewArticle } from "@/components/article/page";
export const metadata: Metadata = {
  title: "How AI reviewers use test evidence",
  description: "How three AI reviewers responded to five test-evidence scenarios across 60 software tasks.",
  robots: { index: false, follow: false },
  openGraph: { title: "How AI reviewers use test evidence", images: [] },
  twitter: { card: "summary", images: [] },
};
export default function Article() { return <EvidenceReviewArticle review={false} />; }
