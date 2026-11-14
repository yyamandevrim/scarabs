'use strict';
const $=id=>document.getElementById(id),M=PlacementMetrics,C=PlacementCharts;
const lang=()=>'en';
const tr=en=>en;
function localized(el,en,turkish){el.setAttribute('data-localized','');el.textContent=tr(en,turkish);return el;}
const fmt=(value,digits=0)=>M.number(value,lang(),digits);
const area=(value,resolution)=>M.headline(value,resolution,lang());
let candidates=[],results=[null,null],selected=0,map=null,layers=null,overlay=null,otherOverlays=[],priorityLayer=null,drawing=false,drawPoints=[],priority=null,timer=null,busy=false,pending=new Set(),scheduled=new Set();
let scenario='canopy_smoke',dataInfo=null,dirty=new Set([0,1]),requestErrors=new Map(),lastError='',ready=false;
const letters='AB';
const camName=i=>'Camera '+(i+1);
const siteName=c=>c?.name?.split(' · ').pop()||'—';
let mapRenderRevision=0,reconnectTimer=null,reconnectAttempt=0,reconnecting=false,configFingerprint=null;
const overlaysBySite=new Map(),heightSamples=new Map();
let heightLoading=false,analysisTransport=Promise.resolve();
const token=name=>getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const scenarioNames={canopy_smoke:['smoke + canopy','duman + taç'],canopy_ground:['ground + canopy','zemin + taç'],bare_smoke:['smoke / bare terrain','duman / çıplak arazi'],bare_ground:['ground / bare terrain','zemin / çıplak arazi']};
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
function addText(parent,tag,text,cls){const e=el(tag,cls,text);parent.append(e);return e;}

// --- Shell state -------------------------------------------------------------
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function banner(title,text,retry){$('banner').hidden=!title;$('banner-title').textContent=title||'';$('banner-text').textContent=text||'';$('retry').hidden=!retry;}
function state(text,error=false,turkish){const e=$('result-state');if(turkish)localized(e,text,turkish);else{e.removeAttribute('data-localized');e.textContent=text;}e.classList.toggle('error',error);}
function setBusy(value){for(const id of ['result-summary','details-results'])$(id).setAttribute('aria-busy',String(value));$('analyze').disabled=value;$('analyze').setAttribute('aria-busy',String(value));}
function markStale(indices=[selected]){indices.forEach(i=>{dirty.add(i);requestErrors.delete(i);});lastError=[...requestErrors.values()].at(-1)||'';document.body.classList.add('stale');if(!requestErrors.size&&!reconnectAttempt)banner();if(indices.some(i=>results[i]))state('Updating · results are for previous settings.');renderSummary();}
function later(delay=600,indices=[selected]){markStale(indices);clearTimeout(timer);
 // Validate while the controls still belong to the edited site. An invalid edit
 // must not cancel valid work already scheduled for the other site.
 const valid=validateControls();if(!valid){scheduled.delete(selected);pending.delete(selected);lastError='Check the highlighted settings.';status(lastError,true);renderSummary();}
 indices.filter(i=>i!==selected||valid).forEach(i=>scheduled.add(i));if(scheduled.size)timer=setTimeout(()=>run(false,[]),delay);}

// --- Controls ----------------------------------------------------------------
function readControls(){if(!candidates.length)return;const c=candidates[selected];c.lat=+$('lat').value;c.lon=+$('lon').value;c.max_range=+$('max-range').value*1000;c.smoke_height=+$('smoke-height').value;c.cameras.forEach(cam=>{cam.tilt=+$('tilt').value;cam.vfov=+$('vfov').value});}
function showControls(){const c=candidates[selected];if(!c)return;$('lat').value=c.lat.toFixed(5);$('lon').value=c.lon.toFixed(5);$('height').value=String(c.height);$('resolution').value=c.resolution;$('max-range').value=c.max_range/1000;$('smoke-height').value=c.smoke_height;$('tilt').value=c.cameras[0].tilt;$('vfov').value=c.cameras[0].vfov;$('settings-site').textContent='Editing '+letters[selected]+' · '+siteName(c);$('height-site').textContent='Both sites';}
function selectSite(i,reveal=true){if(i===selected||!candidates[i])return;readControls();selected=i;showControls();render();if(reveal)revealSite(i);}

