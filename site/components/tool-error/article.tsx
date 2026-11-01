"use client";

import { ArticleNavigation } from "@/components/article/article-navigation";
import { useEffect, useRef } from "react";
import content from "./content.json";
import { initializeArticle } from "./interactions";
import "./article.css";

export function ToolErrorArticle() {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (root.current) return initializeArticle(root.current);
  }, []);
  return <div data-research-article="" className="toolErrorArticle" ref={root}><ArticleNavigation /><div className="page" dangerouslySetInnerHTML={{ __html: content.html }} /></div>;
}
