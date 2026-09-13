"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";

export function ArticleIndex({ entries }: { entries: { id: string; title: string; nested?: boolean }[] }) {
  const [active, setActive] = useState("introduction");
  useEffect(() => {
    let scheduled = false;
    const update = () => {
      scheduled = false;
      const target = entries.filter(entry => (document.getElementById(entry.id)?.getBoundingClientRect().top ?? Infinity) <= 160).at(-1);
      setActive(target?.id ?? entries[0].id);
    };
    const onScroll = () => { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } };
    window.addEventListener("scroll", onScroll, { passive: true });
    update();
    return () => window.removeEventListener("scroll", onScroll);
  }, [entries]);
  const links = <nav aria-label="Article sections">{entries.map(entry => <a key={entry.id} href={`#${entry.id}`} className={entry.nested ? styles.indexChild : undefined} aria-current={active === entry.id ? "location" : undefined}>{entry.title}</a>)}</nav>;
  return <>
    <aside className={styles.index}>{links}</aside>
    <details className={styles.mobileIndex}><summary>In this article</summary>{links}</details>
  </>;
}