// --- Headline metric: total visible forest, or priority forest while a polygon is active.
const usePriority=()=>Boolean(priority);
function headlineValue(r){return usePriority()?M.priorityValue(r,scenario):r?.metrics?.[scenario]?.visible_forest_ha;}
function renderSummary(){
 const priorityMode=usePriority();
 localized($('result-title'),(priorityMode?'Visible priority forest · ':'Visible forest · ')+scenarioNames[scenario][0],(priorityMode?'Görünür öncelikli orman · ':'Görünür orman · ')+scenarioNames[scenario][1]);
 const figures=$('headline-figures');figures.replaceChildren();
 candidates.forEach((c,i)=>{const r=results[i],m=r?.metrics?.[scenario],block=el('button','headline-site'+(i===selected?' selected':'')+(r&&dirty.has(i)?' stale':''));
  block.type='button';block.setAttribute('aria-pressed',String(i===selected));block.setAttribute('aria-label','Select '+letters[i]+' · '+siteName(c));block.addEventListener('click',()=>selectSite(i));const name=el('span','headline-name');name.append(el('span','cand-letter mono',letters[i]),document.createTextNode(siteName(c)));block.append(name);
  const shown=r?area(headlineValue(r),r.resolution_m):'—',n=addText(block,'div',shown,'headline-value'+(shown==='—'?' missing':''));if(shown!=='—')addText(n,'small',' ha');
  if(r)localized(addText(block,'p','','headline-sub'),`${fmt(r.input.height)} m · 360°`,`${fmt(r.input.height)} m · 360°`);else localized(addText(block,'p','','headline-sub'),'Not computed','Hesaplanmadı');
  if(r&&priorityMode&&M.valid(m?.visible_forest_ha))localized(addText(block,'p','','headline-sub'),`of ${area(m.visible_forest_ha,r.resolution_m)} ha visible forest in total`,`toplam görünür orman ${area(m.visible_forest_ha,r.resolution_m)} ha`);
  if(r&&M.valid(M.share(m)))localized(addText(block,'p','','headline-sub'),`${M.percent(M.share(m),'en')} of the view is water`,`Görülen alanda su payı: ${M.percent(M.share(m),'tr')}`);
  figures.append(block)});
 const values=results.map(headlineValue),comparable=results.every(Boolean)&&!dirty.size&&results[0].input.height===results[1].input.height&&results[0].resolution_m===results[1].resolution_m;
 if(!comparable&&results.some(Boolean))$('verdict').textContent='Updating the comparison…';
 else if(values.every(M.valid)){const winner=values[0]>=values[1]?0:1,other=1-winner,high=values[winner],low=values[other],what=priorityMode?['visible priority forest','görünür öncelikli orman']:['visible forest','görünür orman'];
  localized($('verdict'),high===low?`Both sites show the same ${what[0]}.`:low>0?`${siteName(candidates[winner])} shows ${fmt(high/low,1)}× the ${what[0]}.`:`${siteName(candidates[winner])} shows more ${what[0]}.`,high===low?`İki konumda da aynı ${what[1]} görünüyor.`:low>0?`${siteName(candidates[winner])} konumunda ${fmt(high/low,1)} kat daha fazla ${what[1]} görünüyor.`:`${siteName(candidates[winner])} konumunda daha fazla ${what[1]} görünüyor.`);
 }else localized($('verdict'),busy&&!lastError?'The comparison appears when both sites are calculated.':'No comparison yet. Recalculate both sites to compare.',busy&&!lastError?'Karşılaştırma iki konum da hesaplandığında görünür.':'Henüz karşılaştırma yok. Karşılaştırmak için iki konumu yeniden hesaplayın.');
 const smoke=r=>r?.metrics?.canopy_smoke,ranked=comparable?[0,1].filter(i=>M.valid(smoke(results[i])?.visible_forest_ha)).sort((a,b)=>(priorityMode?(smoke(results[b]).priority_visible_ha??-Infinity)-(smoke(results[a]).priority_visible_ha??-Infinity):0)||smoke(results[b]).visible_forest_ha-smoke(results[a]).visible_forest_ha):[];
 if(ranked.length===2){const order=ranked.map((i,k)=>`${k+1} ${siteName(candidates[i])}`).join(', ');localized($('ranking'),`Ranking by ${priorityMode?'visible priority forest':'total visible forest'} (smoke-target scenario): ${order}`,`Sıralama, ${priorityMode?'görünür öncelikli orman':'toplam görünür orman'} (duman hedefi senaryosu): ${order}`);}else $('ranking').textContent='';
 overlaysBySite.forEach((layer,i)=>layer.setOpacity(dirty.has(i)?.3:i===selected?.85:.45));
 const stale=[...dirty].some(i=>results[i]),missing=[0,1].filter(i=>!results[i]).map(i=>siteName(candidates[i])).join(', ');document.body.classList.toggle('stale',stale);
 if(lastError)state(lastError+(results.some(Boolean)?' Results are for previous settings.':''),true);else if(stale)state('Updating · showing previous results.');else if(missing)state(busy?`Calculating ${missing}…`:'— means not computed. Recalculate both sites to begin.',false,busy?`${missing} hesaplanıyor…`:'— hesaplanmadı demektir. Başlamak için iki konumu yeniden hesaplayın.');else state('');

}

