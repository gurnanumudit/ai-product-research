import type { ReactNode } from "react";

function normalizeHref(href: string) {
  const article = href.match(/\.\.\/articles\/([^/]+)\.md/);
  if (article) {
    const aliases: Record<string, string> = {
      "positive-evidence-can-make-review-less-safe": "positive-ai-evidence-can-make-review-less-safe",
    };
    return `/research/articles/${aliases[article[1]] ?? article[1]}`;
  }
  const experiment = href.match(/\.\.\/experiments\/([^/]+)\.md/);
  if (experiment) return `/research/experiments/${experiment[1]}`;
  if (/^(?:\.\.\/){2,}reports\//.test(href)) return "/research/methods#technical-records";
  return href;
}

function inline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`|\*([^*]+)\*)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  let index = 0;
  while ((match = pattern.exec(text))) {
    if (match.index > cursor) nodes.push(text.slice(cursor, match.index));
    if (match[2] && match[3]) {
      const href = normalizeHref(match[3]);
      const external = /^https?:\/\//.test(href);
      nodes.push(external
        ? <a key={`${keyPrefix}-a-${index}`} href={href} target="_blank" rel="noreferrer">{match[2]} ↗</a>
        : <a key={`${keyPrefix}-a-${index}`} href={href}>{match[2]}</a>);
    } else if (match[4]) nodes.push(<strong key={`${keyPrefix}-b-${index}`}>{match[4]}</strong>);
    else if (match[5]) nodes.push(<code key={`${keyPrefix}-c-${index}`}>{match[5]}</code>);
    else if (match[6]) nodes.push(<em key={`${keyPrefix}-i-${index}`}>{match[6]}</em>);
    cursor = pattern.lastIndex;
    index += 1;
  }
  if (cursor < text.length) nodes.push(text.slice(cursor));
  return nodes;
}

function isTableRule(line: string) {
  return /^\|?\s*:?-{3,}/.test(line) && line.includes("|");
}

function cells(line: string) {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((value) => value.trim());
}

function headingId(label: string) {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

type MarkdownList = {
  ordered: boolean;
  start: number;
  items: Array<{ text: string; children: MarkdownList[] }>;
};

function listItem(line: string) {
  const match = line.match(/^(\s*)(?:(\d+)\.|([-*]))\s+(.+)$/);
  if (!match) return null;
  return {
    indent: match[1].replace(/\t/g, "    ").length,
    ordered: Boolean(match[2]),
    start: match[2] ? Number(match[2]) : 1,
    text: match[4],
  };
}

function parseList(lines: string[], startIndex: number): { list: MarkdownList; nextIndex: number } | null {
  const first = listItem(lines[startIndex]);
  if (!first) return null;

  const list: MarkdownList = { ordered: first.ordered, start: first.start, items: [] };
  let index = startIndex;

  while (index < lines.length) {
    const current = listItem(lines[index]);
    if (!current || current.indent < first.indent) break;
    if (current.indent > first.indent) {
      const parent = list.items.at(-1);
      const nested = parent ? parseList(lines, index) : null;
      if (!parent || !nested) break;
      parent.children.push(nested.list);
      index = nested.nextIndex;
      continue;
    }
    if (current.ordered !== list.ordered) break;

    list.items.push({ text: current.text, children: [] });
    index += 1;
  }

  return { list, nextIndex: index };
}

function renderList(list: MarkdownList, keyPrefix: string): ReactNode {
  const items = list.items.map((item, itemIndex) => (
    <li key={`${keyPrefix}-item-${itemIndex}`}>
      {inline(item.text, `${keyPrefix}-text-${itemIndex}`)}
      {item.children.map((child, childIndex) => renderList(child, `${keyPrefix}-nested-${itemIndex}-${childIndex}`))}
    </li>
  ));

  return list.ordered
    ? <ol start={list.start === 1 ? undefined : list.start} key={keyPrefix}>{items}</ol>
    : <ul key={keyPrefix}>{items}</ul>;
}

function displayLines(markdown: string, kind: "article" | "experiment") {
  const sourceLines = markdown.replace(/\r/g, "").split("\n");
  if (kind === "experiment") return sourceLines;
  const visible: string[] = [];
  let index = 0;
  while (index < sourceLines.length) {
    const line = sourceLines[index];
    if (line.trim() === "## Evidence behind this article") {
      index += 1;
      while (index < sourceLines.length && !sourceLines[index].startsWith("## ")) index += 1;
      continue;
    }
    if (line.trim() === "## External literature") {
      const section = [line];
      index += 1;
      while (index < sourceLines.length && !sourceLines[index].startsWith("## ")) section.push(sourceLines[index++]);
      if (section.some((value) => /https?:\/\//.test(value))) visible.push(...section);
      continue;
    }
    visible.push(line);
    index += 1;
  }
  return visible;
}

export function articleSectionHeadings(markdown: string) {
  return displayLines(markdown, "article")
    .filter((line) => line.startsWith("## "))
    .map((line) => ({ label: line.slice(3).trim(), id: headingId(line.slice(3).trim()) }));
}

export function MarkdownContent({ markdown, kind = "article", beforeHeading = {} }: { markdown: string; kind?: "article" | "experiment"; beforeHeading?: Record<string, ReactNode> }) {
  const sourceLines = displayLines(markdown, kind);
  const lines = sourceLines.filter((line, index) => {
    if (index === 0 && line.startsWith("# ")) return false;
    if (/^(Type|Deck|Status):/.test(line)) return false;
    return true;
  });
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line || line === "---") { i += 1; continue; }
    if (line.startsWith("## ")) {
      const id = headingId(line.slice(3));
      if (beforeHeading[id]) blocks.push(<div className="proseVisualBreak" key={`visual-${id}`}>{beforeHeading[id]}</div>);
      blocks.push(<h2 id={id} key={`h2-${key++}`}>{inline(line.slice(3), `h2-${key}`)}</h2>);
      i += 1; continue;
    }
    if (line.startsWith("### ")) {
      blocks.push(<h3 key={`h3-${key++}`}>{inline(line.slice(4), `h3-${key}`)}</h3>);
      i += 1; continue;
    }
    if (line.startsWith("> ")) {
      const quote: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quote.push(lines[i].trim().replace(/^>\s?/, "")); i += 1;
      }
      blocks.push(<blockquote key={`q-${key++}`}>{inline(quote.join(" "), `q-${key}`)}</blockquote>);
      continue;
    }
    if (listItem(lines[i])) {
      const parsed = parseList(lines, i);
      if (!parsed) { i += 1; continue; }
      blocks.push(renderList(parsed.list, `list-${key++}`));
      i = parsed.nextIndex;
      continue;
    }
    if (line.includes("|") && i + 1 < lines.length && isTableRule(lines[i + 1].trim())) {
      const headers = cells(line); i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().includes("|") && lines[i].trim()) { rows.push(cells(lines[i])); i += 1; }
      blocks.push(
        <div className="tableWrap" role="region" aria-label="Scrollable data table" key={`t-${key++}`}>
          <table><thead><tr>{headers.map((cell, idx) => <th key={idx} scope="col">{inline(cell, `th-${key}-${idx}`)}</th>)}</tr></thead>
          <tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, idx) => <td key={idx}>{inline(cell, `td-${key}-${rowIndex}-${idx}`)}</td>)}</tr>)}</tbody></table>
        </div>,
      );
      continue;
    }
    const paragraph = [line]; i += 1;
    while (i < lines.length) {
      const next = lines[i].trim();
      if (!next || /^(## |### |> |[-*]\s+|\d+\.\s+)/.test(next)) break;
      if (next.includes("|") && i + 1 < lines.length && isTableRule(lines[i + 1].trim())) break;
      paragraph.push(next); i += 1;
    }
    blocks.push(<p className={kind === "experiment" && key === 0 ? "experimentLead" : undefined} key={`p-${key++}`}>{inline(paragraph.join(" "), `p-${key}`)}</p>);
  }

  return <div className={`prose prose-${kind}`}>{blocks}</div>;
}
