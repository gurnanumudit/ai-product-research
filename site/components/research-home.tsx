import { publication } from "@/content/publication";
import { localReview } from "@/lib/research-release";
import { ResearchCatalog } from "./research-catalog";
import styles from "./research-home.module.css";

export function ResearchHome() {
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}><a href="/" className={styles.name}>{publication.name}<span>Independent research</span></a><nav aria-label="Main navigation"><a href="#all-research">Research</a><a href="#about">About</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></nav></header>
    {localReview && <div className={styles.previewNotice}>Homepage draft <span>The live site is unchanged.</span></div>}
    <main id="research">
      <section className={styles.intro} aria-labelledby="research-title"><p className={styles.eyebrow}>Experiments · Simulations · Data analysis</p><h1 id="research-title">Evidence for better decisions about AI.</h1><p className={styles.description}>I study what AI can do, what it costs and how it behaves. Through experiments, simulations and data analysis, I test where it succeeds, where it fails and what those results mean for how we use it.</p><p className={styles.purpose}>The goal: help people choose AI systems, decide which results to trust and understand the tradeoffs before putting them to work.</p></section>
      <ResearchCatalog />
      <section id="about" className={styles.about} aria-labelledby="about-title"><div><p className={styles.eyebrow}>Behind the research</p><h2 id="about-title">From a result to a decision.</h2></div><div><p>I’m Mudit Gurnani. My background is in finance and data science. I’m interested in the decisions behind AI adoption: what an improvement buys, whether the evidence holds up and what we should do differently because of it.</p><p>Each study starts with a question, tests it with code and data, and explains both the findings and their limits. The interactive articles let you explore the results; the research code lets you inspect how they were produced.</p><p className={styles.aboutLinks}><a href={publication.linkedin} target="_blank" rel="noreferrer">Connect on LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></p></div></section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href="#research">Back to top ↑</a></footer>
  </div>;
}
