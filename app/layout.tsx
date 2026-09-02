import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: {
    default: "Mudit Gurnani — Research & Writing",
    template: "%s — Mudit Gurnani",
  },
  description:
    "Experiments and essays about AI, products, and questions worth testing.",
  openGraph: {
    type: "website",
    title: "Mudit Gurnani — Research & Writing",
    description: "Experiments and essays about AI, products, and questions worth testing.",
    images: [{ url: "/og.png", width: 1730, height: 909 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Mudit Gurnani — Research & Writing",
    description: "Experiments and essays about AI, products, and questions worth testing.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
