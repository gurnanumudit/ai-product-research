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
      <section className={styles.intro} aria-labelledby="research-title">
        <p className={styles.eyebrow}>AI evaluation · Economics · Agent behavior</p>
        <h1 id="research-title">What is an AI system actually worth, and how do you know?</h1>
        <p className={styles.description}>I measure cost, success and decision quality, so a launch, review budget or model switch can be judged on evidence, not a headline score.</p>
        <p className={styles.purpose}>Independent experiments, simulations and data analysis by Mudit Gurnani.</p>
        <p className={styles.heroActions}><a href="#flagship">Start with the flagship research ↓</a><a href={publication.linkedin} target="_blank" rel="noreferrer">Discuss the research ↗</a></p>
      </section>
      <ResearchCatalog />
      <section id="about" className={styles.about} aria-labelledby="about-title"><div><p className={styles.eyebrow}>Behind the research</p><h2 id="about-title">From a result to a decision.</h2></div><div><p>I’m Mudit Gurnani. My background is in finance and data science. I’m interested in the decisions behind AI adoption: what an improvement buys, whether the evidence holds up and what we should do differently because of it.</p><p className={styles.positioning}>My focus is measuring what an AI system delivers per dollar, and whether the evidence is strong enough to support a launch, allocate a review budget or justify switching models.</p><p>Each study starts with a question, tests it with code and data, and explains both the findings and their limits. The interactive articles let you explore the results; the research code lets you inspect how they were produced.</p><p className={styles.aboutLinks}><a href={publication.linkedin} target="_blank" rel="noreferrer">Connect on LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></p></div></section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href="#research">Back to top ↑</a></footer>
  </div>;
}
