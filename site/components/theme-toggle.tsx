"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

const storageKey = "research-site-theme";

function currentTheme(): Theme {
  if (typeof document === "undefined") return "light";
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute(
    "content",
    theme === "dark" ? "#05060a" : "#f7f5ef",
  );
}

function ThemeIcon({ theme }: { theme: Theme }) {
  if (theme === "dark") {
    return (
      <svg viewBox="0 0 24 24" role="presentation">
        <circle cx="12" cy="12" r="3.5" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" role="presentation">
      <path d="M20.25 15.25A8.5 8.5 0 0 1 8.75 3.75a8.5 8.5 0 1 0 11.5 11.5Z" />
    </svg>
  );
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    setTheme(currentTheme());
  }, []);

  const nextTheme: Theme = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      className="themeToggle"
      aria-label={`Switch to ${nextTheme} mode`}
      aria-pressed={theme === "dark"}
      title={`Switch to ${nextTheme} mode`}
      onClick={() => {
        applyTheme(nextTheme);
        window.localStorage.setItem(storageKey, nextTheme);
        setTheme(nextTheme);
      }}
    >
      <span className="themeToggleIcon" aria-hidden="true">
        <ThemeIcon theme={theme} />
      </span>
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
