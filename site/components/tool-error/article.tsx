"use client";

import { useEffect, useRef } from "react";
import content from "./content.json";
import { initializeArticle } from "./interactions";
import "./article.css";

export function ToolErrorArticle() {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (root.current) return initializeArticle(root.current);
  }, []);
  return <div className="toolErrorArticle" ref={root}><div className="page" dangerouslySetInnerHTML={{ __html: content.html }} /></div>;
}
