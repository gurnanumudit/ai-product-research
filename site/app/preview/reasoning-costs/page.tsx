import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { showReasoningArticle, reasoningPublished, publicOrigin, localReview } from "@/lib/research-release";
import data from "@/content/reasoning-expanded.json";
import { ArticleIndex } from "@/components/article/article-index";
import base from "@/components/article/page.module.css";
import styles from "./page.module.css";
import { ResultsOverview, ExactResults, ExactCosts, CostSmallMultiples, Recommendations, DollarImpact, percent, type Point } from "./expanded-figures";
import { DifficultyMethod, DifficultyRubricAppendix } from "./difficulty-method";

export const metadata: Metadata = {
  title: reasoningPublished ? "When is more reasoning worth it?" : "When is more reasoning worth it? · Review draft",
  description: "134 analytical questions, three models and three reasoning settings. Where reasoning helped, and what extra effort bought.",
  robots: { index: reasoningPublished && !localReview, follow: reasoningPublished && !localReview },
  alternates: { canonical: publicOrigin + "/research/when-is-more-reasoning-worth-it" },
  openGraph: { title: "When is more reasoning worth it?", description: "An experiment on reasoning, analytical accuracy and model spending across 134 questions.", images: [] },
  twitter: { card: "summary", title: "When is more reasoning worth it?", description: "An experiment on reasoning, analytical accuracy and model spending across 134 questions.", images: [] },
};
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const points: Point[] = data.points.map(p => ({ ...p, effort: cap(p.effort) }));
const economic: Point[] = data.economicFullPoints.map(p => ({ ...p, effort: cap(p.effort) }));
const entries = [
  { id: "introduction", title: "Why this research?" },
  { id: "experiment-setup", title: "How we tested reasoning" },
  { id: "results-overview", title: "Results across 134 questions" },
  { id: "finding-1", title: "1. Reasoning beyond hard tasks" },
  { id: "finding-2", title: "2. The payoff from high effort" },
  { id: "dollar-impact", title: "What the upgrade buys", nested: true },
  { id: "choosing-settings", title: "How to use these findings" },
  { id: "limitations", title: "What this study does—and doesn’t—tell us" },
  { id: "conclusion", title: "The bottom line" },
  { id: "appendix", title: "Appendix" },
  { id: "appendix-a", title: "A. Sample and selection", nested: true },
  { id: "difficulty-rubric", title: "B. Difficulty rubric", nested: true },
  { id: "appendix-b", title: "C. Models and scoring", nested: true },
  { id: "appendix-c", title: "D. Exact results and phases", nested: true },
  { id: "appendix-d", title: "E. Costs and uncertainty", nested: true },
  { id: "appendix-e", title: "F. Robustness checks", nested: true },
  { id: "appendix-f", title: "G. Delivery failures", nested: true },
  { id: "references", title: "References" },
];
function AppendixReturn({ href, label }: { href: string; label: string }) {
  return <p className={styles.appendixReturn}><a href={href}>Back to {label} ↑</a></p>;
}
function PhaseTable() {
  return <div className={styles.resultsTable}><table><caption>Overall success within each collection cohort. Historical grades were preserved.</caption><thead><tr><th>Model / reasoning</th><th>Original 50</th><th>Additional 84</th><th>Combined 134</th></tr></thead><tbody>{data.overall.map(p => {
    const old = data.historicalOverall.find(q => q.modelName === p.modelName && q.effort === p.effort)!;
    const ext = data.extensionOverall.find(q => q.modelName === p.modelName && q.effort === p.effort)!;
    return <tr key={p.modelName+p.effort}><th scope="row">{p.modelName} · {cap(p.effort)}</th><td>{percent(old.correct, old.n)}</td><td>{percent(ext.correct, ext.n)}</td><td>{percent(p.correct, p.n)}</td></tr>;
  })}</tbody></table></div>;
}
function SensitivityTable() {
  return <div className={styles.resultsTable}><table><caption>Filtered comparisons remove whole questions across all nine settings.</caption><thead><tr><th>Model / reasoning</th><th>Main · 134</th><th>No provider / infrastructure failures · 97</th><th>Ordinary terminals only · 92</th></tr></thead><tbody>{data.overall.map(p => <tr key={p.modelName+p.effort}><th scope="row">{p.modelName} · {cap(p.effort)}</th><td>{percent(p.correct, p.n)}</td>{Object.values(data.sensitivities).map((s, i) => { const v = s.overall.find(q => q.modelName === p.modelName && q.effort === p.effort)!; return <td key={i}>{percent(v.correct, v.n)}</td>; })}</tr>)}</tbody></table></div>;
}

