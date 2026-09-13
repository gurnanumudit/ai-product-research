import { headers } from "next/headers";

const LOCAL_FALLBACK = "http://localhost:3000";

function firstHeaderValue(value: string | null) {
  return value?.split(",", 1)[0]?.trim() || null;
}

function fallbackSiteUrl() {
  const configured = process.env.NEXT_PUBLIC_SITE_URL;
  if (!configured) return new URL(LOCAL_FALLBACK);

  try {
    return new URL(configured);
  } catch {
    return new URL(LOCAL_FALLBACK);
  }
}

/** Build absolute social URLs from the host that is actually serving the page. */
export async function requestSiteUrl() {
  const requestHeaders = await headers();
  const host =
    firstHeaderValue(requestHeaders.get("x-forwarded-host")) ??
    firstHeaderValue(requestHeaders.get("host"));
  if (!host || host.includes("/") || /\s/.test(host)) return fallbackSiteUrl();

  const forwardedProtocol = firstHeaderValue(requestHeaders.get("x-forwarded-proto"));
  const protocol =
    forwardedProtocol === "http" || forwardedProtocol === "https"
      ? forwardedProtocol
      : /^(localhost|127\.0\.0\.1)(:\d+)?$/i.test(host)
        ? "http"
        : "https";

  try {
    return new URL(`${protocol}://${host}`);
  } catch {
    return fallbackSiteUrl();
  }
}

export async function socialPreviewUrl() {
  return new URL("/og-v2.png", await requestSiteUrl());
}
