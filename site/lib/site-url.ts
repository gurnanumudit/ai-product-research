import { publicOrigin } from "./research-release";

// Social metadata uses the configured public origin, never untrusted Host headers.
export async function requestSiteUrl() {
  return new URL(publicOrigin);
}

export async function socialPreviewUrl() {
  return new URL("/og-research-journey-v1.png", publicOrigin);
}
