import { publishedStudies } from "@/content/research-catalog";
import { publicOrigin } from "@/lib/research-release";

function escapeXml(value: string) {
  return value.replace(/[<>&'\"]/g, (character) => ({
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    "'": "&apos;",
    "\"": "&quot;",
  })[character]!);
}

export function GET() {
  const items = [...publishedStudies]
    .sort((a, b) => b.iso.localeCompare(a.iso))
    .map((study) => `
      <item>
        <title>${escapeXml(study.title)}</title>
        <link>${publicOrigin}${study.path}</link>
        <guid isPermaLink="true">${publicOrigin}${study.path}</guid>
        <pubDate>${new Date(`${study.iso}T12:00:00Z`).toUTCString()}</pubDate>
        <description>${escapeXml(study.summary)}</description>
      </item>`)
    .join("");

  const body = `<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Mudit Gurnani | Research</title>
        <link>${publicOrigin}</link>
        <description>Independent research on AI cost, success, decision quality and agent behavior.</description>
        <language>en-us</language>
        <lastBuildDate>${new Date("2026-11-04T12:00:00Z").toUTCString()}</lastBuildDate>
        ${items}
      </channel>
    </rss>`;

  return new Response(body, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}
