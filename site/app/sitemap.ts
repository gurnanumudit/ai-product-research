import type { MetadataRoute } from "next";
import { publishedStudies } from "@/content/research-catalog";
import { publicOrigin } from "@/lib/research-release";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${publicOrigin}/`,
      lastModified: new Date("2026-11-04"),
      changeFrequency: "weekly",
      priority: 1,
    },
    ...publishedStudies.map((study) => ({
      url: `${publicOrigin}${study.path}`,
      lastModified: new Date(study.iso),
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
  ];
}
