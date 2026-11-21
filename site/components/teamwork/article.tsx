import {ArticleIndex} from '@/components/article/article-index';
import {ArticleNavigation} from '@/components/article/article-navigation';
import content from './content.json';
import './article.css';
const entries=[{id:'question',title:'The question'},{id:'design',title:'How we tested it'},{id:'results',title:'The result'},{id:'joining',title:'Combining the work'},{id:'cost',title:'Cost per success'},{id:'takeaway',title:'What we learned'},{id:'appendix',title:'Appendix (optional)'}];
export function TeamworkArticle(){return <div className="teamworkArticle" data-research-article=""><ArticleNavigation/><div dangerouslySetInnerHTML={{__html:content.header}}/><div data-article-layout=""><ArticleIndex entries={entries}><a href="/research-assets/teamwork/chart-data.json" download>Download chart data</a></ArticleIndex><main data-article-body="" dangerouslySetInnerHTML={{__html:content.body}}/></div><div dangerouslySetInnerHTML={{__html:content.footer}}/></div>;}
