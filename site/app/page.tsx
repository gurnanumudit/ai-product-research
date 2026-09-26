import type { Metadata } from "next";
import { ResearchHome } from "@/components/research-home";
import { localReview, publicOrigin } from "@/lib/research-release";

const description = "I'm starting a research journey into how AI performs on real-world tasks. Here I share experiments, findings, and code—exploring when reasoning helps, what better results cost, and how to evaluate AI beyond demos.";

export const metadata: Metadata = {
  title: { absolute: "Mudit Gurnani | Research" },
  description,
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: publicOrigin + "/" },
  openGraph: { title: "Mudit Gurnani | Research", description, type: "website", url: publicOrigin + "/", images: [{ url: publicOrigin + "/og-research-journey-v1.png", width: 1600, height: 840, type: "image/png", alt: "Mudit Gurnani — Exploring AI through experiments. Models, reasoning, and real-world analytical work." }] },
  twitter: { card: "summary_large_image", title: "Mudit Gurnani | Research", description, images: [publicOrigin + "/og-research-journey-v1.png"] },
};

export default ResearchHome;
