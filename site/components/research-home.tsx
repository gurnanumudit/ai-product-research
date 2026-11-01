import { publication } from "@/content/publication";
import { localReview } from "@/lib/research-release";
import styles from "./research-home.module.css";

const paths = {
  reasoning: "/research/when-is-more-reasoning-worth-it",
  finance: "/research/which-financial-ai-answers-should-we-review",
  financeTwo: "/research/which-financial-ai-answers-should-we-review-part-2",
  reliability: "/research/how-to-avoid-false-confidence-in-ai-evaluations",
  negotiation: "/research/how-ai-negotiates",
  toolError: "/research/when-a-test-report-is-wrong",
};
const published = [
  { path: paths.negotiation, title: "How AI negotiates", date: "Oct 29, 2026", iso: "2026-10-29" },
  { path: paths.financeTwo, title: "Which financial AI answers should we review? Part 2", date: "Oct 21, 2026", iso: "2026-10-21" },
  { path: paths.finance, title: "Which financial AI answers should we review? Part 1", date: "Oct 10, 2026", iso: "2026-10-10" },
  { path: paths.reliability, title: "How to avoid false confidence in AI evaluations", date: "Sep 30, 2026", iso: "2026-09-30" },
  { path: paths.reasoning, title: "When is more reasoning worth it?", date: "Sep 24, 2026", iso: "2026-09-24" },
  { path: publication.articlePath, title: publication.articleTitle, date: "Sep 13, 2026", iso: "2026-09-13" },
];

