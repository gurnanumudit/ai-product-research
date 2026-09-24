// Keep false until the owner approves public publication.
export const reasoningPublished = false;
// Explicit build-time opt-in for a bundled, local-only review server.
// The ordinary production build still hides the unpublished study.
export const localReview = process.env.NODE_ENV !== "production" || process.env.RESEARCH_LOCAL_REVIEW === "1";
export const showReasoningArticle = reasoningPublished || localReview;
export const publicOrigin = "https://mudit-gurnani-research.muditgurnani.chatgpt.site";