// --- Charts ------------------------------------------------------------------
function renderAccounting(){
 const box=$('accounting');box.replaceChildren();const rows=results.map((r,i)=>({i,r,a:r?C.accounting(r.metrics?.[scenario],M.round,M.blind,r.resolution_m):null}));const max=Math.max(1,...rows.map(x=>x.a?.total).filter(M.valid));
 rows.forEach(({i,r,a})=>{const row=el('div','acc-row'+(i===selected?' selected':''));const head=el('div','acc-head');head.append(el('span','cand-letter mono',letters[i]),el('span','acc-name',siteName(candidates[i])),el('span','acc-total mono',a?fmt(a.total):'—'));row.append(head);
  const bar=el('div','acc-bar');if(a){for(const [key,cls] of [['visible','visible'],['occluded','occluded'],['outside','outside']]){const seg=el('i',cls);seg.style.width=(a[key]/max*100)+'%';seg.title=key;bar.append(seg);}}else bar.classList.add('empty');row.append(bar);
  const legend=el('div','acc-values');if(a){for(const [key,en,turkish] of [['visible','Visible','Görünür'],['occluded','Occluded','Perdelenmiş'],['outside','Vertical blind area','Görüş dışında']]){if(a[key]===0)continue;const s=el('span');s.append(el('i','sw '+key));localized(s.appendChild(el('span')),`${en} ${fmt(a[key])}`,`${turkish} ${fmt(a[key])}`);legend.append(s);}}else localized(legend,r?'Split not available':'Not computed',r?'Ayrım yok':'Hesaplanmadı');row.append(legend);box.append(row)});
 localized(addText(box,'p','','small'),'Forest in range · visible and unseen','Menzil diski içindeki orman. Toplam = görünür + görüş içinde perdelenmiş + görüş dışında.');
}
function renderCameras(){
 const result=results[selected],box=$('camera-breakdown');box.replaceChildren();
 $('camera-context').textContent=letters[selected]+' · '+siteName(candidates[selected]);
 const metrics=result?.metrics?.[scenario],total=metrics?.visible_forest_ha;
 for(let i=0;i<3;i++){
  const value=result?.camera_breakdown?.[i]?.metrics?.[scenario]?.visible_forest_ha;
  const row=el('div','camera-result'),head=el('div','camera-result-head');
  const camera=result?.input?.cameras?.[i],label=camName(i)+(camera?' · '+fmt((result.input.heading+camera.yaw)%360)+'°':'');
  head.append(el('span','',label),el('span','mono',M.valid(value)?area(value,result.resolution_m)+' ha':'—'));
  row.append(head);const bar=el('div','camera-result-bar'),fill=el('i','visible');
  fill.style.width=(M.valid(value)&&total>0?100*value/total:0)+'%';bar.append(fill);row.append(bar);box.append(row);
 }
 addText(box,'p','Share of this site’s visible forest · simulated ha','small');
}

// --- Table and notes -----------------------------------------------------------
function appendRow(body,label,unit,values,cls=''){
 // Hide only measured values that round to zero at both sites. Missing stays “—”.
 if(values.every(value=>value==='0'))return;
 const row=el('tr',cls),heading=el('th','',label);heading.scope='row';if(unit)heading.append(el('small','metric-unit',' · '+unit));row.append(heading);
 values.forEach(value=>{const td=el('td','',value);if(value==='—')td.title='Not computed';row.append(td)});body.append(row);
}
function renderTable(){
 for(const id of ['comparison','more-comparison']){const headers=$(id).querySelectorAll('thead th');candidates.forEach((c,i)=>headers[i+1].textContent=letters[i]+' · '+siteName(c));$(id).querySelector('tbody').replaceChildren();}
 const body=$('comparison').querySelector('tbody'),more=$('more-comparison').querySelector('tbody');
 const metrics=results.map(r=>r?.metrics?.[scenario]),res=results.map(r=>r?.resolution_m),split=metrics.map((m,i)=>M.blind(m,res[i])),values=key=>metrics.map((m,i)=>fmt(M.round(m?.[key],res[i]))),other=key=>results.map(r=>fmt(M.round(key(r),r?.resolution_m)));
 $('precision').textContent=res.includes(120)?'Quick figures rounded to 10 ha; detailed to whole hectares.':'Rounded to whole hectares.';
 appendRow(body,'Visible forest','ha',values('visible_forest_ha'),'main-metric');
 appendRow(body,'Unseen forest','ha',split.map(s=>fmt(s.total)));
 appendRow(body,'Water in view','ha',values('water_view_ha'));
 appendRow(body,'Water share','%',metrics.map(m=>fmt(M.share(m))));
 appendRow(more,'Vertical blind area','ha',split.map(s=>fmt(s.outside)));
 appendRow(more,'Occluded','ha',split.map(s=>fmt(s.occluded)));
 if(usePriority())appendRow(more,'Visible priority forest','ha',other(r=>M.priorityValue(r,scenario)));
 appendRow(more,'Bare terrain · ground','ha',other(r=>r?.metrics?.bare_ground?.visible_forest_ha));
 appendRow(more,'Canopy · ground','ha',other(r=>r?.metrics?.canopy_ground?.visible_forest_ha));
 for(let i=0;i<3;i++)appendRow(more,camName(i),'ha',other(r=>r?.camera_breakdown?.[i]?.metrics?.[scenario]?.visible_forest_ha));
}