export function ResearchHome() {
  // Recency only controls the small latest strip, never flagship selection.
  const latest = published[0];
  const age = Date.now() - Date.parse(latest.iso + "T00:00:00Z");
  const showLatest = age >= 0 && age < 30 * 24 * 60 * 60 * 1000;
  return <div className={styles.page}>
    <a className={styles.skip} href="#research">Skip to research</a>
    <header className={styles.header}>
      <a href="/" className={styles.name}>{publication.name}<span>Independent research</span></a>
      <nav aria-label="Main navigation"><a href="#cost-quality">Research</a><a href="#about">About</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></nav>
    </header>
    {localReview && <div className={styles.previewNotice}>Homepage draft <span>Proposed direction and upcoming work. The live site is unchanged.</span></div>}
    <main id="research">
      <section className={styles.intro} aria-labelledby="research-title">
        <p className={styles.eyebrow}>AI value, measured</p>
        <h1 id="research-title">What is an AI system actually worth, and how do you know?</h1>
        <p className={styles.description}>I measure cost, success, and decision quality — so a launch, a review budget, or a model switch can be judged on evidence, not a headline score.</p>
        <p className={styles.methods}>Experiments · Simulations · Data analysis</p>
      </section>
      {showLatest && <aside className={styles.latest} aria-label="Latest published research"><span className={styles.new}>New</span><span className={styles.latestLabel}>Latest research</span><a href={latest.path}>{latest.title} <span aria-hidden="true">↗</span></a><time dateTime={latest.iso}>October 29, 2026</time></aside>}
      <nav className={styles.trackNav} aria-label="Research tracks">
        <a href="#cost-quality"><span>01 · Cost and quality</span><strong>What should we pay for? <b aria-hidden="true">↓</b></strong></a>
        <a href="#trust-review"><span>02 · Trust and review</span><strong>What can we rely on? <b aria-hidden="true">↓</b></strong></a>
        <a href="#agent-decisions"><span>03 · Agent decisions · Series</span><strong>Who captures the value? <b aria-hidden="true">↓</b></strong></a>
      </nav>
      <section id="cost-quality" className={styles.track} aria-labelledby="cost-title">
        <div className={styles.trackHeading}><div><p className={styles.eyebrow}>01 / Cost and quality</p><h2 id="cost-title">What do you actually get per dollar?</h2></div><p>Which model, reasoning setting or workflow is worth paying for? Start with what the extra spending buys.</p></div>
        <div className={styles.trackBody}>
          <article className={styles.flagship}>
            <a href={paths.reasoning} className={styles.cover} aria-label="Read When is more reasoning worth it?"><img src="/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp" width={1774} height={887} alt="A reasoning dial links analytical tasks and cost." loading="lazy" /></a>
            <div className={styles.flagshipCopy}><p className={styles.tag}>Flagship · Cost and quality</p><h3><a href={paths.reasoning}>When is more reasoning worth it?</a></h3><p className={styles.decision}>Choose a reasoning setting by what it buys in correct answers, not by how powerful it sounds.</p>
            <div className={styles.metric}><strong>+$0.06 <span>for +10 correct answers</span></strong><p>Per 100 easy questions, moving Luna from low to high reasoning. Rounded from 29 questions; model charges and reservations only, excluding runtime.</p></div>
            <a className={styles.read} href={paths.reasoning}>Explore the cost and quality tradeoffs →</a></div>
          </article>
          <aside className={styles.next} aria-labelledby="next-title"><p className={styles.tag}>Coming next · Not yet published</p><h3 id="next-title">Prompt vs harness</h3><p>Should you improve the instructions, or the workflow around the model?</p><p>Compare what each approach buys in successful answers and what it costs.</p><div className={styles.nextFoot}>The next study in this track.</div></aside>
        </div>
      </section>
      <section id="trust-review" className={styles.track} aria-labelledby="trust-title">
        <div className={styles.trackHeading}><div><p className={styles.eyebrow}>02 / Trust and review</p><h2 id="trust-title">How do you know the result is real?</h2></div><p>A good score is a starting point. What should you check, how much review is enough, and when is the evidence too weak to decide?</p></div>
        <div className={styles.trackBody}>
          <article className={styles.flagship}>
            <a href={paths.finance} className={styles.cover} aria-label="Read Which financial AI answers should we review? Part 1"><img src="/research-assets/financial-answer-review/cover-v3.png" width={1774} height={887} alt="A review tray holds a selection of answers from a larger batch." loading="lazy" /></a>
            <div className={styles.flagshipCopy}><p className={styles.tag}>Flagship · Two-part study</p><h3>Which financial AI answers should we review?</h3><p className={styles.decision}>Spend a limited review budget where it catches more mistakes. Retest the rule when the model changes.</p>
            <div className={styles.metric}><strong>143 <span>mismatches caught, versus 103</span></strong><p>Verification versus AI confidence, using 225 review slots in Part 1. Part 2 found that the better method depended on the model setup.</p></div>
            <div className={styles.partLinks}><a className={styles.read} href={paths.finance}>Part 1 · Choosing what to review →</a><a className={styles.read} href={paths.financeTwo}>Part 2 · Does the rule travel? →</a></div></div>
          </article>
          <div className={styles.supporting}>
            <article><p className={styles.tag}>Simulation</p><h3><a href={paths.reliability}>How to avoid false confidence in AI evaluations</a></h3><p>Before switching versions on a small lead, check how repeated comparisons and missing results could change the decision.</p><a className={styles.read} href={paths.reliability}>Read the study →</a></article>
            <article><p className={styles.tag}>Reviewer behavior</p><h3><a href={publication.articlePath}>How AI reviewers use test evidence</a></h3><p>Test whether giving a reviewer more evidence improves which fixes it accepts and rejects.</p><a className={styles.read} href={publication.articlePath}>Read the study →</a></article>
            {localReview && <article className={styles.draft}><p className={styles.tag}>Reviewed draft · Not yet published</p><h3><a href={paths.toolError}>When a test report is wrong, is a warning enough?</a></h3><p>Compare a warning with a fresh check when the evidence given to a coding agent is unreliable.</p><a className={styles.read} href={paths.toolError}>Preview the article →</a></article>}
          </div>
        </div>
      </section>
      <section id="agent-decisions" className={`${styles.track} ${styles.series}`} aria-labelledby="agent-title">
        <div className={styles.trackHeading}><div><p className={styles.eyebrow}>03 / Agent decisions · Negotiation series</p><h2 id="agent-title">Who captures the value?</h2></div><p>When AI agents negotiate, how much do instructions matter? And how much comes from their role or the rules of the exchange?</p></div>
        <div className={styles.seriesBody}>
          <a href={paths.negotiation} className={styles.seriesCover} aria-label="Read How AI negotiates"><img src="/research-assets/negotiation/negotiation-hero-v1.png" width={1200} height={600} alt="Buyer and seller consider a contract across a table." loading="lazy" /></a>
          <article><p className={styles.tag}>Part 1 · Published October 29, 2026</p><h3><a href={paths.negotiation}>How AI negotiates</a></h3><p>Across 2,160 synthetic negotiations, changes to buyer instructions had modest effects. A buyer lead left an open question: was it the role, or the setup?</p><a className={styles.read} href={paths.negotiation}>Read Part 1 →</a></article>
          <aside className={styles.seriesNext}><p className={styles.tag}>Part 2 · Forthcoming conclusion</p><h3>Does the advantage follow the role?</h3><p>The follow-up reverses starting order and swaps opportunities to test what produced the buyer lead.</p><p className={styles.seriesNote}>This two-part series will close after Part 2. Ongoing research will focus on cost and quality, and trust and review.</p></aside>
        </div>
      </section>
      <section id="all-research" className={styles.archive} aria-labelledby="all-title"><div className={styles.sectionHeading}><h2 id="all-title">All published research</h2><span>6 articles · Newest first</span></div>
        {published.map(item => <div key={item.path} className={styles.archiveRow}><a href={item.path}>{item.title} <span aria-hidden="true">↗</span></a><time dateTime={item.iso}>{item.date}</time></div>)}
      </section>
      <section id="about" className={styles.about} aria-labelledby="about-title"><h2 id="about-title">About this research</h2><div><p>I’m Mudit Gurnani. My background is in finance and data science. This site is my working answer to the question a Finance DS team asks on every model launch: did it actually deliver value, and how would we know?</p><p>I explore those questions through experiments, simulations and data analysis. Each article explains what we tested, what we found and what the evidence cannot tell us, with links to the methods and research code.</p><p>These studies measure parts of that decision, such as cost per correct answer and mistakes caught within a review budget. They do not yet measure the full impact of a product launch on revenue or adoption.</p><p className={styles.aboutLinks}><a href={publication.linkedin} target="_blank" rel="noreferrer">Connect on LinkedIn ↗</a><a href={publication.repository} target="_blank" rel="noreferrer">Research code ↗</a></p></div></section>
    </main>
    <footer className={styles.footer}><span>Independent research by {publication.name}</span><a href="#research">Back to top ↑</a></footer>
  </div>;
}
