import Link from "next/link";

export default function Home() {
  return (
    <main>
      <header className="siteHeader shell">
        <Link className="wordmark" href="/" aria-label="Mudit Gurnani home">
          Mudit Gurnani
        </Link>
        <nav aria-label="Primary navigation">
          <a href="#research">Research</a>
          <a href="#about">About</a>
          <a
            href="https://www.linkedin.com/in/muditgurnani"
            target="_blank"
            rel="noreferrer"
          >
            LinkedIn ↗
          </a>
          <a
            href="https://github.com/gurnanumudit/ai-product-research"
            target="_blank"
            rel="noreferrer"
          >
            GitHub ↗
          </a>
        </nav>
      </header>

      <section className="homeIntro shell">
        <p className="eyebrow">Independent research</p>
        <h1>Research notes on how AI systems behave in the real world.</h1>
        <p className="homeDek">
          I run practical experiments and write about what the results mean for
          people building AI products.
        </p>
      </section>

      <section className="researchIndex shell" id="research">
        <div className="sectionHeader">
          <h2>Research</h2>
          <p>New work will be added as each study is ready to share.</p>
        </div>

        <article className="researchEntry">
          <div className="researchDate">
            <time dateTime="2026-06">June 2026</time>
            <span>AI agents · Software</span>
          </div>
          <div className="researchSummary">
            <h3>The Test Passed. The Patch Was Still Wrong.</h3>
            <p>
              We asked an independent AI agent to check another agent’s code.
              Passing that check sounded reassuring. In our experiment, it was not
              enough to safely approve the patch.
            </p>
            <Link href="/research/agent-verification">
              Read the research note <span aria-hidden="true">→</span>
            </Link>
          </div>
          <div className="researchFinding" aria-label="Key finding">
            <span>Key finding</span>
            <strong>23 of 38</strong>
            <p>Patches that passed the AI check were still wrong.</p>
          </div>
        </article>
      </section>

      <section className="simpleAbout shell" id="about">
        <h2>About</h2>
        <div>
          <p>
            I’m Mudit Gurnani. This is a growing collection of experiments and
            essays about AI, products, and decisions worth testing.
          </p>
          <a
            href="https://www.linkedin.com/in/muditgurnani"
            target="_blank"
            rel="noreferrer"
          >
            Connect on LinkedIn ↗
          </a>
        </div>
      </section>

      <footer className="siteFooter shell">
        <span>© 2026 Mudit Gurnani</span>
        <a
          href="https://github.com/gurnanumudit/ai-product-research"
          target="_blank"
          rel="noreferrer"
        >
          Code and study materials ↗
        </a>
      </footer>
    </main>
  );
}
