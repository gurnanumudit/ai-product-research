import { ArticleIndex } from '@/components/article/article-index';
import { partOneUrl, sections } from '@/content/financial-answer-review-part-2';
import base from '@/components/article/page.module.css';
import prose from '@/components/financial-answer-review/page.module.css';
import styles from './page.module.css';

const entries = sections.map(({id,title})=>({id,title}));
export function PartTwo({draft = false}: {draft?: boolean}) {
  return <div className={base.page}>
    <a href="#why" className={base.skip}>Skip to article</a>
    <header className={base.siteHeader}><a className={base.wordmark} href="/">Mudit Gurnani</a><nav aria-label="Site navigation"><a href="/">Research</a><a href={partOneUrl}>Part 1 ↗</a></nav></header>
    <main>
      <header className={base.hero}>
        <p className={base.eyebrow}>AI evaluation · Financial answers · Part 2</p>
        <h1>Which financial AI answers<br/> should we review?<br/><span className={styles.part}>Part 2</span></h1>
        <p className={base.subtitle}>A follow-up study comparing confidence-based and rule-based review across four AI configurations and two financial datasets.</p>
        <p className={base.byline}>Mudit Gurnani <span>·</span> {draft ? 'Draft for review' : <time dateTime="2026-10-21">October 21, 2026</time>}</p>
        <p className={base.resourceLine}><a href={partOneUrl}>Read Part 1 ↗</a><span> · </span><a href="#appendix">Methods and study files ↓</a><span> · </span><a href="/research-assets/financial-answer-review-part-2/reproduction.zip" download>Code and data ↓</a></p>
      </header>
      <figure className={`${base.cover} ${styles.cover}`}>
        <img src="/research-assets/financial-answer-review-part-2/cover-v1.png" width="1774" height="887" alt="Terracotta and teal trays select different paper cards from the same field of answers, a companion illustration to Part 1." />
        <figcaption>Same answers, different ways to choose what deserves a closer look. AI-generated illustration.</figcaption>
      </figure>
      <div className={base.layout}><ArticleIndex entries={entries}/><article className={`${base.article} ${prose.body} ${styles.body}`}>{sections.map(s=><section key={s.id} id={s.id} className={base.section} dangerouslySetInnerHTML={{__html:s.html}}/>)}</article></div>
    </main>
    <footer className={base.footer}><span>Independent research by Mudit Gurnani</span><a href={partOneUrl}>Read Part 1 ↗</a><a href="#why">Back to introduction ↑</a></footer>
    <script src="/research-assets/financial-answer-review/appendix-navigation.js" defer/>
  </div>;
}
