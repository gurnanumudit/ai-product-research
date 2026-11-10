import { publication } from "@/content/publication";
import { publicOrigin } from "@/lib/research-release";

type StructuredResearchDataProps = {
  title: string;
  description: string;
  path: string;
  image: string;
  published: string;
  modified?: string;
};

export function StructuredResearchData({
  title,
  description,
  path,
  image,
  published,
  modified = published,
}: StructuredResearchDataProps) {
  const data = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: title,
    description,
    genre: "Independent research",
    datePublished: published,
    dateModified: modified,
    mainEntityOfPage: `${publicOrigin}${path}`,
    image: `${publicOrigin}${image}`,
    author: {
      "@type": "Person",
      name: publication.name,
      url: publicOrigin,
      sameAs: [publication.linkedin, publication.repository],
    },
    isAccessibleForFree: true,
  };

  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}
