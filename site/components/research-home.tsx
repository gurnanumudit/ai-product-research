import { publication } from "@/content/publication";
import styles from "./research-home.module.css";

export function ResearchHome() {
  const reasoning = {
    path: "/research/when-is-more-reasoning-worth-it",
    title: "When is more reasoning worth it?",
    image: "/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp",
    alt: "A reasoning dial connects spreadsheets, analytical paths and cost.",
    category: "AI economics",
    summary: "We tested three models at three reasoning settings on analytical work. Some reasoning helped; paying for more did not always buy a better answer.",
  };
  const reliability = {
    path: "/research/how-to-avoid-false-confidence-in-ai-evaluations",
    title: "How to avoid false confidence in AI evaluations",
    image: "/research-assets/evaluation-reliability/evaluation-confidence-cover.png",
    alt: "A magnifying glass reveals gaps in evaluation evidence.",
    category: "AI evaluation",
    summary: "A higher score is not always a reason to switch. We simulated how related questions, repeated checks and missing results affect the decision—and when safeguards leave us waiting.",
  };
  const latest = {
    path: "/research/which-financial-ai-answers-should-we-review",
    title: "Which financial AI answers should we review?",
    image: "/research-assets/financial-answer-review/cover-v3.png",
    alt: "A small selection of paper tiles placed in a review tray.",
    category: "AI evaluation",
    summary: "We compared AI confidence with rule-based verification on financial answers. Confidence found more answer-key mismatches at smaller review budgets—but neither approach caught everything.",
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
            <p className={styles.meta}>{latest.category} <span>·</span> <time dateTime="2026-10-10">October 10, 2026</time></p>
            <h3><a href={latest.path}>{latest.title}</a></h3>
            <p>{latest.summary}</p>
            <a href={latest.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>
      <section className={styles.earlier} aria-labelledby="earlier-title">
        <h2 id="earlier-title">Earlier research</h2>
        <article className={styles.previous}>
          <a href={reliability.path} className={styles.thumbnail} aria-label={`Read ${reliability.title}`}>
            <img src={reliability.image} alt={reliability.alt} width={1774} height={887} loading="lazy" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>{reliability.category} <span>·</span> <time dateTime="2026-09-30">September 30, 2026</time></p>
            <h3><a href={reliability.path}>{reliability.title}</a></h3>
            <p>{reliability.summary}</p>
            <a href={reliability.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
        <article className={styles.previous}>
          <a href={reasoning.path} className={styles.thumbnail} aria-label={`Read ${reasoning.title}`}>
            <img src={reasoning.image} alt={reasoning.alt} width={1774} height={887} loading="lazy" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>{reasoning.category} <span>·</span> <time dateTime="2026-09-24">September 24, 2026</time></p>
            <h3><a href={reasoning.path}>{reasoning.title}</a></h3>
            <p>{reasoning.summary}</p>
            <a href={reasoning.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
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
      </section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href={publication.repository} target="_blank" rel="noreferrer">Research repository ↗</a></footer>
  </div>;
}
