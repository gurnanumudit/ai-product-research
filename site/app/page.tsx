import type { Metadata } from "next";
import { ResearchHome } from "@/components/research-home";
import { localReview, publicOrigin } from "@/lib/research-release";

export const metadata: Metadata = {
  title: { absolute: "Mudit Gurnani | Research" },
  description: "Research on AI evaluation, decision-making, and the economics of AI effort.",
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: publicOrigin + "/" },
  openGraph: { title: "Mudit Gurnani | Research", description: "Independent experiments on AI evaluation and cost–quality trade-offs.", type: "website", url: publicOrigin + "/", images: [{ url: publicOrigin + "/og-v2.png", width: 1731, height: 909, type: "image/png", alt: "Mudit Gurnani — independent AI product research" }] },
  twitter: { card: "summary_large_image", title: "Mudit Gurnani | Research", description: "Independent experiments on AI evaluation and cost–quality trade-offs.", images: [publicOrigin + "/og-v2.png"] },
};

export default ResearchHome;
