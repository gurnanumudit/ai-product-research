"use client";

import { useEffect, useRef } from "react";
import "./exhibits.css";

/** Presentation-only controls. Original figures, scales, tables and notes remain in place. */
export function ExhibitEnhancements() {
  const marker = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const root = marker.current?.closest<HTMLElement>('[data-research-article]');
    const body = root?.querySelector<HTMLElement>('[data-article-body]');
    if (!root || !body) return;
    root.dataset.exhibitStandard = '';
    const cleanups: Array<() => void> = [];
    let closeExpanded: (() => void) | null = null;
    const listen = (node: EventTarget, type: string, handler: EventListener) => {
      node.addEventListener(type, handler);
      cleanups.push(() => node.removeEventListener(type, handler));
    };
    const button = (text: string, label: string) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.setAttribute('aria-label', label); return b;
    };
    const toolbar = (label: string) => {
      const bar = document.createElement('div'); bar.className = 'exhibitToolbar'; bar.dataset.exhibitUi = '';
      const name = document.createElement('span'); name.className = 'exhibitKind'; name.textContent = label; bar.append(name); return bar;
    };
    const expandable = (host: HTMLElement, bar: HTMLElement, name: string) => {
      const b = button('↗ Expand', `Expand ${name}`); b.className = 'exhibitExpand'; b.setAttribute('aria-expanded', 'false'); bar.append(b);
      let close: (() => void) | null = null;
      const toggle = () => {
        if (close) { close(); return; }
        closeExpanded?.();
        const previous = document.activeElement as HTMLElement | null;
        const oldOverflow = document.body.style.overflow;
        const oldRole = host.getAttribute('role'); const oldLabel = host.getAttribute('aria-label');
        const backdrop = document.createElement('div'); backdrop.className = 'exhibitBackdrop'; document.body.append(backdrop);
        // Keep the original nodes, captions and controls. No duplicated research data or lost event handlers.
        const hiddenSiblings: Array<[HTMLElement, boolean]> = [];
        for (let node: HTMLElement | null = host; node?.parentElement; node = node.parentElement) {
          for (const sibling of Array.from(node.parentElement.children)) {
            if (sibling !== node && sibling !== backdrop && sibling instanceof HTMLElement) {
              hiddenSiblings.push([sibling, sibling.inert]); sibling.inert = true;
            }
          }
        }
        document.body.style.overflow = 'hidden'; host.classList.add('exhibitExpanded');
        host.setAttribute('role', 'dialog'); host.setAttribute('aria-modal', 'true'); host.setAttribute('aria-label', name);
        b.textContent = 'Close ×'; b.setAttribute('aria-label', `Close ${name}`); b.setAttribute('aria-expanded', 'true');
        const onKey = (event: KeyboardEvent) => {
          if (event.key === 'Escape') { event.preventDefault(); close?.(); }
          if (event.key !== 'Tab') return;
          const focusable = Array.from(host.querySelectorAll<HTMLElement>('a[href],button,input,select,summary,[tabindex="0"]')).filter(el => el.getClientRects().length && !el.matches(':disabled'));
          const first = focusable[0], last = focusable.at(-1);
          if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
          else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        };
        close = () => {
          host.classList.remove('exhibitExpanded'); host.removeAttribute('aria-modal');
          if (oldRole === null) host.removeAttribute('role'); else host.setAttribute('role', oldRole);
          if (oldLabel === null) host.removeAttribute('aria-label'); else host.setAttribute('aria-label', oldLabel);
          b.textContent = '↗ Expand'; b.setAttribute('aria-label', `Expand ${name}`); b.setAttribute('aria-expanded', 'false');
          document.body.style.overflow = oldOverflow; backdrop.remove();
          hiddenSiblings.forEach(([node, value]) => { node.inert = value; });
          document.removeEventListener('keydown', onKey); close = null; closeExpanded = null; previous?.focus({ preventScroll: true });
        };
        closeExpanded = close; backdrop.addEventListener('click', close); document.addEventListener('keydown', onKey); b.focus({ preventScroll: true });
      };
      listen(b, 'click', toggle); cleanups.push(() => close?.());
    };
    const enhanceFigure = (figure: HTMLElement) => {
      if (figure.dataset.exhibitReady !== undefined) return;
      figure.dataset.exhibitReady = ''; figure.classList.add('standardExhibit');
      const title = figure.getAttribute('data-exhibit-title') || figure.querySelector('h3,svg title,caption')?.textContent?.trim() || 'figure';
      const bar = toolbar('Explore figure'); figure.prepend(bar); expandable(figure, bar, title);
      const panels = Array.from(figure.querySelectorAll<HTMLElement | SVGElement>('[data-exhibit-panel]'));
      let panelSelect: HTMLSelectElement | null = null;
      if (panels.length > 1) {
        const label = document.createElement('label'); label.textContent = 'View ';
        panelSelect = document.createElement('select'); panelSelect.setAttribute('aria-label', `Panel for ${title}`);
        panelSelect.add(new Option('All panels', 'all'));
        panels.forEach((panel, i) => panelSelect!.add(new Option(panel.getAttribute('data-exhibit-panel')!, String(i))));
        label.append(panelSelect); bar.insertBefore(label, bar.lastChild);
        listen(panelSelect, 'change', () => {
          panels.forEach((panel, i) => panel.classList.toggle('exhibitPanelHidden', panelSelect!.value !== 'all' && panelSelect!.value !== String(i)));
          figure.classList.toggle('exhibitSinglePanel', panelSelect!.value !== 'all');
          refreshOptions();
        });
      }
      const marks = Array.from(figure.querySelectorAll<HTMLElement | SVGElement>('[data-exhibit-value], svg g[data-model], svg circle:has(>title), svg rect:has(>title)'));
      const markText = (mark: Element) => mark.getAttribute('data-exhibit-value') || mark.querySelector(':scope > title')?.textContent || '';
      const valuePanel = document.createElement('div'); valuePanel.className = 'exhibitValue'; valuePanel.dataset.exhibitUi = '';
      valuePanel.setAttribute('role', 'status'); valuePanel.setAttribute('aria-live', 'polite'); valuePanel.textContent = 'Tap a plotted value or choose one to inspect. The chart scale stays fixed.';
      let valueSelect: HTMLSelectElement | null = null;
      const showValue = (mark: Element | null) => {
        marks.forEach(m => m.classList.toggle('exhibitMarkSelected', m === mark));
        const context = mark?.closest('[data-exhibit-panel]')?.getAttribute('data-exhibit-panel');
        valuePanel.textContent = mark ? `${context && !markText(mark).startsWith(context) ? context + ' · ' : ''}${markText(mark)}` : 'Tap a plotted value or choose one to inspect. The chart scale stays fixed.';
        if (valueSelect) valueSelect.value = mark ? String(marks.indexOf(mark as HTMLElement)) : '';
      };
      const refreshOptions = () => {
        if (!valueSelect) return;
        valueSelect.replaceChildren(new Option('Choose a value', ''));
        marks.forEach((mark, i) => {
          if (mark.closest('.exhibitPanelHidden')) return;
          const panel = mark.closest('[data-exhibit-panel]')?.getAttribute('data-exhibit-panel');
          valueSelect!.add(new Option(`${panel && !markText(mark).startsWith(panel) ? panel + ' · ' : ''}${markText(mark)}`, String(i)));
        });
        showValue(null);
      };
      if (marks.length) {
        const label = document.createElement('label'); label.textContent = 'Inspect ';
        valueSelect = document.createElement('select'); valueSelect.setAttribute('aria-label', `Value for ${title}`); label.append(valueSelect); bar.insertBefore(label, bar.lastChild);
        refreshOptions(); listen(valueSelect, 'change', () => showValue(valueSelect!.value === '' ? null : marks[Number(valueSelect!.value)]));
        marks.forEach(mark => {
          const oldTab = mark.getAttribute('tabindex'), oldLabel = mark.getAttribute('aria-label');
          mark.setAttribute('tabindex', '0'); mark.setAttribute('aria-label', markText(mark)); mark.classList.add('exhibitMark');
          listen(mark, 'click', () => showValue(mark)); listen(mark, 'focus', () => showValue(mark));
          listen(mark, 'keydown', ((e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showValue(mark); } }) as EventListener);
          cleanups.push(() => { mark.classList.remove('exhibitMark', 'exhibitMarkSelected'); if(oldTab===null)mark.removeAttribute('tabindex');else mark.setAttribute('tabindex',oldTab); if(oldLabel===null)mark.removeAttribute('aria-label');else mark.setAttribute('aria-label',oldLabel); });
        });
        const caption = figure.querySelector(':scope > figcaption'); figure.insertBefore(valuePanel, caption);
      }
      cleanups.push(() => { bar.remove(); valuePanel.remove(); delete figure.dataset.exhibitReady; figure.classList.remove('standardExhibit','exhibitSinglePanel'); panels.forEach(p=>p.classList.remove('exhibitPanelHidden')); });
    };
    const enhanceTable = (table: HTMLTableElement) => {
      if (table.dataset.exhibitReady !== undefined) return;
      table.dataset.exhibitReady = '';
      const host = document.createElement('div'); host.className = 'standardTable';
      const scroll = document.createElement('div'); scroll.className = 'exhibitTableScroll'; scroll.tabIndex = 0;
      const title = table.caption?.textContent?.trim() || table.closest('section,details')?.querySelector('summary,h2,h3')?.textContent?.trim() || 'table';
      scroll.setAttribute('role','region'); scroll.setAttribute('aria-label',title);
      table.before(host); host.append(scroll); scroll.append(table);
      const bar = toolbar('Explore table'); host.prepend(bar);
      if (!host.closest('figure')) expandable(host, bar, title);
      const rows = Array.from(table.tBodies).flatMap(b => Array.from(b.rows));
      // Do not split row groups or merged cells. Their context is part of the published information.
      const searchable = rows.length >= 6 && rows.every(r => Array.from(r.cells).every(c => c.rowSpan === 1 && c.colSpan === 1));
      if (searchable) {
        const label = document.createElement('label'); label.textContent = 'Find rows ';
        const input = document.createElement('input'); input.type = 'search'; input.placeholder = 'Model, method or value'; input.setAttribute('aria-label',`Find rows in ${title}`); label.append(input); bar.prepend(label);
        const status = document.createElement('span'); status.className = 'exhibitRowCount'; status.setAttribute('role','status'); bar.append(status);
        const reset = button('Reset','Show all rows'); bar.append(reset);
        const filter = () => { const term=input.value.trim().toLocaleLowerCase(); let count=0; rows.forEach(row=>{row.hidden=term!==''&&!row.textContent?.toLocaleLowerCase().includes(term);if(!row.hidden)count++;});status.textContent=`${count} of ${rows.length} rows`; };
        listen(input,'input',filter);listen(reset,'click',()=>{input.value='';filter();input.focus();});filter();
      }
      rows.forEach(row => { row.classList.add('exhibitTableRow'); });
      cleanups.push(()=>{rows.forEach(r=>{r.hidden=false;r.classList.remove('exhibitTableRow');});host.before(table);host.remove();delete table.dataset.exhibitReady;});
    };
    const scan = () => {
      body.querySelectorAll<HTMLElement>('figure:not([data-article-cover])').forEach(enhanceFigure);
      body.querySelectorAll<HTMLTableElement>('table').forEach(enhanceTable);
    };
    scan();
    let frame = 0;
    const observer = new MutationObserver(records => {
      if (!records.some(r=>Array.from(r.addedNodes).some(n=>n instanceof Element&&!n.closest('[data-exhibit-ui]')&&(n.matches('table,figure')||n.querySelector('table,figure'))))) return;
      cancelAnimationFrame(frame);frame=requestAnimationFrame(scan);
    });
    observer.observe(body,{childList:true,subtree:true});
    return () => { observer.disconnect();cancelAnimationFrame(frame);closeExpanded?.();cleanups.reverse().forEach(cleanup=>cleanup());delete root.dataset.exhibitStandard; };
  }, []);
  return <span ref={marker} hidden aria-hidden="true" />;
}
