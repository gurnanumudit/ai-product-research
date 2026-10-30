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
    summary: "A higher score is not always a reason to switch. We simulated how related questions, repeated checks and missing results affect decisions, including useful improvements left unconfirmed.",
  };
  const partOne = {
    path: "/research/which-financial-ai-answers-should-we-review",
    title: "Which financial AI answers should we review? Part 1",
    image: "/research-assets/financial-answer-review/cover-v3.png",
    alt: "A small selection of paper tiles placed in a review tray.",
    category: "AI evaluation",
    summary: "We compared AI confidence with rule-based verification on financial answers. Verification found more answer-key mismatches at each review budget we tested, but neither approach caught everything.",
  };
  const partTwo = {
    path: "/research/which-financial-ai-answers-should-we-review-part-2",
    title: "Which financial AI answers should we review? Part 2",
    image: "/research-assets/financial-answer-review-part-2/cover-v1.png",
    alt: "Two review trays select different answers from the same batch.",
    category: "AI evaluation",
    summary: "We extended the study to four AI configurations and two financial datasets. Confidence led for some setups, verification for another, and neither was best everywhere.",
  };
  const latest = {
    path: "/research/how-ai-negotiates",
    title: "How AI negotiates",
    image: "/research-assets/negotiation/negotiation-hero-v1.png",
    alt: "A buyer and seller consider a contract across a table.",
    category: "Agents & decision-making",
    summary: "We tested different buyer instructions in 2,160 synthetic negotiations. Instruction effects were modest, and a buyer lead remained worth testing again.",
  };
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}>
      <a href="/" className={styles.name}>{publication.name}</a>
      <nav aria-label="Main navigation"><a href="#about">About</a><a href={publication.linkedin} target="_blank" rel="noreferrer">LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">GitHub ↗</a></nav>
    </header>
    <main id="research">
      <section className={`${styles.intro} ${styles.headlineIntro}`} aria-labelledby="research-title">
        <h1 id="research-title">Understanding AI through evidence.</h1>
        <div><p className={styles.note}>I use experiments and data to understand how AI behaves, where it succeeds or fails, and what that means for the decisions we make.</p>
        <p className={styles.focus}>Current work explores AI evaluation and economics.</p></div>
      </section>
      <section className={styles.publications} aria-labelledby="publications-title">
        <h2 id="publications-title">Latest research</h2>
        <article className={styles.feature}>
          <a href={latest.path} className={styles.image} aria-label={`Read ${latest.title}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={latest.image} alt={latest.alt} width={1774} height={887} fetchPriority="high" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>{latest.category} <span>·</span> <time dateTime="2026-10-29">October 29, 2026</time></p>
            <h3><a href={latest.path}>{latest.title}</a></h3>
            <p>{latest.summary}</p>
            <p className={styles.methods}>Negotiation experiment · Exploratory analysis</p>
            <a href={latest.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>
      <section className={styles.earlier} aria-labelledby="earlier-title">
        <h2 id="earlier-title">Earlier research</h2>
        <article className={styles.previous}>
          <a href={partTwo.path} className={styles.thumbnail} aria-label={`Read ${partTwo.title}`}><img src={partTwo.image} alt={partTwo.alt} width={1774} height={887} loading="lazy" /></a>
          <div className={styles.copy}>
            <p className={styles.meta}>{partTwo.category} <span>·</span> <time dateTime="2026-10-21">October 21, 2026</time></p>
            <h3><a href={partTwo.path}>{partTwo.title}</a></h3><p>{partTwo.summary}</p>
            <p className={styles.methods}>Review-policy evaluation · Error analysis</p>
            <a href={partTwo.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
        <article className={styles.previous}>
          <a href={partOne.path} className={styles.thumbnail} aria-label={`Read ${partOne.title}`}><img src={partOne.image} alt={partOne.alt} width={1774} height={887} loading="lazy" /></a>
          <div className={styles.copy}>
            <p className={styles.meta}>{partOne.category} <span>·</span> <time dateTime="2026-10-10">October 10, 2026</time></p>
            <h3><a href={partOne.path}>{partOne.title}</a></h3><p>{partOne.summary}</p>
            <p className={styles.methods}>Review-policy evaluation · Error analysis</p>
            <a href={partOne.path} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
        <article className={styles.previous}>
          <a href={reliability.path} className={styles.thumbnail} aria-label={`Read ${reliability.title}`}>
            <img src={reliability.image} alt={reliability.alt} width={1774} height={887} loading="lazy" />
          </a>
          <div className={styles.copy}>
            <p className={styles.meta}>{reliability.category} <span>·</span> <time dateTime="2026-09-30">September 30, 2026</time></p>
            <h3><a href={reliability.path}>{reliability.title}</a></h3>
            <p>{reliability.summary}</p>
            <p className={styles.methods}>Simulation · Statistical decision-making</p>
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
            <p className={styles.methods}>Model comparison · Cost–quality analysis</p>
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
            <p className={styles.methods}>Controlled experiments · Reviewer behavior</p>
            <a href={publication.articlePath} className={styles.read}>Read the study <span aria-hidden="true">→</span></a>
          </div>
        </article>
      </section>
      <section id="about" className={styles.about} aria-labelledby="about-title">
        <h2 id="about-title">About this research</h2>
        <div><p>I’m Mudit Gurnani. My background is in finance and data science, and I’m interested in the decisions we make as AI becomes part of our work.</p>
        <p>This is where I explore those questions through experiments, data analysis and research. Each study explains what we tested, what we found, and what the evidence cannot tell us—with links to the methods and code.</p>
        <p className={styles.aboutLinks}><a href={publication.linkedin} target="_blank" rel="noreferrer">Connect on LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">Explore the research code ↗</a></p></div>
      </section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href={publication.repository} target="_blank" rel="noreferrer">Research repository ↗</a></footer>
  </div>;
}
