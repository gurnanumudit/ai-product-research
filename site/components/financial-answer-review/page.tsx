import { ArticleIndex } from "@/components/article/article-index";
import { financialAnswerReviewSections as sections, financialAnswerReviewCode as codeUrl } from "@/content/financial-answer-review-draft";
import base from "@/components/article/page.module.css";
import styles from "./page.module.css";

const entries = sections.map(({id,title}) => ({id,title}));
export function FinancialAnswerReviewArticle() {
  return <div className={base.page}>
    <a className={base.skip} href="#why">Skip to article</a>
    <header className={base.siteHeader}><a className={base.wordmark} href="/">Mudit Gurnani</a><nav aria-label="Site navigation"><a href="/">Research</a><a href="#appendix">Methods &amp; results</a></nav></header>
    <main>
      <header className={base.hero}>
        <p className={base.eyebrow}>AI evaluation · Financial answers · Part 1</p>
        <h1>Which financial AI answers<br className={styles.titleBreak} /> should we review?<br/><span className={styles.part}>Part 1</span></h1>
        <p className={base.subtitle}>Verification selected more answer-key mismatches than AI confidence on these financial questions. The lesson: a useful warning should reflect what we want reviewers to catch.</p>
        <p className={base.byline}>Mudit Gurnani <span>·</span> <time dateTime="2026-10-10">October 10, 2026</time><span>·</span>Updated <time dateTime="2026-10-21">October 21, 2026</time></p>
        <p className={base.resourceLine}><a href={codeUrl} target="_blank" rel="noreferrer">Research code ↗</a><span> · </span><a href="#appendix">Methods and results ↓</a><span> · </span><a href="/research/which-financial-ai-answers-should-we-review-part-2">Read Part 2 ↗</a></p>
      </header>
      <figure className={base.cover}><img src="/research-assets/financial-answer-review/cover-v3.png" width="1774" height="887" alt="Folded paper tiles with a small selection placed in a separate tray." fetchPriority="high" /><figcaption>Choosing a few answers from many. AI-generated illustration; quantities shown are not study data.</figcaption></figure>
      <div className={base.layout}><ArticleIndex entries={entries} /><article className={`${base.article} ${styles.body}`}>
        {sections.map(section => <section key={section.id} id={section.id} className={base.section} dangerouslySetInnerHTML={{__html: section.html}} />)}
      </article></div>
    </main>
    <footer className={base.footer}><span>Independent research by Mudit Gurnani</span><a href="#method-limits">Code and reproducibility ↓</a><a href="#why">Back to introduction ↑</a></footer>
    <script src="/research-assets/financial-answer-review/appendix-navigation.js" defer />
  </div>;
}
