import { publication } from "@/content/publication";
import { localReview } from "@/lib/research-release";
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
  const negotiation = {
    path: "/research/how-ai-negotiates",
    title: "How AI negotiates",
    image: "/research-assets/negotiation/negotiation-hero-v1.png",
    alt: "A buyer and seller consider a contract across a table.",
    category: "Agents & decision-making",
    summary: "We tested different buyer instructions in 2,160 synthetic negotiations. Instruction effects were modest, and a buyer lead remained worth testing again.",
  };

  const toolError = {
    path: "/research/when-a-test-report-is-wrong",
    title: "When a test report is wrong, is a warning enough?",
    image: "/research-assets/tool-error/cover.png",
    alt: "A passed report is checked again, revealing a failure.",
    category: "Agents & reliability",
    summary: "An AI can only act on the evidence it receives. Across 240 coding tasks, we compared a warning with an automatic fresh check when test reports were unreliable.",
  };
  const latest = localReview ? toolError : negotiation;
  const selected = [
    { ...negotiation, date: "October 29, 2026", iso: "2026-10-29", method: "Negotiation experiment", question: "How do AI agents make decisions?" },
    { ...reliability, date: "September 30, 2026", iso: "2026-09-30", method: "Simulation", question: "When should we trust an evaluation?" },
  ];
  const collection = [
    ...(localReview ? [{ ...toolError, date: "Preview", iso: "", method: "Controlled experiment", draft: true }] : []),
    { ...negotiation, date: "Oct 29, 2026", iso: "2026-10-29", method: "Negotiation experiment", draft: false },
    { ...partTwo, date: "Oct 21, 2026", iso: "2026-10-21", method: "Review-policy evaluation", draft: false },
    { ...partOne, date: "Oct 10, 2026", iso: "2026-10-10", method: "Review-policy evaluation", draft: false },
    { ...reliability, date: "Sep 30, 2026", iso: "2026-09-30", method: "Simulation", draft: false },
    { ...reasoning, date: "Sep 24, 2026", iso: "2026-09-24", method: "Cost–quality analysis", draft: false },
    { path: publication.articlePath, title: publication.articleTitle, category: "AI evaluation", date: "Sep 13, 2026", iso: "2026-09-13", method: "Reviewer behavior", draft: false },
  ];
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}>
      <a href="/" className={styles.name}>{publication.name}</a>
      <nav aria-label="Main navigation"><a href="#all-research">Research</a><a href="#about">About</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></nav>
    </header>
    {localReview && <div className={styles.previewNotice}>Homepage draft <span>Includes the next article for preview. The live site is unchanged.</span></div>}
    <main id="research">
      <section className={styles.intro} aria-labelledby="research-title">
        <p className={styles.eyebrow}>Independent research by Mudit Gurnani</p>
        <h1 id="research-title">Understanding AI through evidence.</h1>
        <p className={styles.description}>I use experiments, simulations and data analysis to understand how AI behaves, where it succeeds or fails, and what that means for the decisions we make.</p>
        <p className={styles.focus}>AI evaluation · Agent behavior · Economic tradeoffs</p>
      </section>
      <section className={styles.publications} aria-labelledby="latest-title">
        <div className={styles.sectionHeading}><h2 id="latest-title">Latest research</h2><a href="#all-research">View all research ↓</a></div>
        <article className={styles.feature}>
          <a href={latest.path} className={styles.image} aria-label={`Read ${latest.title}`}><img src={latest.image} alt={latest.alt} width={1200} height={600} fetchPriority="high" /></a>
          <div className={styles.copy}>
            <p className={styles.meta}>{latest.category} · {localReview ? <span className={styles.draftLabel}>Article preview</span> : <time dateTime="2026-10-29">October 29, 2026</time>}</p>
            <h3><a href={latest.path}>{latest.title}</a></h3>
            <p>{latest.summary}</p>
            <p className={styles.methods}>{localReview ? "Controlled experiment · 720 outcomes" : "Negotiation experiment · Exploratory analysis"}</p>
            <a href={latest.path} className={styles.read}>{localReview ? "Read the draft" : "Read the study"} →</a>
          </div>
        </article>
      </section>
      <section className={styles.featured} aria-labelledby="featured-title">
        <div className={styles.sectionHeading}><div><h2 id="featured-title">Featured research</h2><p>Two places to start, beyond the latest article.</p></div></div>
        <div className={styles.featuredGrid}>{selected.map(item => <article className={styles.selectedCard} key={item.path}>
          <a href={item.path} className={styles.selectedImage} aria-label={`Read ${item.title}`}><img src={item.image} alt={item.alt} width={1200} height={600} loading="lazy" /></a>
          <div className={styles.copy}><p className={styles.cardQuestion}>{item.question}</p><h3><a href={item.path}>{item.title}</a></h3><p>{item.summary}</p><p className={styles.meta}>{item.method} · <time dateTime={item.iso}>{item.date}</time></p><a className={styles.read} href={item.path}>Read the study →</a></div>
        </article>)}</div>
      </section>
      <section id="all-research" className={styles.archive} aria-labelledby="all-title">
        <div className={styles.sectionHeading}><h2 id="all-title">All research</h2><span>{localReview ? "6 published · 1 preview" : "6 published articles"}</span></div>
        <div>{collection.map(item => <article key={item.path} className={styles.archiveRow}>
          <div className={styles.archiveDate}>{item.draft ? <span className={styles.draftLabel}>Preview</span> : <time dateTime={item.iso}>{item.date}</time>}</div>
          <div><h3><a href={item.path}>{item.title}<span aria-hidden="true"> ↗</span></a></h3><p>{item.category} · {item.method}</p></div>
        </article>)}</div>
      </section>
      <section id="about" className={styles.about} aria-labelledby="about-title">
        <h2 id="about-title">About this research</h2>
        <div><p>I’m Mudit Gurnani. My background is in finance and data science, and I’m interested in the decisions we make as AI becomes part of our work.</p>
        <p>I explore those questions through experiments, simulations and data analysis. Each article explains what we tested, what we found and what the evidence cannot tell us, with links to the methods and research code.</p>
        <p className={styles.aboutLinks}><a href={publication.linkedin} target="_blank" rel="noreferrer">Connect on LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></p></div>
      </section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></footer>
  </div>;
}
