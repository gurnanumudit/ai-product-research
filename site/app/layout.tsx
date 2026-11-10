import type { Metadata } from "next";
import { requestSiteUrl, socialPreviewUrl } from "@/lib/site-url";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";
import "@/components/article/standard.css";

const themeBootScript = `(() => {
  try {
    const saved = localStorage.getItem("research-site-theme");
    const theme = saved === "dark" || saved === "light" ? saved : "light";
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#05060a" : "#f7f5ef"
    );
  } catch (_) {
    document.documentElement.dataset.theme = "light";
  }
})();`;

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
    alternates: {
      types: { "application/rss+xml": `${siteUrl}/feed.xml` },
    },
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
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#f7f5ef" />
        <script dangerouslySetInnerHTML={{ __html: themeBootScript }} />
      </head>
      <body>
        <div className="themeCanvas">{children}</div>
        <ThemeToggle />
      </body>
    </html>
  );
}
