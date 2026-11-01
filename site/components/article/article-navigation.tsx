"use client";

import { useEffect } from "react";

/** One fragment-link contract for every article, including collapsed appendices. */
export function ArticleNavigation() {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>('[data-research-article]');
    if (!root) return;
    let frame = 0;
    const reveal = (hash: string) => {
      if (!hash || hash === '#') return;
      let id: string;
      try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
      const target = document.getElementById(id);
      if (!target || !root.contains(target)) return;
      for (let node: HTMLElement | null = target; node && node !== root; node = node.parentElement) {
        if (node instanceof HTMLDetailsElement) node.open = true;
      }
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        frame = requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
      });
    };
    const followHash = () => reveal(window.location.hash);
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
      if (!link || link.hasAttribute('download') || link.target === '_blank') return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== location.origin || url.pathname !== location.pathname || !url.hash) return;
      let id: string;
      try { id = decodeURIComponent(url.hash.slice(1)); } catch { return; }
      if (!root.contains(document.getElementById(id))) return;
      event.preventDefault();
      if (location.hash !== url.hash) history.pushState(null, '', url.hash);
      reveal(url.hash); // Also works when the same hash is clicked again after closing a disclosure.
    };
    root.addEventListener('click', onClick);
    window.addEventListener('hashchange', followHash);
    window.addEventListener('popstate', followHash);
    followHash();
    return () => {
      cancelAnimationFrame(frame);
      root.removeEventListener('click', onClick);
      window.removeEventListener('hashchange', followHash);
      window.removeEventListener('popstate', followHash);
    };
  }, []);
  return null;
}
