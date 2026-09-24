import { publication } from "@/content/publication";
import { showReasoningArticle, reasoningPublished } from "@/lib/research-release";
import styles from "./research-home.module.css";

export function ResearchHome() {
  const showDraft = showReasoningArticle;
  const latest = showDraft ? {
    path: "/research/when-is-more-reasoning-worth-it",
    title: "When is more reasoning worth it?",
    image: "/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp",
    alt: "A reasoning dial connects spreadsheets, analytical paths and cost.",
    category: "AI economics",
    summary: "We tested three models at three reasoning settings on analytical work. Some reasoning helped; paying for more did not always buy a better answer.",
  } : {
    path: publication.articlePath, title: publication.articleTitle,
    image: "/research-assets/evidence-review/v3/three-lenses.webp",
    alt: "One document seen through three lenses.", category: "AI evaluation",
    summary: "We gave three AI reviewers the same software fixes under five evidence scenarios. Test reports reduced faulty approvals on matched tasks, but reviewers still differed in which passing fixes they accepted.",
  };
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}>
      <a href="/" className={styles.name}>{publication.name}</a>
      <nav aria-label="Main navigation"><a href={publication.linkedin} target="_blank" rel="noreferrer">LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">GitHub ↗</a></nav>
    </header>
    <main id="research">
      <section className={styles.intro} aria-labelledby="research-title">
        <h1 id="research-title">Research</h1>
        <div><p>How AI works, where it falls short, and when it’s worth the cost.</p>
        <p className={styles.note}>Independent experiments by Mudit Gurnani, with the evidence and code behind the findings.</p></div>
      </section>
      <section className={styles.publications} aria-labelledby="publications-title">
        <h2 id="publications-title">Latest research</h2>
        <article className={styles.feature}>
          <a href={latest.path} className={styles.image} aria-label={`Read ${latest.title}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={latest.image} alt={latest.alt} width={1774} height={887} fetchPriority="high" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>{latest.category} <span>·</span> {showDraft ? (reasoningPublished ? <time dateTime="2026-09-24">September 24, 2026</time> : "Review draft") : <time dateTime="2026-09-13">September 13, 2026</time>}</p>
            <h3><a href={latest.path}>{latest.title}</a></h3>
            <p>{latest.summary}</p>
            <a href={latest.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>
      {showDraft && <section className={styles.earlier} aria-labelledby="earlier-title">
        <h2 id="earlier-title">Earlier research</h2>
        <article className={styles.previous}>
          <a href={publication.articlePath} className={styles.thumbnail} aria-label={`Read ${publication.articleTitle}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/research-assets/evidence-review/v3/three-lenses.webp" alt="One document seen through three lenses." width={1774} height={887} loading="lazy" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>AI evaluation <span>·</span> <time dateTime="2026-09-13">September 13, 2026</time></p>
            <h3><a href={publication.articlePath}>{publication.articleTitle}</a></h3>
            <p>Test reports reduced faulty approvals, but reviewers still differed in which passing fixes they accepted.</p>
            <a href={publication.articlePath} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>}
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href={publication.repository} target="_blank" rel="noreferrer">Research repository ↗</a></footer>
  </div>;
}
