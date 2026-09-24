// Public release approved by the owner on September 24, 2026.
export const reasoningPublished = true;
// Explicit build-time opt-in for a bundled, local-only review server.
// Review builds remain noindex; normal builds publish the approved study.
export const localReview = process.env.NODE_ENV !== "production" || process.env.RESEARCH_LOCAL_REVIEW === "1";
export const showReasoningArticle = reasoningPublished || localReview;
export const publicOrigin = "https://research.muditgurnani.chatgpt.site";
