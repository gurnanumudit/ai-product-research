import type { Metadata } from "next";
import { MarkdownContent } from "@/components/markdown-content";
import { reviewSections, conciseAppendixSections as appendixSections, technicalAppendix, resultTableSections, findingSummaries, approvalOverviewTakeaway } from "@/content/evidence-review-v3";
import { ArticleIndex } from "./article-index";
import { ApprovalOverview, ScenarioWalkthrough } from "./evidence-exhibits";
import { EvidenceFigure } from "./evidence-figures";
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
    if (image[2].includes("/evidence-review/v2/finding-")) return <EvidenceFigure key={index} src={image[2]} />;
    return <figure key={index} className={styles.chart}>
      <a href={image[2]} target="_blank" rel="noreferrer" aria-label={`Open chart at full size: ${image[1]}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={image[2]} alt={image[1]} loading="lazy" />
      </a><figcaption>Open chart at full size ↗</figcaption>
    </figure>;
  })}</>;
}

const entries = [
  { id: "introduction", title: "Why this research?" },
  { id: "experiment-setup", title: "How we tested AI reviewers" },
  { id: "findings-at-a-glance", title: "Three findings at a glance" },
  { id: "finding-1", title: "1. What test evidence changed" },
  { id: "finding-2", title: "2. Same evidence, different decisions" },
  { id: "finding-3", title: "3. The independence label" },
  { id: "application", title: "How to use these findings" },
  { id: "limitations", title: "What this study does—and doesn’t—tell us" },
  { id: "conclusion", title: "The bottom line" },
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
  { id: "references", title: "References" },
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
      <a href="/" className={styles.wordmark}>Mudit Gurnani</a>
      <nav aria-label="Site navigation"><a href="/">Research</a><a href="#appendix">Methods & results</a></nav>
    </header>
    <main>
      <header className={styles.hero}>
        <p className={styles.eyebrow}>{review ? "Research · Review version 3" : "Research · AI evaluation"}</p>
        <h1>How AI reviewers<br />use test evidence</h1>
        <p className={styles.subtitle}>We gave three AI reviewers the same proposed fixes. What changed when we supplied test results, more detail, or a different source label?</p>
        <p className={styles.byline}>Mudit Gurnani <span>·</span> <time dateTime="2026-09-13">September 13, 2026</time><br />Updated September 24, 2026 · Presentation and explanation; results unchanged</p>
        <p className={styles.resourceLine}><a href={publication.articleCodeUrl ?? publication.repository} target="_blank" rel="noreferrer">{publication.articleCodeUrl ? "Study code and data" : "Research repository"} ↗</a>{!publication.articleCodeUrl && <span> · Study-specific code and data release pending</span>}</p>
      </header>
      <figure className={styles.cover}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/research-assets/evidence-review/v3/three-lenses.webp" width={1774} height={887} alt="Editorial illustration of one document viewed through three optical lenses." fetchPriority="high" />
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
          </section>)}
          <section id="appendix" className={styles.appendix}>
            <p className={styles.eyebrow}>Methods and supporting material</p>
            <h2>Appendix</h2>
            <p className={styles.appendixIntro}>Supporting evidence for the article: how the comparisons were made, the complete results, and the actual inputs behind the examples. Use the article index to jump to a section. Long tables and technical records open on demand.</p>
            {appendixSections.map(section => <section id={section.id} key={section.id} className={styles.appendixSection}>
              <h3>{section.title}</h3>
              {section.id === "full-tables" && <div id="approval-overview"><h4>Approval across the five scenarios</h4><ApprovalOverview /><IllustratedText body={approvalOverviewTakeaway} /></div>}
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
              <p className={styles.appendixReturn}><a href={section.id === "appendix-g" ? "#limitations" : section.id === "appendix-b" || section.id === "appendix-a" ? "#experiment-setup" : "#findings-at-a-glance"}>Back to the main article ↑</a></p>
            </section>)}
          </section>
          <section id="references" className={styles.references}>
            <h2>References</h2>
            <ol>
              <li><a href="https://aclanthology.org/2026.findings-eacl.70/">Don’t Judge Code by Its Cover: Exploring Biases in LLM Judges for Code Evaluation</a>. Moon and colleagues, EACL Findings, 2026.</li>
              <li><a href="https://arxiv.org/html/2608.18091">Self- and Other-Labels Induce Bidirectional Bias in LLM Judges</a>. arXiv:2608.18091, 2026.</li>
              <li><a href="https://arxiv.org/abs/2503.15223">Are “Solved Issues” in SWE-bench Really Solved Correctly? An Empirical Study</a>. arXiv:2503.15223, 2025.</li>
              <li><a href="https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/">Why SWE-bench Verified no longer measures frontier coding capabilities</a>. OpenAI, 2026.</li>
            </ol>
          </section>
        </article>
      </div>
    </main>
    <footer className={styles.footer}><span>{review ? "Local review draft · Not published" : "Independent research by Mudit Gurnani"}</span><a href={publication.repository} target="_blank" rel="noreferrer">GitHub ↗</a><a href="#introduction">Back to introduction ↑</a></footer>
  </div>;
}

export default function EvidenceReviewV3() { return <EvidenceReviewArticle />; }
