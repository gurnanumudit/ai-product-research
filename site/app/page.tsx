import type { Metadata } from "next";
import { ResearchHome } from "@/components/research-home";
import { localReview, publicOrigin } from "@/lib/research-release";

const description = "Understanding AI through evidence. Independent experiments and data analysis by Mudit Gurnani, exploring what AI can do, where it falls short, and how to use it well.";

export const metadata: Metadata = {
  title: { absolute: "Mudit Gurnani | Research" },
  description,
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: publicOrigin + "/" },
  openGraph: { title: "Mudit Gurnani | Research", description, type: "website", url: publicOrigin + "/", images: [{ url: publicOrigin + "/og-research-journey-v1.png", width: 1600, height: 840, type: "image/png", alt: "Mudit Gurnani — Exploring AI through experiments. Models, reasoning, and real-world analytical work." }] },
  twitter: { card: "summary_large_image", title: "Mudit Gurnani | Research", description, images: [publicOrigin + "/og-research-journey-v1.png"] },
};

export default ResearchHome;
