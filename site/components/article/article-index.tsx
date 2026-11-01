"use client";

import { useEffect, useState, type ReactNode } from "react";

export function ArticleIndex({ entries, children }: { entries: { id: string; title: string; nested?: boolean }[]; children?: ReactNode }) {
  const [active, setActive] = useState(entries[0]?.id);
  useEffect(() => {
    let frame = 0;
    const update = () => {
      const target = entries.filter(entry => (document.getElementById(entry.id)?.getBoundingClientRect().top ?? Infinity) <= 160).at(-1);
      setActive(target?.id ?? entries[0]?.id);
    };
    const onScroll = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); };
    window.addEventListener("scroll", onScroll, { passive: true });
    update();
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", onScroll); };
  }, [entries]);
  return <aside data-article-index="" aria-label="In this article">
    <span data-index-label="">In this article</span>
    <nav aria-label="Article sections">{entries.map(entry => <a key={entry.id} href={`#${entry.id}`} data-index-nested={entry.nested || undefined} aria-current={active === entry.id ? "location" : undefined}>{entry.title}</a>)}</nav>
    {children}
  </aside>;
}
