import { ExhibitEnhancements } from "@/components/article/exhibit-enhancements";
import { ArticleNavigation } from "@/components/article/article-navigation";
import { ArticleIndex } from "@/components/article/article-index";
import { financialAnswerReviewSections as sections, financialAnswerReviewCode as codeUrl } from "@/content/financial-answer-review-draft";
import base from "@/components/article/page.module.css";
import styles from "./page.module.css";

const entries = sections.map(({id,title}) => ({id,title}));
export function FinancialAnswerReviewArticle() {
  return <div data-research-article="" className={base.page}>
    <ArticleNavigation /><ExhibitEnhancements />
    <a className={base.skip} href="#why">Skip to article</a>
    <header data-article-header=""><a href="/">Mudit Gurnani / Research</a><a href="/#research">All research ↗</a></header>
    <main>
      <header data-article-hero="" className={base.hero}>
        <p data-article-eyebrow="" className={base.eyebrow}>AI evaluation · Financial answers · Part 1</p>
        <figure data-article-cover="" className={base.cover}><img src="/research-assets/financial-answer-review/cover-v3.png" width="1774" height="887" alt="Folded paper tiles with a small selection placed in a separate tray." fetchPriority="high" /><figcaption>Choosing a few answers from many. AI-generated illustration; quantities shown are not study data.</figcaption></figure>
        <h1>Which financial AI answers<br className={styles.titleBreak} /> should we review?<br/><span className={styles.part}>Part 1</span></h1>
        <p data-article-dek="" className={base.subtitle}>Verification selected more answer-key mismatches than AI confidence on these financial questions. The lesson: a useful warning should reflect what we want reviewers to catch.</p>
        <p data-article-byline="" className={base.byline}>Mudit Gurnani <span>·</span> <time dateTime="2026-10-10">October 10, 2026</time><span>·</span>Updated <time dateTime="2026-10-21">October 21, 2026</time></p>
        <p data-article-resources="" className={base.resourceLine}><a href={codeUrl} target="_blank" rel="noreferrer">Research code ↗</a><span> · </span><a href="#appendix">Data and methods ↓</a><span> · </span><a href="/research/which-financial-ai-answers-should-we-review-part-2">Read Part 2 ↗</a></p>
      </header>

      <div data-article-layout="" className={base.layout}><ArticleIndex entries={entries} /><article data-article-body="" className={`${base.article} ${styles.body}`}>
        {sections.map(section => <section key={section.id} id={section.id} className={base.section} dangerouslySetInnerHTML={{__html: section.html}} />)}
      </article></div>
    </main>
    <footer data-article-footer="" className={base.footer}><span>Independent research by Mudit Gurnani</span><a href="#method-limits">Code and reproducibility ↓</a><a href="#why">Back to introduction ↑</a></footer>
  </div>;
}
