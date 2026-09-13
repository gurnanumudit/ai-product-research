import type { Metadata } from "next";
import Link from "next/link";
import { MarkdownContent } from "@/components/markdown-content";
import { reviewSections, conciseAppendixSections as appendixSections, technicalAppendix, resultTableSections, findingSummaries, approvalOverviewTakeaway } from "@/content/evidence-review-v3";
import { ArticleIndex } from "./article-index";
import { ApprovalOverview, ScenarioWalkthrough } from "./evidence-exhibits";
import { publication } from "@/content/publication";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "How AI reviewers use test evidence | Review version 3",
  description: "How three AI reviewers used the same test evidence across five review scenarios.",
  robots: { index: false, follow: false },
  openGraph: { title: "How AI reviewers use test evidence", images: [] },
  twitter: { card: "summary", images: [] },
};

function IllustratedText({ body }: { body: string }) {
  return <>{body.replaceAll("**", "").split(/(!\[[^\]]*\]\([^\n]+\))/g).map((part, index) => {
    const image = part.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (!image) return <MarkdownContent key={index} markdown={part} />;
    return <figure key={index} className={styles.chart}>
      <a href={image[2]} target="_blank" rel="noreferrer" aria-label={`Open chart at full size: ${image[1]}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={image[2]} alt={image[1]} loading="lazy" />
      </a><figcaption>Open chart at full size ↗</figcaption>
    </figure>;
  })}</>;
}

const entries = [
  { id: "introduction", title: "Introduction" },
  { id: "experiment-setup", title: "Experiment setup" },
  { id: "approval-overview", title: "Approval across scenarios" },
  { id: "findings-at-a-glance", title: "Three findings at a glance" },
  { id: "finding-1", title: "1. What test evidence changed" },
  { id: "finding-2", title: "2. Same evidence, different decisions" },
  { id: "finding-3", title: "3. The independence label" },
  { id: "conclusion", title: "What this means" },
  { id: "appendix", title: "Appendix" },
  ...appendixSections.map(section => ({ id: section.id, title: ({
    "appendix-a": "A. Tasks and evidence",
    "appendix-b": "B. Models and collection",
    "appendix-c": "C. Metrics and decisions",
    "appendix-d": "D. Analysis and uncertainty",
    "full-tables": "E. Full results",
    "appendix-f": "F. Worked examples",
    "appendix-g": "G. Limitations",
  } as Record<string, string>)[section.id], nested: true })),
];

const technicalLabels: Record<string, string> = {
  "appendix-a": "Detailed selection rules and evidence provenance",
  "appendix-b": "Exact model settings and collection details",
  "appendix-d": "Full statistical definitions and sensitivity calculations",
  "appendix-f": "Source identifiers and reproducibility references",
};

export function EvidenceReviewArticle({ review = true }: { review?: boolean }) {
  return <div className={styles.page}>
    <a className={styles.skip} href="#introduction">Skip to article</a>
    <header className={styles.siteHeader}>
      <Link href="/" className={styles.wordmark}>Mudit Gurnani</Link>
      <nav aria-label="Site navigation"><Link href="/">Research</Link><a href="#appendix">Methods & results</a><a href={publication.linkedin} target="_blank" rel="noreferrer">LinkedIn ↗</a></nav>
    </header>
    <main>
      <header className={styles.hero}>
        <p className={styles.eyebrow}>{review ? "Research · Review version 3" : "Research · AI evaluation"}</p>
        <h1>How AI reviewers<br />use test evidence</h1>
        <p className={styles.subtitle}>We gave three AI reviewers the same proposed fixes. What changed when we supplied test results, more detail, or a different source label?</p>
        <p className={styles.byline}>Mudit Gurnani <span>·</span> September 13, 2026</p>
        <p className={styles.resourceLine}><a href={publication.articleCodeUrl ?? publication.repository} target="_blank" rel="noreferrer">{publication.articleCodeUrl ? "Study code and data" : "Research repository"} ↗</a>{!publication.articleCodeUrl && <span> · Study-specific code and data release pending</span>}</p>
      </header>
      <figure className={styles.cover}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/research-assets/evidence-review/v3/three-lenses.png" width={1774} height={887} alt="Editorial illustration of one document viewed through three optical lenses." fetchPriority="high" />
        <figcaption>One source of evidence, three perspectives. AI-generated editorial illustration, not experimental data.</figcaption>
      </figure>
      <div className={styles.layout}>
        <ArticleIndex entries={entries} />
        <article className={styles.article}>
          {reviewSections.map(section => <section id={section.id} key={section.id} className={section.id === "findings-at-a-glance" ? styles.takeaways : styles.section}>
            <h2>{section.title}</h2>{section.id === "findings-at-a-glance" ? <ol className={styles.findingList}>
              {findingSummaries.map((finding, i) => <li key={finding.id}>
                <span className={styles.findingNumber} aria-hidden="true">0{i + 1}</span>
                <div><h3><a href={`#${finding.id}`}>{finding.title}<span aria-hidden="true"> ↗</span></a></h3><p>{finding.summary}</p></div>
              </li>)}
            </ol> : <IllustratedText body={section.body} />}
            {section.id === "approval-overview" && <><ApprovalOverview /><IllustratedText body={approvalOverviewTakeaway} /></>}
          </section>)}
          <section id="appendix" className={styles.appendix}>
            <p className={styles.eyebrow}>Methods and supporting material</p>
            <h2>Appendix</h2>
            <p className={styles.appendixIntro}>Supporting evidence for the article: how the comparisons were made, the complete results, and the actual inputs behind the examples. Use the article index to jump to a section. Long tables and technical records open on demand.</p>
            {appendixSections.map(section => <section id={section.id} key={section.id} className={styles.appendixSection}>
              <h3>{section.title}</h3>
              {section.id === "appendix-f" && <ScenarioWalkthrough />}
              <IllustratedText body={section.body} />
              {section.id === "full-tables" && resultTableSections.map(table => <details key={table.id} id={table.id} className={styles.resultsDetails}>
                <summary>{table.title}</summary>
                <p className={styles.tableHint}>Scroll horizontally to see all metrics. These descriptive rates use all usable reviews, not a shared matched sample.</p>
                <IllustratedText body={table.body} />
              </details>)}
              {technicalAppendix.filter(detail => detail.id === section.id).map(detail => <details key={detail.id} className={styles.technicalDetails}>
                <summary>{technicalLabels[detail.id]}</summary>
                <IllustratedText body={detail.body} />
              </details>)}
            </section>)}
          </section>
        </article>
      </div>
    </main>
    <footer className={styles.footer}><span>{review ? "Local review draft · Not published" : "Independent research by Mudit Gurnani"}</span>{review ? <Link href="/simple/how-ai-reviewers-use-test-evidence">Previous draft</Link> : <a href={publication.repository} target="_blank" rel="noreferrer">GitHub ↗</a>}<a href="#introduction">Back to introduction ↑</a></footer>
  </div>;
}

export default function EvidenceReviewV3() { return <EvidenceReviewArticle />; }
