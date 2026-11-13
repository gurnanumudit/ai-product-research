"use client";

import { useRef, useState } from "react";
import {
  latestStudy,
  publishedStudies,
  researchTracks,
  type ResearchTrack,
} from "@/content/research-catalog";
import styles from "./research-home.module.css";

const financialPartOne = "/research/which-financial-ai-answers-should-we-review";
const financialPartTwo = "/research/which-financial-ai-answers-should-we-review-part-2";

export function ResearchCatalog() {
  const [selected, setSelected] = useState<ResearchTrack | "all">("all");
  const results = useRef<HTMLElement>(null);
  const count = (track: ResearchTrack) => publishedStudies.filter((study) => study.track === track).length;
  const visible = publishedStudies
    .filter((study) => selected === "all" || study.track === selected)
    .sort((a, b) => b.iso.localeCompare(a.iso));

  function choose(track: ResearchTrack | "all") {
    setSelected(track);
    results.current?.scrollIntoView({ behavior: "instant", block: "start" });
  }

  return <>
    <section className={styles.tracks} aria-labelledby="tracks-title">
      <div className={styles.sectionHeading}>
        <h2 id="tracks-title">Three questions guide the work</h2>
        <span>Explore a track, or browse every study below.</span>
      </div>
      <div className={styles.trackGrid}>{researchTracks.map((track, index) => <button
        type="button"
        key={track.id}
        className={styles.trackCard}
        aria-pressed={selected === track.id}
        onClick={() => choose(track.id)}
      >
        <span className={styles.eyebrow}>0{index + 1} / {track.name}</span>
        <strong>{track.question}</strong>
        <span className={styles.trackDescription}>{track.description}</span>
        <span className={styles.trackLink}><span>{count(track.id)} {count(track.id) === 1 ? "article" : "articles"}</span><span>Explore track ↓</span></span>
      </button>)}</div>
    </section>

    <section id="flagship" className={styles.featured} aria-labelledby="flagship-title">
      <div className={styles.sectionHeading}>
        <div><h2 id="flagship-title">Flagship research</h2><p>Start with the result, then see whether it travelled.</p></div>
      </div>
      <div className={styles.featuredGrid}>
        <article className={`${styles.highlightCard} ${styles.flagshipCard}`}>
          <a href={financialPartOne} className={styles.highlightImage} aria-label="Read the financial review flagship">
            <img src="/research-assets/financial-answer-review/cover-v3.png" width={1200} height={600} alt="" loading="lazy" />
          </a>
          <div className={styles.highlightCopy}>
            <p className={styles.eyebrow}>Trust and review · Two-part study</p>
            <h3><a href={financialPartOne}>Which financial AI answers should we review?</a></h3>
            <p className={styles.decisionLine}>Test whether your checks catch the mistakes your AI makes.</p>
            <p className={styles.keyNumbers}><strong>Part 1:</strong> Checking calculations and cited figures helped select more wrong answers for review than relying on the AI’s confidence.<br /><br /><strong>Part 2:</strong> That advantage did not hold across models. Some wrong answers passed the checks without a warning.</p>
            <div className={styles.highlightLinks}><a href={financialPartOne}>Read Part 1 →</a><a href={financialPartTwo}>Read Part 2 →</a></div>
          </div>
        </article>

        <div className={styles.supportingResearch} aria-label="More selected research">
          <article className={styles.supportingCard}>
            <p className={styles.eyebrow}>Cost and quality</p>
            <h3><a href="/research/when-is-more-reasoning-worth-it">When is more reasoning worth it?</a></h3>
            <p>The observed accuracy and cost tradeoffs across the tested models and reasoning settings.</p>
            <a className={styles.textLink} href="/research/when-is-more-reasoning-worth-it">Read the study →</a>
          </article>
          <article className={styles.supportingCard}>
            <p className={styles.eyebrow}>Featured exploration · Agent decisions</p>
            <h3><a href="/research/how-ai-negotiates">How AI negotiates</a></h3>
            <p>A two-part exploration of how instructions, starting roles and economic opportunities shaped simulated negotiations.</p>
            <a className={styles.textLink} href="/research/how-ai-negotiates">Start with Part 1 →</a>
          </article>
        </div>
      </div>
    </section>

    <section className={styles.latestStrip} aria-labelledby="latest-title">
      <div><p className={styles.eyebrow}><span>New</span> · <time dateTime={latestStudy.iso}>{latestStudy.date}</time> · {researchTracks.find((track) => track.id === latestStudy.track)!.name}</p><h2 id="latest-title"><a href={latestStudy.path}>{latestStudy.title}</a></h2></div>
      <p>{latestStudy.summary}</p>
      <a className={styles.textLink} href={latestStudy.path}>Read the latest →</a>
    </section>

    <section ref={results} id="all-research" className={styles.research} aria-labelledby="all-title">
      <div className={styles.sectionHeading}><div><h2 id="all-title">The research</h2><p>Explore the studies, their methods, results and research code.</p></div></div>
      <div className={styles.filters} role="group" aria-label="Filter research by track">
        <button type="button" aria-pressed={selected === "all"} onClick={() => setSelected("all")}>All studies <span>{publishedStudies.length}</span></button>
        {researchTracks.map((track) => <button key={track.id} type="button" aria-pressed={selected === track.id} onClick={() => setSelected(track.id)}>{track.name} <span>{count(track.id)}</span></button>)}
      </div>
      <p className={styles.resultCount} role="status">{selected === "all" ? `All ${publishedStudies.length} published studies` : `${visible.length} ${visible.length === 1 ? "study" : "studies"} in ${researchTracks.find((track) => track.id === selected)!.name.toLowerCase()}`}</p>
      <div className={styles.studyGrid}>{visible.map((study) => <article className={styles.studyCard} id={study.id} key={study.id}>
        <a href={study.path} className={styles.cover} aria-label={`Read ${study.title}`}><img src={study.image} width={1200} height={600} alt="" loading="lazy" /></a>
        <div className={styles.studyCopy}><p className={styles.studyMeta}>{researchTracks.find((track) => track.id === study.track)!.name}<time dateTime={study.iso}>{study.date}</time></p><h3><a href={study.path}>{study.title}</a></h3><p className={styles.summary}>{study.summary}</p><div className={styles.studyFoot}><span>{study.method}</span><a href={study.path}>Read study <span aria-hidden="true">↗</span></a></div></div>
      </article>)}</div>
    </section>
  </>;
}
