export type ResearchTrack = "cost" | "trust" | "agents";

export type ResearchStudy = {
  id: string;
  track: ResearchTrack;
  title: string;
  path: string;
  date: string;
  iso: string;
  method: string;
  summary: string;
  image: string;
};

export const researchTracks: {
  id: ResearchTrack;
  name: string;
  question: string;
  description: string;
}[] = [
  {
    id: "trust",
    name: "Trust and review",
    question: "Which results can we rely on?",
    description: "Test how we evaluate AI, catch mistakes and decide when the evidence is strong enough.",
  },
  {
    id: "cost",
    name: "Cost and quality",
    question: "When is better AI worth the cost?",
    description: "Compare models and workflows by the quality they deliver and the resources they use.",
  },
  {
    id: "agents",
    name: "Agent decisions",
    question: "What shapes an AI agent’s decisions?",
    description: "Study how instructions, roles and incentives affect behavior when AI agents interact.",
  },
];

export const publishedStudies: ResearchStudy[] = [
  {
    id: "negotiation-two",
    track: "agents",
    title: "How AI negotiates Part 2",
    path: "/research/how-ai-negotiates-part-2",
    date: "Nov 4, 2026",
    iso: "2026-11-04",
    method: "Negotiation · Part 2",
    summary: "Does the buyer’s advantage last when opportunities are reversed? We tested both who starts and which side has the better opportunity.",
    image: "/research-assets/negotiation-part2/negotiation-hero-v1.png",
  },
  {
    id: "tool-error",
    track: "trust",
    title: "When a test report is wrong, is a warning enough?",
    path: "/research/when-a-test-report-is-wrong",
    date: "Nov 1, 2026",
    iso: "2026-11-01",
    method: "Tool feedback experiment",
    summary: "Warning an AI about unreliable test reports did little to help. Running the tests again helped most when the first report falsely claimed success.",
    image: "/research-assets/tool-error/cover.png",
  },
  {
    id: "financial-review",
    track: "trust",
    title: "Which financial AI answers should we review? Part 1",
    path: "/research/which-financial-ai-answers-should-we-review",
    date: "Oct 10, 2026",
    iso: "2026-10-10",
    method: "Financial review · Part 1",
    summary: "Checking calculations and cited figures helped select more wrong answers for review than relying on the AI’s confidence.",
    image: "/research-assets/financial-answer-review/cover-v3.png",
  },
  {
    id: "reasoning",
    track: "cost",
    title: "When is more reasoning worth it?",
    path: "/research/when-is-more-reasoning-worth-it",
    date: "Sep 24, 2026",
    iso: "2026-09-24",
    method: "Cost and accuracy experiment",
    summary: "More reasoning can improve accuracy, but is the improvement worth the cost? The answer depends on the model and task.",
    image: "/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp",
  },
  {
    id: "negotiation",
    track: "agents",
    title: "How AI negotiates Part 1",
    path: "/research/how-ai-negotiates",
    date: "Oct 29, 2026",
    iso: "2026-10-29",
    method: "Negotiation · Part 1",
    summary: "Changing buyer instructions had modest effects in simulated negotiations. Buyers appeared to have an advantage, prompting a closer look at why.",
    image: "/research-assets/negotiation/negotiation-hero-v1.png",
  },
  {
    id: "financial-review-two",
    track: "trust",
    title: "Which financial AI answers should we review? Part 2",
    path: "/research/which-financial-ai-answers-should-we-review-part-2",
    date: "Oct 21, 2026",
    iso: "2026-10-21",
    method: "Financial review · Part 2",
    summary: "The same checks did not work equally well across models. Some wrong answers passed without a warning.",
    image: "/research-assets/financial-answer-review-part-2/cover-v1.png",
  },
  {
    id: "evaluation",
    track: "trust",
    title: "How to avoid false confidence in AI evaluations",
    path: "/research/how-to-avoid-false-confidence-in-ai-evaluations",
    date: "Sep 30, 2026",
    iso: "2026-09-30",
    method: "Simulation",
    summary: "A higher test score is not always a good reason to switch AI models. Simulations show how testing choices can lead us astray.",
    image: "/research-assets/evaluation-reliability/evaluation-confidence-cover.png",
  },
  {
    id: "reviewers",
    track: "trust",
    title: "How AI reviewers use test evidence",
    path: "/research/how-ai-reviewers-use-test-evidence",
    date: "Sep 13, 2026",
    iso: "2026-09-13",
    method: "Reviewer behavior experiment",
    summary: "Test reports helped AI reviewers reject faulty code fixes. But reviewers still differed in which fixes they accepted when tests passed.",
    image: "/research-assets/evidence-review/v3/three-lenses.webp",
  },
];

export const latestStudy = publishedStudies.reduce((latest, study) =>
  latest.iso > study.iso ? latest : study,
);