export default function ReasoningArticle() {
  if (!showReasoningArticle) notFound();
  return <div className={`${base.page} ${styles.page}`}>
    <a className={base.skip} href="#introduction">Skip to article</a>
    <header className={base.siteHeader}><a href="/" className={base.wordmark}>Mudit Gurnani</a><nav aria-label="Site navigation"><a href="/">Research</a><a href="#appendix">Methods & results</a></nav></header>
    <main>
      <header className={`${base.hero} ${styles.hero}`}><p className={base.eyebrow}>AI economics{!reasoningPublished && " · Review draft"}</p><h1>When is more<br />reasoning worth it?</h1><p className={base.subtitle}>The cheapest answer is not always the best choice. We tested three models at three reasoning settings to see when paying more was worthwhile.</p><p className={base.byline}>Mudit Gurnani <span>·</span> Updated September 24, 2026{!reasoningPublished && <> <span>·</span> Unpublished</>}</p><p className={base.resourceLine}><a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/reasoning-costs">Study code and results ↗</a></p></header>
      <figure className={base.cover}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp" width={1774} height={887} alt="A none, low and high reasoning dial links spreadsheets to branching analytical paths; coins represent cost." fetchPriority="high" />
        <figcaption>How much reasoning should an analytical task receive? AI-generated editorial illustration.</figcaption>
      </figure>
      <div className={styles.studyStrip}><div><strong>134</strong><span>evaluated questions</span></div><div><strong>3 × 3</strong><span>models × reasoning settings</span></div><div><strong>1,206</strong><span>matched results</span></div></div>
      <div className={base.layout}><ArticleIndex entries={entries} /><article className={`${base.article} ${styles.article}`}>
        <section id="introduction" className={base.section}><h2>Why this research?</h2><div className="prose"><p>We wanted to understand model capabilities on analytical work beyond coding: interpreting spreadsheets, performing calculations and building forecasts. Should you use a cheaper model with more reasoning, or a more expensive model with less? Does the answer change with the complexity of the task?</p><p>On mathematical problems, <a href="https://arxiv.org/abs/2408.03314">Snell and colleagues</a> found that the benefit of additional computation depended on problem difficulty and how that computation was used. We explored a related practical question: when is it worth paying for more reasoning on analytical work?</p><p>We chose business-analysis questions from <a href="https://arxiv.org/abs/2409.07703">DSBench, a benchmark designed around realistic data-science tasks</a>. Models could use code as a tool, but we evaluated the final analytical answer—not the code itself. By testing the same questions across three models and three reasoning settings, we examined when extra reasoning improves results and whether the improvement justifies the cost. <a href="#appendix-a">Our question selection</a>.</p></div></section>
        <section id="experiment-setup" className={base.section}><h2>How we tested reasoning</h2><div className="prose"><p>We evaluated 134 business-analysis questions using three OpenAI GPT-5.6 models—Luna, Terra and Sol—each with reasoning set to none, low and high. Every setting faced the same questions and tools. The tasks came from <a href="#appendix-a">DSBench’s business-analysis material</a>, including operating calendars, tax calculations, financial forecasts and loan schedules.</p></div><DifficultyMethod /></section>
        <section id="results-overview" className={base.section}><h2>The results at a glance</h2><div className="prose"><p>Success means <a href="#appendix-b">returning the correct final answer</a>; a wrong answer or no answer counts as unsuccessful.</p></div><ResultsOverview points={points} /><div className="prose"><p><a href="#appendix-c">Exact counts</a> · <a href="#appendix-f">Examples of unsuccessful answers</a> · <a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/reasoning-costs">Research code and results on GitHub</a>.</p></div></section>
        <section id="finding-1" className={base.section}><h2>1. Reasoning helped beyond hard tasks</h2><div className="prose"><h3>Was reasoning useful on easy work?</h3><p>Yes. Some reasoning helped every model across easy, medium and hard questions. The benefit wasn’t limited to difficult work—even straightforward tasks benefited from a little reasoning. <a href="#appendix-e">Checks on operational failures</a>.</p><p>This is not a universal rule. <a href="https://arxiv.org/abs/2504.09858">Ma and colleagues</a> found that skipping explicit thinking could work well in tested reasoning models under tight token budgets. Their setup differs from ours; here, low reasoning improved success over none in every model and difficulty group.</p><h3>What this means</h3><p>Don’t switch reasoning off just because a task looks easy. Start with some reasoning; then decide whether turning it up is worth the extra cost.</p></div></section>
        <section id="finding-2" className={base.section}><h2>2. High reasoning had a conditional payoff</h2><div className="prose"><h3>When was turning it up worthwhile?</h3><p>Compared with low, high reasoning helped Luna most on easy and hard questions, with little change on medium work. Terra gained most on hard questions. Sol benefited most on medium questions.</p><p>On hard questions, Sol high solved four that low missed—but missed four that low solved. The totals tied, even though the answers differed. That is not evidence that the two settings are interchangeable. <a href="#hard-question-check">The tie and workload mix</a>.</p><p>Research by <a href="https://arxiv.org/abs/2412.21187">Chen and colleagues on overthinking</a> shows that models can spend extra computation for little benefit, particularly on simpler problems. That offers context for our mixed returns from high reasoning, but does not establish why particular answers failed in our study.</p><h3>What should you pay for?</h3><p><a href="https://arxiv.org/abs/2407.01502">Kapoor and colleagues argue for evaluating agent accuracy and cost together</a>. We use that lens below: what does an upgrade cost, and how many more correct answers does it deliver?</p><p>Pay for more correct answers, not simply a higher setting. Cost per correct answer leaves out what a wrong or missing answer costs you. Whether an upgrade is worthwhile depends on how much those failures matter in your work.</p></div>
          <DollarImpact points={economic} />
          <div className="prose"><p>The easy-question upgrade cost very little. The medium and hard comparisons bought more correct answers at a larger premium. These figures include model charges and pending reservations, not the full cost of running an agent. Runtime and the cost of mistakes can change which option is worthwhile. <a href="#appendix-d">Full cost breakdown</a>.</p></div>
        </section>
        <section id="choosing-settings" className={base.section}><h2>How to use these findings</h2><div className="prose"><p>A cheaper model with more reasoning can be a useful alternative to a more expensive model—but only if its accuracy is sufficient for your work. The table pairs a lower-cost option with the highest-scoring setting in each group, not a single best-value choice for everyone. <a href="#configuration-choice">How we chose these options</a>.</p></div><Recommendations points={economic} /><div className="prose"><ol><li>Group your own tasks by complexity before testing, based on the work required.</li><li>Compare the same questions across candidate settings. Record correct final answers, failures and total costs.</li><li>Choose the least expensive option that meets your accuracy needs, then check it on fresh tasks before adopting it.</li></ol></div></section>
        <section id="limitations" className={base.section}><span id="appendix-g" aria-hidden="true" /><h2>What this study does—and doesn’t—tell us</h2><div className="prose"><p>Use this study to shortlist model and reasoning settings and understand when extra spending may buy better results. The findings come from selected questions, some sharing the same workbook, with difficulty labels assigned by us. We don’t know whether the models saw these public questions during training. Small differences don’t prove one setting is better, so test the options on your own work rather than treating these results as a universal ranking or a guarantee of accuracy or cost.</p></div></section>
        <section id="conclusion" className={base.section}><h2>The bottom line</h2><div className="prose"><p>Some reasoning helped across easy, medium and hard analytical work. More reasoning was not always better, and the most expensive setting did not always return more correct answers. <strong>Choose the cheapest setting that meets the accuracy your work needs.</strong></p></div></section>
        <section id="appendix" className={base.appendix}>
          <p className={base.eyebrow}>Methods and supporting material</p><h2>Appendix</h2>
          <p className={base.appendixIntro}>The evidence behind the main findings. Expand the supporting tables for exact values.</p>
          <div className="prose"><p>The <a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/reasoning-costs">research supplement</a> includes question-level outcomes, costs and instructions to reproduce the article’s numbers without paid model calls. It reproduces the analysis from saved classifications, not the original experiment or independent answer grading.</p></div>
          <section id="appendix-a" className={base.appendixSection}>
            <h3>A. Sample and selection</h3>
            <div className="prose">
              <p>We used selected questions from DSBench’s public data-analysis track, derived from ModelOff business-analysis cases—not its separate modeling track. Most use Excel workbooks; some use supplied text. The <a href="https://github.com/LiqiangJing/DSBench/tree/ba786096137a5108af11c016ad3f09cdb97beefd/data_analysis">dataset version</a> was fixed before collection.</p>
              <p>The matched sample contains 29 easy, 55 medium and 50 hard questions. Five additional medium questions were excluded from all nine settings because evaluation was incomplete, not because of their scores.</p>
              <p>The questions share 24 source contexts and were purposefully selected, not randomly sampled. One answer changes the easy rate by 3.4 percentage points, medium by 1.8 and hard by 2.0.</p>
            </div>
            <details className={styles.appendixDetails}><summary>Excluded questions and coverage</summary><div className="prose"><p>Across the five excluded questions, 19 configuration runs never started and 26 finished. All 45 were kept outside the matched comparison; records and spending remain in the research archive.</p><p>{data.excludedQuestions.map((q,i) => <span key={q}>{i > 0 ? "; " : ""}<code>{q}</code></span>)}</p></div></details>
            <AppendixReturn href="#experiment-setup" label="How we tested reasoning" />
          </section>
          <DifficultyRubricAppendix />
          <section id="appendix-b" className={base.appendixSection}>
            <h3>C. Models, tools and scoring</h3>
            <div className="prose">
              <p>We used <code>openai/gpt-5.6-luna</code>, <code>openai/gpt-5.6-terra</code> and <code>openai/gpt-5.6-sol</code> at none, low and high reasoning. Each setting received the same questions and tools; prompts, scoring and per-task limits stayed fixed across the extension.</p>
              <p>Each question/configuration has one selected result. Six budget-interrupted runs received approved retries; we used the retry outcome regardless of success, never the better answer. Costs include both attempts.</p>
              <p>We scored final answers against the frozen public reference using a deterministic option/numeric comparator adapted from the publisher’s evaluator. Wrong, invalid or missing answers scored zero; runs that never started were not scored as wrong. We verified reference attachment but did not independently rederive every reference answer.</p>
              <p>Collection used different concurrency and operational-containment phases, with an interim review. These changed scheduling and execution handling, not questions, model settings, per-task limits or scoring. Phase comparisons are therefore descriptive, not randomized.</p>
            </div>
            <AppendixReturn href="#results-overview" label="The results at a glance" />
          </section>
          <section id="appendix-c" className={base.appendixSection}>
            <h3>D. Exact results and collection cohorts</h3><ExactResults points={points} />
            <details className={styles.appendixDetails}><summary>How the results varied across collection cohorts</summary><div className="prose"><p>The original 50 questions included 10 easy, 10 medium and 30 hard; the additional 84 included 19, 45 and 20. Sol low → high fell from 84% to 78% in the first cohort but rose from 84.5% to 92.9% in the second. The question mix matters; this is not evidence of a change in model capability.</p></div><PhaseTable /></details>
            <AppendixReturn href="#results-overview" label="The results at a glance" />
          </section>
          <section id="appendix-d" className={base.appendixSection}>
            <h3>E. Costs and the value calculation</h3>
            <div className="prose">
              <p>Costs cover the same 134 questions as accuracy, including failures and approved retries: 1,212 physical attempts. “Model cost” adds recorded charges and pending reservations; it is not a settled bill or a quote at one current tariff. Runtime estimates are separate.</p>
              <p id="configuration-choice">The lower-cost comparisons use Luna low for easy/medium and Luna high for hard. These are illustrative trade-offs, not an optimized routing rule. The accuracy column picks the most correct answers, then the cheaper setting if tied. Cost per correct answer favors Luna low in every band, but cannot price the harm of a wrong or missing answer.</p>
              <p id="cost-calculation">For each difficulty group, extra cost per 100 = 100 × the difference in total model costs ÷ question count. Extra correct answers uses the same calculation on correct counts. We calculate before rounding; scaling does not create new trials or predict future results.</p>
              <p>Including estimated runtime narrowly makes Luna high cheaper per correct easy answer than Luna low ($0.0408 versus $0.0413); low remains cheapest on medium and hard. Pending reservations and estimated runtime leave final-bill rankings uncertain.</p>
            </div>
            <details className={styles.appendixDetails}><summary>Exact costs for all 27 configurations</summary><div className="prose"><p>Retained-question totals: $30.5499 in model charges, $4.4001 pending and $49.1097 in estimated runtime. Excluded-question spending is preserved separately.</p></div><ExactCosts points={economic} /></details>
            <CostSmallMultiples points={economic} />
            <div className="prose"><p>A frontier point has no tested alternative that is both no more expensive and at least as successful, with one strict improvement. The hard-question frontier contains Luna none, low and high, then Sol low. Lines guide the eye; intermediate settings were not tested.</p></div>
            <AppendixReturn href="#dollar-impact" label="What does the upgrade buy?" />
          </section>
          <section id="appendix-e" className={base.appendixSection}>
            <h3>F. Operational and shared-context checks</h3>
            <div className="prose"><p>Removing every question affected by a provider or infrastructure failure in any setting leaves 97 questions: 26 easy, 42 medium and 29 hard. Low still beats none in all nine model/difficulty comparisons. Requiring ordinary completed answers at every setting leaves 92 questions. Both checks remove whole questions, not individual bad results.</p></div>
            <details className={styles.appendixDetails}><summary>Results with operational failures filtered out</summary><SensitivityTable /><div className="prose"><p>In the 97-question check, high’s hard-question gain over low is 17.2 percentage points for Luna and Terra and 3.4 for Sol. These checks do not replace the primary results, which retain attempted failures.</p></div></details>
            <div id="hard-question-check" className="prose"><h4>Why the Sol tie needs care</h4><p>Sol low and high each answered 42 of 50 hard questions correctly: 38 were correct at both settings, four only at low and four only at high. Both missed the remaining four.</p><p>Giving each of the 16 hard-question source contexts equal weight instead gives low 89.4% and high 77.1%. The workload mix changes the comparison; equal question-level totals do not establish equivalence.</p></div>
            <AppendixReturn href="#finding-2" label="The payoff from high reasoning" />
          </section>
          <section id="appendix-f" className={base.appendixSection}>
            <h3>G. Delivery failures and worked examples</h3>
            <div className="prose"><p>The 1,206 evaluations include 899 correct deliveries and 69 provider/infrastructure failures. These failures did not consistently increase with model size or reasoning. Another 19 model-limit or fallback outcomes are separate; some returned answers.</p><p>On an easy operating-days question, Luna none calculated 92 − 17 = 75 but submitted the option for 76. Low and high submitted 75. We scored the final answer, not the calculation.</p><p>On one tax workbook, Sol timed out at every setting on both a medium calculation and a hard forecast. Six failures on one workbook are not six independent reasoning errors. These examples illustrate failure modes, not their prevalence.</p></div>
            <AppendixReturn href="#results-overview" label="How success is counted" />
          </section>
        </section>
        <section id="references" className={`${base.section} ${styles.references}`} aria-labelledby="references-heading">
          <h2 id="references-heading">References</h2>
          <ol>
            <li>Snell, C., Lee, J., Xu, K., and Kumar, A. (2024). <a href="https://arxiv.org/abs/2408.03314">Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters</a>. arXiv:2408.03314.</li>
            <li>Jing, L., et al. (2025). <a href="https://arxiv.org/abs/2409.07703">DSBench: How Far Are Data Science Agents from Becoming Data Science Experts?</a> ICLR 2025. arXiv:2409.07703.</li>
            <li>Ma, W., He, J., Snell, C., Griggs, T., Min, S., and Zaharia, M. (2025). <a href="https://arxiv.org/abs/2504.09858">Reasoning Models Can Be Effective Without Thinking</a>. arXiv:2504.09858.</li>
            <li>Chen, X., et al. (2024; revised 2025). <a href="https://arxiv.org/abs/2412.21187">Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs</a>. arXiv:2412.21187.</li>
            <li>Kapoor, S., Stroebl, B., Siegel, Z. S., Nadgir, N., and Narayanan, A. (2024). <a href="https://arxiv.org/abs/2407.01502">AI Agents That Matter</a>. arXiv:2407.01502.</li>
          </ol>
        </section>
      </article></div>
    </main><footer className={base.footer}><span>{reasoningPublished ? "Independent research by Mudit Gurnani" : "Review draft · Not published"}</span><a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/reasoning-costs">Study code and results ↗</a><a href="#introduction">Back to introduction ↑</a></footer>
  </div>;
}
