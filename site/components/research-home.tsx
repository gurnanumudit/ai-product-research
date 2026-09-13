import { publication } from "@/content/publication";
import styles from "./research-home.module.css";

export function ResearchHome() {
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}>
      <a href="/" className={styles.name}>{publication.name}</a>
      <nav aria-label="Main navigation"><a href={publication.linkedin} target="_blank" rel="noreferrer">LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">GitHub ↗</a></nav>
    </header>
    <main id="research">
      <section className={styles.intro} aria-labelledby="research-title">
        <h1 id="research-title">Research</h1>
        <div><p>I’m Mudit. I explore how AI works, where it falls short, and what makes it useful in everyday work.</p>
        <p className={styles.note}>Here I share experiments, findings, and the evidence behind them.</p></div>
      </section>
      <section className={styles.publications} aria-labelledby="publications-title">
        <h2 id="publications-title">Latest research</h2>
        <article className={styles.feature}>
          <a href={publication.articlePath} className={styles.image} aria-label={`Read ${publication.articleTitle}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/research-assets/evidence-review/v3/three-lenses.png" alt="One document seen through three lenses." width={1774} height={887} />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>AI evaluation <span>·</span> <time dateTime="2026-09-13">September 13, 2026</time></p>
            <h3><a href={publication.articlePath}>{publication.articleTitle}</a></h3>
            <p>We gave three AI reviewers the same software fixes under five evidence scenarios. Test reports reduced faulty approvals on matched tasks, but reviewers still differed in which passing fixes they accepted.</p>
            <a href={publication.articlePath} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href={publication.repository} target="_blank" rel="noreferrer">Research repository ↗</a></footer>
  </div>;
}