// Hide secondary place labels where they would collide with camera/site labels.
function arrangeLabels(){
 const obstacles=[...document.querySelectorAll('.sector-label,.candidate-label')].map(e=>e.getBoundingClientRect());
 document.querySelectorAll('.map-label').forEach(e=>{e.style.visibility='visible';const b=e.getBoundingClientRect();if(obstacles.some(a=>b.left<a.right+4&&b.right>a.left-4&&b.top<a.bottom+4&&b.bottom>a.top-4))e.style.visibility='hidden';});
}
// --- Map -----------------------------------------------------------------------
function refreshLegend(){
 if(!map)return;
 const metric=results[selected]?.metrics?.[scenario];
 $('legend-occluded').hidden=!(metric?.occluded_forest_ha>0);
 $('legend-outside').hidden=!(metric?.outside_fov_forest_ha>0);
 $('legend-other').hidden=!results.some((r,i)=>r&&i!==selected&&map.getBounds().contains(L.latLng(r.input.lat,r.input.lon)));
}
function offset(lat,lon,bearing,metres){const b=bearing*Math.PI/180;return [lat+metres*Math.cos(b)/111320,lon+metres*Math.sin(b)/(111320*Math.cos(lat*Math.PI/180))];}
function renderMap(){
 if(!map||!layers)return;layers.markers.clearLayers();layers.sectors.clearLayers();if(overlay){map.removeLayer(overlay);overlay=null;}otherOverlays.forEach(layer=>map.removeLayer(layer));otherOverlays=[];overlaysBySite.clear();
 const revision=++mapRenderRevision,result=results[selected];
 // One complete secondary perimeter; no camera seams or competing data raster.
 results.forEach((r,index)=>{if(!r||index===selected)return;
  const footprints=r.sectors.map(s=>s.footprints[scenario]);
  for(let span=0;span<footprints[0].polygons.length;span++){
   const perimeter=footprints.flatMap(f=>{const points=f.polygons[span];return points.slice(0,points.length/2)});
   L.polygon(perimeter,{color:token('--text-2'),weight:1.25,opacity:.6,fillOpacity:0,interactive:false,className:'other-footprint'}).addTo(layers.sectors);
  }
 });
 refreshLegend();
 const rgb=value=>value.match(/[a-f0-9]{2}/gi).map(v=>parseInt(v,16));
 const source=Object.fromEntries(['visible','water'].map(k=>[k,rgb(token('--map-'+k))]));
 const display={visible:rgb(token('--display-visible')),water:rgb(token('--display-water'))};
 results.forEach((r,i)=>{const image=r?.images?.[scenario];if(!image)return;
  MapDisplay.image(image.url,source,display).then(url=>{if(revision!==mapRenderRevision)return;
   const layer=L.imageOverlay(url,image.bounds,{opacity:dirty.has(i)?.3:i===selected?.85:.45,interactive:false,zIndex:i===selected?2:1,className:i===selected?'coverage-map':'other-coverage-map'}).addTo(map);overlaysBySite.set(i,layer);if(i===selected)overlay=layer;else otherOverlays.push(layer);
  }).catch(()=>{if(revision!==mapRenderRevision)return;requestErrors.set(i,'Refreshing map coverage…');dirty.add(i);scheduleReconnect();});
 });
 if(result){
  const input=result.input;
  result.sectors?.forEach((s,i)=>{L.polygon(s.footprints[scenario].polygons,{color:token('--map-sector'),weight:1.5,opacity:.95,fillOpacity:0,interactive:false,className:'camera-footprint'}).addTo(layers.sectors);
   const cam=input.cameras[i],radii=s.footprints[scenario].radii_m[0];if(!radii)return;
   let at=offset(input.lat,input.lon,input.heading+cam.yaw,radii[0]+(radii[1]-radii[0])*.8);
   if(matchMedia('(max-width:760px)').matches){const point=map.latLngToContainerPoint(at),size=map.getSize();at=map.containerPointToLatLng(L.point(Math.max(38,Math.min(size.x-38,point.x)),Math.max(24,Math.min(size.y-24,point.y))));}
   const label=el('span','sector-label',camName(i));
   L.marker(at,{interactive:false,keyboard:false,icon:L.divIcon({className:'sector-icon',html:label.outerHTML,iconSize:null})}).addTo(layers.sectors)});
 }
 candidates.forEach((c,i)=>{if(!Number.isFinite(c.lat)||!Number.isFinite(c.lon))return;const marker=L.circleMarker([c.lat,c.lon],{radius:i===selected?7:5,color:token('--bg-0'),weight:2,fillColor:i===selected?token('--text'):token('--text-2'),fillOpacity:1}).addTo(layers.markers);
  marker.bindTooltip(matchMedia('(max-width:760px)').matches?letters[i]:letters[i]+' · '+siteName(c),{permanent:true,direction:matchMedia('(max-width:760px)').matches?(map.latLngToContainerPoint([c.lat,c.lon]).x>map.getSize().x/2?'left':'right'):'top',offset:matchMedia('(max-width:760px)').matches?[map.latLngToContainerPoint([c.lat,c.lon]).x>map.getSize().x/2?-10:10,0]:[0,-12],className:'candidate-label'+(i===selected?' selected':'')}).on('click',()=>selectSite(i,false))});
 arrangeLabels();
}
function revealSite(i){if(!map)return;const c=candidates[i];if(!Number.isFinite(c.lat))return;const bounds=L.latLng(c.lat,c.lon).toBounds(2*c.max_range);if(!map.getBounds().contains(bounds))map.fitBounds(bounds,{padding:[24,24],maxZoom:11});}
function render(){renderMap();renderSummary();renderAccounting();renderCameras();renderTable();renderHeightComparison();}

