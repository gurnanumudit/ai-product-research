import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "The Test Passed. The Patch Was Still Wrong.",
  description:
    "A research note on whether one AI coding agent can safely verify another agent’s patch.",
  openGraph: {
    type: "article",
    title: "The Test Passed. The Patch Was Still Wrong.",
    description:
      "A research note on whether one AI coding agent can safely verify another agent’s patch.",
    images: [{ url: "/og-research-note.png", width: 1730, height: 909 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "The Test Passed. The Patch Was Still Wrong.",
    description:
      "A research note on whether one AI coding agent can safely verify another agent’s patch.",
    images: ["/og-research-note.png"],
  },
};

export default function AgentVerificationArticle() {
  return (
    <main className="articlePage" id="top">
      <header className="articleHeader shell">
        <Link className="wordmark" href="/" aria-label="Mudit Gurnani home">
          Mudit Gurnani
        </Link>
        <nav aria-label="Article navigation">
          <Link href="/#research">Research</Link>
          <a
            href="https://www.linkedin.com/in/muditgurnani"
            target="_blank"
            rel="noreferrer"
          >
            LinkedIn ↗
          </a>
          <a
            href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/agent-verification"
            target="_blank"
            rel="noreferrer"
          >
            GitHub ↗
          </a>
        </nav>
      </header>

      <header className="articleHero shell">
        <p className="articleLabel">Research note · AI agents and software</p>
        <h1>The Test Passed. The Patch Was Still Wrong.</h1>
        <p className="articleSubhead">
          What happened when we asked one AI coding agent to check another
          agent’s work.
        </p>
        <div className="articleByline">
          <span>Mudit Gurnani</span>
          <time dateTime="2026-06">June 2026</time>
          <span>6 minute read</span>
        </div>
      </header>

      <article className="articleBody">
        <section className="abstract" aria-label="Summary">
          <p>
            <strong>Summary.</strong> We tested a tempting product rule: let a
            second AI agent challenge a coding patch, then approve the patch if
            that check passes. Of the 38 submitted patches that passed the AI
            check, only 15 were actually correct. The other 23 were still wrong.
            A generated test can be useful evidence, but this verifier was not a
            safe release gate.
          </p>
          <div className="articleLinks">
            <a href="https://swe-rebench.com/about">About SWE-rebench ↗</a>
            <a
              href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/agent-verification"
            >
              Code and study materials ↗
            </a>
            <a href="#study-details">Study details ↓</a>
            <a href="#related-research">Related research ↓</a>
          </div>
        </section>

        <section>
          <p className="sectionLabel">Introduction</p>
          <h2>The idea sounded sensible</h2>
          <p className="lede">
            An AI coding agent says it fixed a bug. The change looks reasonable,
            and its test passes. Would you ship it?
          </p>
          <p>
            This is a practical problem for any product that lets AI change code.
            Producing a patch is only half the job. Someone—or something—still has
            to decide whether the patch is correct.
          </p>
          <p>
            We tested a simple answer. Let one AI write the code. Give a second AI
            the issue, repository, and proposed patch. Ask it to find a situation
            where the fix would fail. If it cannot find one and its check passes,
            perhaps the patch is safe to approve.
          </p>
          <blockquote>
            One AI writes the patch. Another tries to prove it wrong.
          </blockquote>
        </section>

        <section>
          <p className="sectionLabel">The experiment</p>
          <h2>How we tested it</h2>
          <p>
            We used recent software bugs from
            <a href="https://swe-rebench.com/about"> SWE-rebench</a>, a benchmark
            built from real GitHub issues. GPT-5.4 Mini and GPT-5.4 each received
            two attempts at 35 problems, producing 140 attempts in the main study.
          </p>

          <figure className="processFigure">
            <div className="studyFlow" aria-label="The three stages of the experiment">
              <div><span>1</span><strong>Build</strong><p>An AI coding agent proposes a patch.</p></div>
              <div><span>2</span><strong>Challenge</strong><p>A separate AI tries to expose a mistake.</p></div>
              <div><span>3</span><strong>Grade</strong><p>The benchmark’s full evaluation supplies the answer.</p></div>
            </div>
            <figcaption>
              <strong>Figure 1.</strong> The verifier never saw the benchmark’s final
              evaluation while it worked.
            </figcaption>
          </figure>

          <p>
            The second AI got one opportunity to examine each submitted patch. It
            could inspect the repository, run commands, and try several examples,
            but it returned one final verdict: its check passed or it did not.
          </p>

          <dl className="modelList" aria-label="Models used in the study">
            <div><dt>Patch generators</dt><dd>GPT-5.4 Mini and GPT-5.4</dd></div>
            <div><dt>Independent verifier</dt><dd>Claude Opus 4.6</dd></div>
            <div><dt>Problems</dt><dd>35 recent SWE-rebench issues</dd></div>
          </dl>
        </section>

        <section>
          <p className="sectionLabel">The verifier</p>
          <h2>What did the second AI actually do?</h2>
          <p>
            The verifier was a general-purpose Claude Opus 4.6 coding agent, not a
            model specially trained for this study. Its instruction was narrow:
            inspect the issue and patch, then create the smallest useful check that
            might show the patch was wrong.
          </p>
          <p>
            It could read the code and create new test files. It could not alter the
            proposed patch, see the correct patch, inspect the benchmark’s hidden
            evaluation, or learn which model produced the candidate. Our controller
            reran its check and rejected the result if protected files had changed.
          </p>
          <p>
            This matters because the study tested one simple verifier—not every way
            AI might verify software. A system that writes many independent tests,
            uses several agents, or searches inputs automatically may behave
            differently.
          </p>
        </section>

        <section>
          <p className="sectionLabel">Ground truth</p>
          <h2>How did we know whether a patch was really correct?</h2>
          <p>
            The verifier did not grade itself. SWE-rebench provides a separate
            official evaluation for each issue. It checks whether the reported bug
            was fixed and whether the patch broke existing behavior.
          </p>
          <p>
            Only after the patches and verifier results were recorded did we run
            that evaluation in a fresh environment. A patch counted as correct only
            when it passed this independent source of truth.
          </p>
          <div className="truthLine" aria-label="Separation between the AI check and ground truth">
            <div><span>The AI saw</span><strong>Issue + code + proposed patch</strong></div>
            <i aria-hidden="true">separate from</i>
            <div><span>The final judge saw</span><strong>SWE-rebench’s full evaluation</strong></div>
          </div>
        </section>

        <section>
          <p className="sectionLabel">Results</p>
          <h2>The check passed more wrong patches than correct ones</h2>
          <p>
            The coding agents submitted 82 patches. Thirty-eight passed the second
            AI’s check. When the full evaluation ran, only 15 of those 38 patches
            were correct. The remaining <strong>23 were still wrong</strong>.
          </p>

          <figure className="confusionFigure">
            <div className="matrixScroll">
              <table className="confusionMatrix">
                <thead>
                  <tr>
                    <th scope="col">AI check</th>
                    <th scope="col">Actually correct</th>
                    <th scope="col">Actually wrong</th>
                    <th scope="col">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">Passed</th>
                    <td className="matrixGood"><strong>15</strong><span>Useful approval</span></td>
                    <td className="matrixDanger"><strong>23</strong><span>Unsafe approval</span></td>
                    <td className="matrixTotal">38</td>
                  </tr>
                  <tr>
                    <th scope="row">No approval</th>
                    <td className="matrixMiss"><strong>13</strong><span>Correct patch missed</span></td>
                    <td className="matrixSafe"><strong>31</strong><span>Wrong patch not approved</span></td>
                    <td className="matrixTotal">44</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr><th scope="row">Total</th><td>28</td><td>54</td><td>82</td></tr>
                </tfoot>
              </table>
            </div>
            <figcaption>
              <strong>Figure 2.</strong> Red is the central problem: 23 wrong patches
              received a reassuring pass. “No approval” mostly means the verifier did
              not return a usable result; it should not be read as 44 mistakes caught.
            </figcaption>
          </figure>

          <p className="findingStatement">
            In this experiment, passing one AI-generated check was not strong evidence
            that the patch was correct.
          </p>
        </section>

        <section>
          <p className="sectionLabel">Interpretation</p>
          <h2>Why can a wrong patch pass a good test?</h2>
          <p>
            A test checks a particular situation. A requirement is usually wider.
            Imagine a discount that should apply only to a customer’s first order and
            never to gift cards. A test may correctly check the first-order rule but
            never try a gift card. The test passes while the patch implements only half
            the requirement.
          </p>
          <p>
            Two AI agents can also share the same blind spot. They may focus on the
            obvious example, interpret an ambiguous sentence the same way, or overlook
            the same edge case. A second model is independent in name, but not
            necessarily independent in reasoning.
          </p>
        </section>

        <section>
          <p className="sectionLabel">Product implication</p>
          <h2>Keep the verifier, but change its job</h2>
          <p>
            The second agent can still add value. It can suggest tests, point to risky
            areas, and provide extra evidence. It should not provide final sign-off by
            itself.
          </p>
          <ul>
            <li>Run the project’s full evaluation on every submitted patch.</li>
            <li>Treat AI-generated tests as additional coverage, not approval.</li>
            <li>Escalate when evidence is missing or the change is high risk.</li>
            <li>Measure false approvals before trusting any verifier in production.</li>
          </ul>
        </section>

        <section>
          <p className="sectionLabel">Secondary finding</p>
          <h2>Calling the stronger model helped—but only a little</h2>
          <p>
            GPT-5.4 Mini solved 18 of its 70 attempts. GPT-5.4 solved 10. We also
            tested a simple route: start with Mini, then call GPT-5.4 only when Mini
            produced no patch. That raised the result from 18 to 20 correct solutions.
          </p>

          <figure className="routingFigure">
            <div className="routingRow">
              <span>GPT-5.4 Mini alone</span>
              <div className="routingTrack"><i className="routeMini" style={{ width: "90%" }} /></div>
              <strong>18</strong>
            </div>
            <div className="routingRow">
              <span>GPT-5.4 alone</span>
              <div className="routingTrack"><i className="routeStrong" style={{ width: "50%" }} /></div>
              <strong>10</strong>
            </div>
            <div className="routingRow">
              <span>Mini, then GPT-5.4 when no patch appeared</span>
              <div className="routingTrack"><i className="routeEscalated" style={{ width: "100%" }} /></div>
              <strong>20</strong>
            </div>
            <figcaption>
              <strong>Figure 3.</strong> Correct solutions out of the same 70 problems.
              Escalation recovered two additional fixes for $3.02.
            </figcaption>
          </figure>
          <p>
            “No patch produced” was a useful reason to escalate. But once a patch
            existed, routing could not tell us whether it was right. The verification
            problem remained.
          </p>
        </section>

        <section>
          <p className="sectionLabel">Limitations</p>
          <h2>What this study does—and does not—show</h2>
          <p>
            We tested one verifier model, given one independent opportunity to examine
            each patch, on a fixed set of software issues. We did not prove that every
            AI verifier fails or that these results represent every production codebase.
          </p>
          <p>
            We did show that a plausible design was unsafe for automatic approval. The
            next experiment should hold the patches fixed and compare stronger verifier
            designs: multiple independent tests, adversarial search, property-based
            testing, and verifier ensembles.
          </p>
        </section>

        <section>
          <p className="sectionLabel">Conclusion</p>
          <h2>A test pass is a clue—not clearance</h2>
          <p>
            Asking a second AI to challenge a patch is a good instinct. Treating its
            passing check as permission to ship is not. The useful product is not a
            confident verifier; it is a verification system that knows how much evidence
            a decision requires.
          </p>
        </section>

        <details className="technicalDetails" id="study-details">
          <summary>Study details and technical notes</summary>
          <div>
            <p>
              The complete study used 43 repositories: eight for validation and 35
              for the main evaluation. The generators were GPT-5.4 Mini and GPT-5.4;
              the verifier was Claude Opus 4.6. All systems used frozen instructions
              and limits.
            </p>
            <p>
              The decision not to allow automatic approval was made from validation
              results before main outcomes were opened. Across the main study, 28
              submitted patches were correct, 54 were wrong, and 58 attempts produced
              no patch. Model usage was $23.82; Sandbox usage was conservatively bounded
              at $4.56.
            </p>
          </div>
        </details>

        <section className="relatedResearch" id="related-research">
          <p className="sectionLabel">Further reading</p>
          <h2>Related research</h2>
          <div className="researchNotes">
            <article>
              <h3>AI-generated tests can find real bugs</h3>
              <p>
                Anthropic’s property-testing agent found that a NumPy function could
                return impossible negative values; maintainers merged the resulting
                fix. But another report involving Python calendar behavior was judged
                invalid because the semantics were subtler than the agent assumed.
              </p>
              <a href="https://www.anthropic.com/research/property-based-testing">Read the Anthropic study ↗</a>
            </article>
            <article>
              <h3>Even official tests can be incomplete</h3>
              <p>
                UTBoost reported 345 erroneous SWE-bench patches that had previously
                been labelled as passing. Its lesson closely matches ours: a test suite
                can look authoritative and still miss the underlying requirement.
              </p>
              <a href="https://arxiv.org/abs/2506.09289">Read the UTBoost paper ↗</a>
            </article>
            <article>
              <h3>Better verifier designs are possible</h3>
              <p>
                Otter combines language-model test generation with rule-based checks
                and self-reflection. That is a useful direction for the next study:
                compare verifier architectures rather than treating one agent pass as
                the final answer.
              </p>
              <a href="https://arxiv.org/abs/2502.05368">Read the Otter paper ↗</a>
            </article>
          </div>
        </section>

        <nav className="articleFooterNav" aria-label="Article footer">
          <Link href="/">← All research</Link>
          <a
            href="https://www.linkedin.com/in/muditgurnani"
            target="_blank"
            rel="noreferrer"
          >
            LinkedIn ↗
          </a>
          <a href="#top">Back to top ↑</a>
        </nav>
      </article>
    </main>
  );
}
