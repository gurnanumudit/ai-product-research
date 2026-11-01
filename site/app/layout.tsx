import type { Metadata } from "next";
import { requestSiteUrl, socialPreviewUrl } from "@/lib/site-url";
import "./globals.css";
import "@/components/article/standard.css";

export async function generateMetadata(): Promise<Metadata> {
  const [siteUrl, previewUrl] = await Promise.all([requestSiteUrl(), socialPreviewUrl()]);
  const description =
    "Experiments, simulations and data analysis on AI evaluation, agent behavior and economic tradeoffs. Independent research by Mudit Gurnani.";

  return {
    metadataBase: siteUrl,
    title: {
      default: "Mudit Gurnani | Research & Writing",
      template: "%s | Mudit Gurnani",
    },
    description,
    openGraph: {
      type: "website",
      title: "Mudit Gurnani | Research & Writing",
      description,
      images: [{ url: previewUrl, width: 1600, height: 840, alt: "Mudit Gurnani | Exploring AI through experiments. Models, reasoning, and real-world analytical work." }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Mudit Gurnani | Research & Writing",
      description,
      images: [previewUrl],
    },
    icons: { icon: "/og.png" },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
