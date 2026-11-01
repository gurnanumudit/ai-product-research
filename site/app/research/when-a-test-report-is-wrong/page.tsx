import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ToolErrorArticle } from "@/components/tool-error/article";
import { localReview, publicOrigin } from "@/lib/research-release";

const title = "When a test report is wrong, is a warning enough?";
const description = "An experiment with 240 coding tasks compares a warning with an automatic fresh check across four kinds of first test report.";

export const metadata: Metadata = {
  title: { absolute: title + " | Mudit Gurnani" }, description,
  robots: { index: false, follow: false },
  alternates: { canonical: publicOrigin + "/research/when-a-test-report-is-wrong" },
  openGraph: { title, description, type: "article", url: publicOrigin + "/research/when-a-test-report-is-wrong", images: [{ url: publicOrigin + "/research-assets/tool-error/cover.png", width: 1200, height: 630, alt: "Conceptual illustration: a reassuring report is checked again." }] },
  twitter: { card: "summary_large_image", title, description, images: [publicOrigin + "/research-assets/tool-error/cover.png"] },
};

// The owner requested upload preparation and a draft, not publication.
export default function Page() {
  if (!localReview) notFound();
  return <ToolErrorArticle />;
}
