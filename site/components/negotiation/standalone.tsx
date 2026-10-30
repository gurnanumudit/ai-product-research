import React from 'react';
import {createRoot} from 'react-dom/client';
import heroImage from './negotiation-hero.json';
import {NegotiationArticle} from './article';
createRoot(document.getElementById('root')!).render(<NegotiationArticle standalone imageSrc={heroImage.src}/>);
