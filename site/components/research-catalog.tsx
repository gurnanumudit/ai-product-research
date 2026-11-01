"use client";

import { useRef, useState } from "react";
import styles from "./research-home.module.css";

type Track = "cost" | "trust" | "agents";
const tracks: { id: Track; name: string; question: string; description: string }[] = [
  { id: "cost", name: "Cost and quality", question: "When is better AI worth the cost?", description: "Compare models and workflows by the quality they deliver and the resources they use." },
  { id: "trust", name: "Trust and review", question: "Which results can we rely on?", description: "Test how we evaluate AI, catch mistakes and decide when the evidence is strong enough." },
  { id: "agents", name: "Agent decisions", question: "What shapes an AI agent’s decisions?", description: "Study how instructions, roles and incentives affect behavior when AI agents interact." },
];
const studies: { id: string; track: Track; title: string; path: string; date: string; iso: string; method: string; summary: string; image: string }[] = [
  { id: "reasoning", track: "cost", title: "When is more reasoning worth it?", path: "/research/when-is-more-reasoning-worth-it", date: "Sep 24, 2026", iso: "2026-09-24", method: "Cost and accuracy experiment", summary: "More reasoning can improve an answer, but the payoff depends on the task and model. We compare what each upgrade costs with the extra correct answers it buys.", image: "/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp" },
  { id: "financial-review", track: "trust", title: "Which financial AI answers should we review?", path: "/research/which-financial-ai-answers-should-we-review", date: "Oct 10, 2026", iso: "2026-10-10", method: "Financial review · Part 1", summary: "When you can check only some answers, how should you choose? Verification caught more numerical mistakes than AI confidence in this setup, but still missed many.", image: "/research-assets/financial-answer-review/cover-v3.png" },
  { id: "negotiation", track: "agents", title: "How AI negotiates", path: "/research/how-ai-negotiates", date: "Oct 29, 2026", iso: "2026-10-29", method: "Negotiation experiment", summary: "Across 2,160 simulated negotiations, changes to buyer instructions had modest effects. The study examines the outcomes and the open question of why buyers appeared to lead.", image: "/research-assets/negotiation/negotiation-hero-v1.png" },
  { id: "financial-review-two", track: "trust", title: "Which financial AI answers should we review? Part 2", path: "/research/which-financial-ai-answers-should-we-review-part-2", date: "Oct 21, 2026", iso: "2026-10-21", method: "Financial review · Part 2", summary: "Does a useful review rule work with a different model? Across four AI configurations and two datasets, the better method changed. Review policies need testing too.", image: "/research-assets/financial-answer-review-part-2/cover-v1.png" },
  { id: "evaluation", track: "trust", title: "How to avoid false confidence in AI evaluations", path: "/research/how-to-avoid-false-confidence-in-ai-evaluations", date: "Sep 30, 2026", iso: "2026-09-30", method: "Simulation", summary: "A higher score can point to the wrong decision. Simulations show how repeated comparisons, related questions and missing results affect whether we should switch versions.", image: "/research-assets/evaluation-reliability/evaluation-confidence-cover.png" },
  { id: "reviewers", track: "trust", title: "How AI reviewers use test evidence", path: "/research/how-ai-reviewers-use-test-evidence", date: "Sep 13, 2026", iso: "2026-09-13", method: "Reviewer behavior experiment", summary: "Test reports helped AI reviewers reject faulty fixes, but reviewers still differed in which passing fixes they accepted. We examine how evidence changes their judgments.", image: "/research-assets/evidence-review/v3/three-lenses.webp" },
];

export function ResearchCatalog() {
  const [selected, setSelected] = useState<Track | "all">("all");
  const [covers, setCovers] = useState(false);
  const results = useRef<HTMLElement>(null);
  const visible = studies.filter(study => selected === "all" || study.track === selected);
  function choose(track: Track | "all") {
    setSelected(track);
    results.current?.scrollIntoView({ behavior: "instant", block: "start" });
  }
  return <>
    <section className={styles.tracks} aria-labelledby="tracks-title">
      <div className={styles.sectionHeading}><h2 id="tracks-title">Three questions guide the work</h2><span>Explore a track, or browse every study below.</span></div>
      <div className={styles.trackGrid}>{tracks.map((track, index) => <button type="button" key={track.id} className={styles.trackCard} aria-pressed={selected === track.id} onClick={() => choose(track.id)}>
        <span className={styles.eyebrow}>0{index + 1} / {track.name}</span><strong>{track.question}</strong><span className={styles.trackDescription}>{track.description}</span><span className={styles.trackLink}>Explore {studies.filter(s => s.track === track.id).length === 1 ? "the study" : "the studies"} <span aria-hidden="true">↓</span></span>
      </button>)}</div>
    </section>
    <section ref={results} id="all-research" className={styles.research} aria-labelledby="all-title">
      <div className={styles.sectionHeading}><div><h2 id="all-title">The research</h2><p>Every published study, with its methods, results and research code.</p></div><label className={styles.coverToggle}><input type="checkbox" checked={covers} onChange={e => setCovers(e.target.checked)} /> Show article covers</label></div>
      <div className={styles.filters} role="group" aria-label="Filter research by track"><button type="button" aria-pressed={selected === "all"} onClick={() => setSelected("all")}>All studies <span>6</span></button>{tracks.map(track => <button key={track.id} type="button" aria-pressed={selected === track.id} onClick={() => setSelected(track.id)}>{track.name}</button>)}</div>
      <p className={styles.resultCount} role="status">{selected === "all" ? "All 6 published studies" : `${visible.length} ${visible.length === 1 ? "study" : "studies"} in ${tracks.find(t => t.id === selected)!.name.toLowerCase()}`}</p>
      <div className={styles.studyGrid}>{visible.map(study => <article className={styles.studyCard} id={study.id} key={study.id}>
        {covers && <a href={study.path} className={styles.cover} aria-label={`Read ${study.title}`}><img src={study.image} width={1200} height={600} alt="" loading="lazy" /></a>}
        <div className={styles.studyCopy}><p className={styles.studyMeta}>{tracks.find(t => t.id === study.track)!.name}<time dateTime={study.iso}>{study.date}</time></p><h3><a href={study.path}>{study.title}</a></h3><p className={styles.summary}>{study.summary}</p><div className={styles.studyFoot}><span>{study.method}</span><a href={study.path}>Read study <span aria-hidden="true">↗</span></a></div></div>
      </article>)}</div>
    </section>
  </>;
}
