import { ExhibitEnhancements } from "@/components/article/exhibit-enhancements";
import { ArticleNavigation } from "@/components/article/article-navigation";
import { ArticleIndex } from '@/components/article/article-index';
import { partOneUrl, sections } from '@/content/financial-answer-review-part-2';
import base from '@/components/article/page.module.css';
import prose from '@/components/financial-answer-review/page.module.css';
import styles from './page.module.css';

const entries = sections.map(({id,title})=>({id,title}));
export function PartTwo({draft = false}: {draft?: boolean}) {
  return <div data-research-article="" className={base.page}>
    <ArticleNavigation /><ExhibitEnhancements />
    <a href="#why" className={base.skip}>Skip to article</a>
    <header data-article-header=""><a href="/">Mudit Gurnani / Research</a><a href="/#research">All research ↗</a></header>
    <main>
      <header data-article-hero="" className={base.hero}>
        <p data-article-eyebrow="" className={base.eyebrow}>AI evaluation · Financial answers · Part 2</p>
        <figure data-article-cover="" className={`${base.cover} ${styles.cover}`}>
        <img src="/research-assets/financial-answer-review-part-2/cover-v1.png" width="1774" height="887" alt="Terracotta and teal trays select different paper cards from the same field of answers, a companion illustration to Part 1." />
        <figcaption>Same answers, different ways to choose what deserves a closer look. AI-generated illustration.</figcaption>
      </figure>
        <h1>Which financial AI answers<br/> should we review?<br/><span className={styles.part}>Part 2</span></h1>
        <p data-article-dek="" className={base.subtitle}>A follow-up study comparing confidence-based and rule-based review across four AI configurations and two financial datasets.</p>
        <p data-article-byline="" className={base.byline}>Mudit Gurnani <span>·</span> {draft ? 'Draft for review' : <time dateTime="2026-10-21">October 21, 2026</time>}</p>
        <p data-article-resources="" className={base.resourceLine}><a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/financial-answer-review-part-2" target="_blank" rel="noreferrer">Research code ↗</a><span> · </span><a href={partOneUrl}>Read Part 1 ↗</a><span> · </span><a href="#appendix">Data and methods ↓</a><span> · </span><a href="/research-assets/financial-answer-review-part-2/reproduction.zip" download>Code and data ↓</a></p>
      </header>

      <div data-article-layout="" className={base.layout}><ArticleIndex entries={entries}/><article data-article-body="" className={`${base.article} ${prose.body} ${styles.body}`}>{sections.map(s=><section key={s.id} id={s.id} className={base.section} dangerouslySetInnerHTML={{__html:s.html}}/>)}</article></div>
    </main>
    <footer data-article-footer="" className={base.footer}><span>Independent research by Mudit Gurnani</span><a href={partOneUrl}>Read Part 1 ↗</a><a href="#why">Back to introduction ↑</a></footer>
  </div>;
}
