import type { Metadata } from "next";
import { requestSiteUrl, socialPreviewUrl } from "@/lib/site-url";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const [siteUrl, previewUrl] = await Promise.all([requestSiteUrl(), socialPreviewUrl()]);
  const description =
    "Independent AI product research on when evidence earns the right to change an action, judgment, or model-spend decision.";

  return {
    metadataBase: siteUrl,
    title: {
      default: "Mudit Gurnani — Research & Writing",
      template: "%s — Mudit Gurnani",
    },
    description,
    openGraph: {
      type: "website",
      title: "Mudit Gurnani — Research & Writing",
      description,
      images: [{ url: previewUrl, width: 1731, height: 909, alt: "AI products should earn trust with evidence, not demos." }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Mudit Gurnani — Research & Writing",
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