// --- Requests ------------------------------------------------------------------
function validateControls(){let valid=true;for(const id of ['lat','lon']){const input=$(id),bad=!input.value||!input.checkValidity();input.setAttribute('aria-invalid',String(bad));$(id+'-error').textContent=bad?(id==='lat'?'Latitude must be between 59° and 62°.':'Longitude must be between 23° and 27°.'):'';if(bad)valid=false;}for(const input of document.querySelectorAll('#result-summary input[type=number]')){const bad=!input.value||!input.checkValidity();input.setAttribute('aria-invalid',String(bad));if(bad)valid=false;}return valid;}
function friendlyError(response,data){if(response.status===429)return 'Analysis rate limit reached. Retry in one minute.';if(response.status===503)return 'An analysis is running or data is unavailable. Retry shortly.';if(response.status===422){if(typeof data?.detail==='string')return data.detail;return 'Check the location, camera angles and model settings.';}return 'Could not calculate visibility. Retry shortly.';}
async function jsonRequest(url,options={},timeout=15000){
 const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),timeout);
 try{
  const response=await fetch(url,{...options,cache:'no-store',signal:controller.signal});let data;
  try{data=await response.json()}catch{throw Object.assign(Error('Response interrupted.'),{retryable:true})}
  if(!response.ok){const error=Error(friendlyError(response,data));error.status=response.status;error.retryable=response.status===429||response.status>=500;error.retryAfter=Number(response.headers?.get('Retry-After'))*1000;throw error;}
  return data;
 }catch(error){if(error.status===undefined)error.retryable=true;throw error;}
 finally{clearTimeout(deadline);}
}
async function post(snapshot){
 // Serialize this page's requests; background height comparisons yield between cells.
 const previous=analysisTransport;let release;analysisTransport=new Promise(done=>release=done);await previous;
 try{const data=await jsonRequest('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});if(!data.camera_breakdown||data.active_cameras?.length!==3)throw Object.assign(Error('Refreshing analysis configuration.'),{retryable:true});return data;}
 finally{release();}
}
const heightProfile=()=>JSON.stringify(candidates.map(c=>heightSnapshot(c,0)));
const heightKey=input=>JSON.stringify(Object.keys(input).sort().map(key=>[key,input[key]]));
function rememberHeight(result){heightSamples.set(heightKey(result.input),result);if(heightSamples.size>60)heightSamples.delete(heightSamples.keys().next().value);}
function heightSnapshot(c,height){return {...structuredClone(c),height,priority:structuredClone(priority)};}
function renderHeightComparison(){
 const box=$('height-results');box.replaceChildren();if(!$('height-comparison').open)return;
 const table=el('table','grid height-grid'),caption=el('caption','',heightLoading?'Simulated ha · calculating…':usePriority()?'Visible priority forest · simulated ha':'Visible forest · simulated ha');table.append(caption);const head=el('thead'),hr=el('tr');['Height',...candidates.map((c,i)=>letters[i]+' · '+siteName(c))].forEach(value=>hr.append(el('th','',value)));head.append(hr);table.append(head);const body=el('tbody');
 for(const height of [30,100,500,600,700]){const row=el('tr',height===candidates[0]?.height?'main-metric':'');row.append(el('th','',height+' m'));for(const c of candidates){const result=heightSamples.get(heightKey(heightSnapshot(c,height))),value=usePriority()?result?.metrics?.[scenario]?.priority_visible_ha:result?.metrics?.[scenario]?.visible_forest_ha;row.append(el('td','',area(value,result?.resolution_m)));}body.append(row);}
 table.append(body);box.append(table);
}
async function loadHeightComparison(){
 if(heightLoading||busy||reconnecting||!$('height-comparison').open)return;heightLoading=true;renderHeightComparison();
 const inputs=candidates.map(c=>heightSnapshot(c,c.height)),profile=heightProfile();
 try{for(const height of [30,100,500,600,700])for(const c of inputs){
  if(busy||reconnecting||!$('height-comparison').open||profile!==heightProfile())return;
  const snapshot={...c,height},key=heightKey(snapshot);if(!heightSamples.has(key))rememberHeight(await post(snapshot));renderHeightComparison();
 }}catch(error){if(error.retryable)scheduleReconnect(error.retryAfter);}
 finally{heightLoading=false;renderHeightComparison();if(profile!==heightProfile()&&!busy&&!reconnectTimer)loadHeightComparison();}
}
function applyConfig(config){
 if(!config.ready)throw Object.assign(Error('Regional data is loading.'),{retryable:true});
 const fingerprint=JSON.stringify({presets:config.presets,files:config.data?.files}),changed=configFingerprint!==null&&configFingerprint!==fingerprint;
 if(!candidates.length||changed){candidates=structuredClone(config.presets);candidates.forEach(c=>{c.height=candidates[0].height;c.resolution=candidates[0].resolution});results=[null,null];heightSamples.clear();dirty=new Set([0,1]);selected=Math.min(selected,candidates.length-1);}
 configFingerprint=fingerprint;dataInfo=config.data;showControls();dataSummary();return changed;
}
function scheduleReconnect(delay){
 if(reconnectTimer)return;
 const wait=Number.isFinite(delay)&&delay>0?delay:Math.min(15000,1000*2**Math.min(reconnectAttempt,4));reconnectAttempt++;
 status('Connection interrupted. Reconnecting…',true);state('Reconnecting · showing previous results.',true);
 banner('Connection interrupted. Retrying automatically.',results.some(Boolean)?'Previous results are shown.':'',true);
 reconnectTimer=setTimeout(()=>{reconnectTimer=null;if(map)reconnect();else init();},wait);
}
async function reconnect(){
 if(reconnecting)return;if(busy){scheduleReconnect();return;}
 clearTimeout(reconnectTimer);reconnectTimer=null;reconnecting=true;status('Reconnecting…');state('Reconnecting…');
 try{const config=await jsonRequest('/api/config',{},5000);applyConfig(config);requestErrors.clear();lastError='';pending.clear();scheduled.clear();reconnectAttempt=0;reconnecting=false;banner();render();await run(true);}
 catch{reconnecting=false;scheduleReconnect();}
}
async function run(both=true,requested=null){if(!map){init();return;}
 if(requested===null){readControls();if(!validateControls()){lastError='Check the highlighted settings.';status(lastError,true);renderSummary();return;}requested=both?[0,1]:[selected];}
 clearTimeout(timer);const indices=[...new Set([...scheduled,...requested])];scheduled.clear();markStale(indices);
 if(reconnecting||busy){indices.forEach(i=>pending.add(i));return;}
 if(reconnectAttempt){await reconnect();return;}
 await calculate(indices);
}
async function calculate(indices){
 busy=true;setBusy(true);status('Tracing sightlines…');renderSummary();let retryDelay;
 const snapshots=indices.map(i=>({...structuredClone(candidates[i]),priority:structuredClone(priority)}));
 try{
  for(const [k,snapshot] of snapshots.entries()){
   const i=indices[k];try{
    const data=await post(snapshot);
    if(JSON.stringify({...candidates[i],priority})!==JSON.stringify(snapshot))continue;
    const other=1-i;if(results[other]&&results[other].algorithm!==data.algorithm){results[other]=null;heightSamples.clear();dirty.add(other);pending.add(other);}
    results[i]=data;rememberHeight(data);dirty.delete(i);requestErrors.delete(i);render();
   }catch(error){
    if(error.status===422){try{if(applyConfig(await jsonRequest('/api/config',{},5000))){pending.add(0);pending.add(1);break;}}catch{error.retryable=true;}}
    requestErrors.set(i,error.retryable?'Connection interrupted. Retrying automatically.':error.message);
    if(error.retryable){retryDelay=error.retryAfter;scheduleReconnect(retryDelay);break;}
   }
  }
  lastError=[...requestErrors.values()].at(-1)||'';
  if(lastError){status(lastError,true);banner(lastError,results.some(Boolean)?'Previous results are shown.':'',true);renderSummary();}
  else{banner();render();status('');}
 }finally{
  busy=false;setBusy(false);
  if(pending.size&&!reconnectTimer&&!reconnecting){const next=[...pending];pending.clear();calculate(next);}else if(!reconnectTimer)loadHeightComparison();
 }
}

// --- Priority drawing --------------------------------------------------------
function updatePriority(){
 if(priorityLayer){map.removeLayer(priorityLayer);priorityLayer=null;}
 if(priority){const points=priority.map(p=>[p[1],p[0]]);priorityLayer=L.layerGroup([
  L.polygon(points,{color:token('--bg-0'),weight:3,fillOpacity:0,interactive:false,className:'priority-halo'}),
  L.polygon(points,{color:token('--accent'),weight:1.5,fillColor:token('--accent'),fillOpacity:.12,interactive:false,className:'priority-area'})
 ]).addTo(map);}
 $('clear-priority').hidden=!priority;
}
function stopDrawing(){drawing=false;drawPoints=[];layers.draw.clearLayers();$('finish').hidden=true;$('draw').textContent='Draw priority forest';$('draw').classList.remove('active');map.doubleClickZoom.enable();document.body.classList.remove('drawing');$('draw-help').hidden=true;}
function finishDraw(){
 if(drawPoints.length<3){status('Select at least three points.',true);return;}
 priority=drawPoints.map(p=>[p.lng,p.lat]);stopDrawing();updatePriority();showTab($('tab-compare'));$('view-compare').scrollTop=0;
 if(matchMedia('(max-width:760px)').matches)$('result-summary').scrollIntoView({block:'start'});
 run(true);
}
function toggleDraw(){if(!map)return;if(drawing){stopDrawing();return;}drawing=true;drawPoints=[];map.doubleClickZoom.disable();document.body.classList.add('drawing');$('finish').hidden=false;$('finish').disabled=true;$('draw').textContent='Cancel drawing';$('draw').classList.add('active');$('draw-help').hidden=false;$('draw-help').textContent=(matchMedia('(pointer:coarse)').matches?'Tap':'Click')+' area corners, then Finish area.';status('Select corners of the priority forest area.');}

// --- Start -------------------------------------------------------------------
function dataSummary(){const pct=dataInfo.assumed_canopy_forest_pct;localized($('data-summary'),`NLS 2019 · CORINE 2024 · Luke MS-NFI 2023 height and cover. ${M.percent(pct,'en',2)} of forest cells use assumed canopy.`,`NLS 2019 · CORINE 2024 · Luke MS-NFI 2023 boy ve taç örtüsü. Orman hücrelerinin ${M.percent(pct,'tr',2)} kadarında varsayılan taç kullanılır.`);}
function mapState(text){$('map-state').hidden=!text;if(text)$('map-state-text').textContent=text;}
async function init(){let initializingMap=null;if(ready)return;ready=true;mapState('Loading regional map…');setBusy(true);
 try{const config=await jsonRequest('/api/config',{},5000);applyConfig(config);renderSummary();
  const m=initializingMap=L.map('map',{attributionControl:true,zoomControl:false,zoomSnap:.25,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false});
  layers={markers:L.layerGroup(),sectors:L.layerGroup(),draw:L.layerGroup()};
  const DrawControl=L.Control.extend({onAdd(){const controls=document.querySelector('.map-toolbar');L.DomEvent.disableClickPropagation(controls);L.DomEvent.disableScrollPropagation(controls);return controls;}});
  new DrawControl({position:'topleft'}).addTo(m);L.control.zoom({zoomInTitle:'Zoom in',zoomOutTitle:'Zoom out',position:matchMedia('(max-width:760px)').matches?'bottomleft':'topleft'}).addTo(m);m.attributionControl.setPrefix(false);m.attributionControl.addAttribution('NLS 2019 · Syke 2024 · Luke 2023 | CC BY 4.0');
  const mapResponse=await fetch('/maps/map.json');if(!mapResponse.ok)throw Error();const mapConfig=await mapResponse.json();
  const interior=await MapDisplay.extent('/maps/background.png'),nw=m.project(L.latLng(mapConfig.bounds[1][0],mapConfig.bounds[0][1]),0),se=m.project(L.latLng(mapConfig.bounds[0][0],mapConfig.bounds[1][1]),0);
  const corner=(x,y)=>m.unproject(L.point(nw.x+(se.x-nw.x)*x,nw.y+(se.y-nw.y)*y),0);
  const safeBounds=L.latLngBounds(corner(interior.left,interior.bottom),corner(interior.right,interior.top));
  function constrainView(){const minimum=Math.ceil(m.getBoundsZoom(safeBounds,true)*4)/4-.25;m.stop();m.setMinZoom(minimum);if(Number.isFinite(m.getZoom())){if(m.getZoom()<minimum)m.setZoom(minimum,{animate:false});m.panInsideBounds(safeBounds,{animate:false});}}
  m.options.maxBoundsViscosity=1;m.setMaxBounds(safeBounds);constrainView();
  const phone=matchMedia('(max-width:760px)').matches;
  const initialBounds=phone?L.latLngBounds(candidates.map(c=>[c.lat,c.lon])).pad(.08):L.latLngBounds(candidates.flatMap(c=>[0,90,180,270].map(bearing=>offset(c.lat,c.lon,bearing,c.max_range))));
  m.fitBounds(initialBounds,{padding:phone?[28,28]:[44,44],maxZoom:11,animate:false});
  const background=L.imageOverlay('/maps/background.png',mapConfig.bounds,{className:'base-map'}).addTo(m);const forests=L.imageOverlay('/maps/forest.png',mapConfig.bounds,{opacity:.45}),waters=L.imageOverlay('/maps/water.png',mapConfig.bounds,{opacity:.45});
  L.control.layers({'Local terrain map':background},{'Forest highlight':forests,'Water highlight':waters},{collapsed:true,position:phone?'bottomleft':'topleft'}).addTo(m);L.control.scale({imperial:false,position:'bottomright'}).addTo(m);
  for(const layer of Object.values(layers))layer.addTo(m);
  const labels=[['Helsinki',60.17,24.94],['Espoo',60.205,24.66],['Vantaa',60.294,25.04],['Nuuksio',60.32,24.51,true],['Sipoonkorpi',60.32,25.19,true]];
  labels.filter(([name])=>!candidates.some(c=>siteName(c)===name)).forEach(([name,lat,lon,forest])=>L.marker([lat,lon],{interactive:false,keyboard:false,icon:L.divIcon({className:'map-label'+(forest?' forest-label':''),html:name,iconSize:[100,20]})}).addTo(m));
  m.on('click',e=>{if(drawing){drawPoints.push(e.latlng);$('finish').disabled=drawPoints.length<3;layers.draw.clearLayers();L.polyline(drawPoints,{color:token('--accent'),weight:1.5,dashArray:'5 4'}).addTo(layers.draw);drawPoints.forEach(p=>L.circleMarker(p,{radius:4,color:token('--accent'),fillColor:token('--bg-0'),fillOpacity:1}).addTo(layers.draw));return;}readControls();candidates[selected].lat=e.latlng.lat;candidates[selected].lon=e.latlng.lng;showControls();run(false)});
  m.on('dblclick',()=>{if(drawing)finishDraw()});
  m.on('moveend zoomend',()=>{if(map)renderMap()});
  new ResizeObserver(()=>{m.invalidateSize({pan:false});constrainView();}).observe($('map'));
  new ResizeObserver(([entry])=>{document.documentElement.style.setProperty('--map-legend-height',Math.ceil(entry.borderBoxSize?.[0]?.blockSize||entry.contentRect.height)+'px');}).observe(document.querySelector('.legend'));
  map=m;reconnectAttempt=0;mapState('');render();await run(true);
 }catch{ready=false;const failedMap=map||initializingMap;if(failedMap){const controls=document.querySelector('.map-toolbar');failedMap.remove();if(controls)document.querySelector('.map-shell').append(controls);}map=null;layers=null;mapState('Could not load regional map data. Use Recalculate both sites to retry.');lastError='Could not load regional map data. Use Recalculate both sites to retry.';status(lastError,true);banner(lastError,'',true);renderSummary();setBusy(false);scheduleReconnect();}}

['lat','lon','max-range','smoke-height','tilt','vfov'].forEach(id=>$(id).addEventListener('change',()=>{readControls();later(300)}));
for(const id of ['height','resolution'])$(id).addEventListener('change',()=>{readControls();const key=id==='height'?'height':'resolution',value=id==='height'?+$(id).value:$(id).value;candidates.forEach(c=>c[key]=value);later(150,[0,1])});
$('height-comparison').addEventListener('toggle',()=>{renderHeightComparison();if($('height-comparison').open)loadHeightComparison()});
$('analyze').addEventListener('click',()=>run(true));$('retry').addEventListener('click',()=>map?reconnect():init());
window.addEventListener('online',()=>{if(reconnectAttempt)reconnect()});
$('scenario').addEventListener('change',()=>{scenario=$('scenario').value;render()});
$('draw').addEventListener('click',toggleDraw);$('finish').addEventListener('click',finishDraw);$('clear-priority').addEventListener('click',()=>{priority=null;updatePriority();stopDrawing();run(true)});
document.addEventListener('keydown',e=>{if(drawing&&e.key==='Enter'){finishDraw();return;}if(drawing&&e.key==='Escape'){stopDrawing();return;}
 if(e.metaKey||e.ctrlKey||e.altKey||e.target.closest?.('input,select,textarea'))return;
 if(e.key==='1'||e.key==='2'){selectSite(+e.key-1);e.preventDefault();}else if(e.key==='p'||e.key==='P'){toggleDraw();e.preventDefault();}});
if(matchMedia('(max-width:760px)').matches)$('settings').open=false;
window.addEventListener('languagechange',()=>{if(candidates.length){showControls();render();}if(dataInfo)dataSummary();});
// Panel tabs: Compare (default), Breakdown (table), Data (sources and assumptions).
const tabs=[...document.querySelectorAll('[role=tab]')];
function showTab(tab){tabs.forEach(t=>{const on=t===tab;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;$(t.getAttribute('aria-controls')).hidden=!on;});}
tabs.forEach((t,i)=>{t.addEventListener('click',()=>showTab(t));t.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const next=tabs[(i+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length];showTab(next);next.focus();e.preventDefault();}});});
init();
