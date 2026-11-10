import type { Metadata } from "next";
import { ResearchHome } from "@/components/research-home";
import { publication } from "@/content/publication";
import { publishedStudies } from "@/content/research-catalog";
import { localReview, publicOrigin } from "@/lib/research-release";

const description = "What is an AI system actually worth, and how do you know? Independent research by Mudit Gurnani on AI cost, success, decision quality and agent behavior.";

export const metadata: Metadata = {
  title: { absolute: "Mudit Gurnani | Research" },
  description,
  robots: { index: !localReview, follow: !localReview },
  alternates: { canonical: publicOrigin + "/" },
  openGraph: { title: "Mudit Gurnani | Research", description, type: "website", url: publicOrigin + "/", images: [{ url: publicOrigin + "/og-research-journey-v1.png", width: 1600, height: 840, type: "image/png", alt: "Mudit Gurnani: Exploring AI through experiments. Models, reasoning, and real-world analytical work." }] },
  twitter: { card: "summary_large_image", title: "Mudit Gurnani | Research", description, images: [publicOrigin + "/og-research-journey-v1.png"] },
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Person",
      "@id": `${publicOrigin}/#mudit-gurnani`,
      name: publication.name,
      url: publicOrigin,
      sameAs: [publication.linkedin, publication.repository],
      knowsAbout: ["AI evaluation", "AI economics", "agent behavior", "data science"],
    },
    {
      "@type": "WebSite",
      "@id": `${publicOrigin}/#website`,
      name: "Mudit Gurnani | Research",
      url: publicOrigin,
      description,
      author: { "@id": `${publicOrigin}/#mudit-gurnani` },
    },
    {
      "@type": "ItemList",
      name: "Published AI research",
      numberOfItems: publishedStudies.length,
      itemListElement: publishedStudies.map((study, index) => ({
        "@type": "ListItem",
        position: index + 1,
        url: `${publicOrigin}${study.path}`,
        name: study.title,
      })),
    },
  ],
};

export default function HomePage() {
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />
    <ResearchHome />
  </>;
}
