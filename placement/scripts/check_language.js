// Evaluate in Playwright or preview_evaluate after / or /map is ready.
// Run twice with language=tr in storage and ?lang=tr on initial navigation as well.
(async () => {
 const mapPage=location.pathname==='/map';
 const identity=await (await fetch('/api/brand')).json();
 const text=document.body.innerText;
 const expected=mapPage?'Occluded in FOV':'Watch the forest.';
 if(document.documentElement.lang!=='en')throw Error('Placement must always use English');
 if(document.querySelector('.language'))throw Error('Unexpected language control');
 if(!text.includes(expected))throw Error('Missing rendered English text: '+expected);
 if(text.includes('Türkçe')||text.includes('Duman şüphesi'))throw Error('Unexpected Turkish text');
 if(document.querySelector('[data-brand-name]').textContent!==identity.name)throw Error('Brand config not rendered');
 if(!document.title.startsWith(identity.name+' · '))throw Error('Brand title not rendered');
 if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal page overflow');
 const external=performance.getEntriesByType('resource').filter(r=>!r.name.startsWith(location.origin));
 if(external.length)throw Error('Unexpected external resources');
 return {page:location.pathname,width:innerWidth,language:'en',languageControl:false,brand:true,overflow:false,externalResources:0};
})()
