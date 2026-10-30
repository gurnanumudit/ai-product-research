// Progressive enhancement: fragment links reveal their collapsed appendix target.
// Native disclosure controls remain usable without JavaScript.
(() => {
  function reveal(hash, scroll) {
    if (!hash || hash === '#') return;
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !target.closest('article')) return;
    let parent = target;
    while (parent) {
      if (parent.tagName === 'DETAILS') parent.open = true;
      parent = parent.parentElement;
    }
    if (scroll) requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
  }
  document.addEventListener('click', event => {
    const link = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
    if (link && !event.defaultPrevented && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      reveal(link.getAttribute('href'), false);
    }
  }, true);
  window.addEventListener('hashchange', () => reveal(location.hash, true));
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => reveal(location.hash, true), { once: true });
  } else reveal(location.hash, true);
})();
