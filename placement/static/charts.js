'use strict';
// Small SVG/HTML charts drawn from analysis responses. Geometry helpers are pure
// and exported for node tests; nothing here invents a value that is not passed in.
(function(root){
 const NS='http://www.w3.org/2000/svg';
 const valid=v=>typeof v==='number'&&Number.isFinite(v);
 const norm=deg=>((deg%360)+360)%360;
 // Bearing 0 = up (grid north), clockwise, as in the analysis model.
 function polar(cx,cy,r,deg){const a=(deg-90)*Math.PI/180;return [cx+r*Math.cos(a),cy+r*Math.sin(a)];}
 function wedges(heading,cameras){
  return (cameras||[]).map((c,i)=>{const centre=norm(heading+c.yaw);return {index:i,active:Boolean(c.active),centre,from:norm(centre-c.hfov/2),to:norm(centre+c.hfov/2),width:Math.min(360,Math.max(0,c.hfov))};});
 }
 function arcPath(cx,cy,r,from,width,inner=0){
  if(width>=359.99)width=359.99;
  const [x1,y1]=polar(cx,cy,r,from),[x2,y2]=polar(cx,cy,r,from+width),large=width>180?1:0;
  if(!inner)return `M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large} 1 ${x2.toFixed(2)},${y2.toFixed(2)} Z`;
  const [x3,y3]=polar(cx,cy,inner,from+width),[x4,y4]=polar(cx,cy,inner,from);
  return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large} 1 ${x2.toFixed(2)},${y2.toFixed(2)} L${x3.toFixed(2)},${y3.toFixed(2)} A${inner},${inner} 0 ${large} 0 ${x4.toFixed(2)},${y4.toFixed(2)} Z`;
 }
 function niceMax(value){
  if(!valid(value)||value<=0)return 1;
  const p=10**Math.floor(Math.log10(value)),m=value/p;
  return (m<=1?1:m<=2?2:m<=2.5?2.5:m<=5?5:10)*p;
 }
 const scale=(d0,d1,r0,r1)=>v=>d1===d0?r0:r0+(v-d0)*(r1-r0)/(d1-d0);
 // Visible / occluded / outside, rounded part by part so the drawn total equals
 // the sum of the printed parts. Returns null rather than guessing missing parts.
 function accounting(metrics,round,blind,resolution){
  if(!metrics)return null;
  const visible=round(metrics.visible_forest_ha,resolution),split=blind(metrics,resolution);
  if(!valid(visible)||!valid(split.outside)||!valid(split.occluded))return null;
  return {visible,occluded:split.occluded,outside:split.outside,total:visible+split.occluded+split.outside};
 }
 function sensitivityGeometry(points,width,height,pad){
  const usable=(points||[]).filter(p=>valid(p.visible_forest_ha)&&valid(p.drift));
  if(usable.length<2)return null;
  const max=niceMax(Math.max(...usable.map(p=>p.visible_forest_ha)));
  const drifts=usable.map(p=>p.drift),x=scale(Math.min(...drifts),Math.max(...drifts),pad.left,width-pad.right),y=scale(0,max,height-pad.bottom,pad.top);
  return {max,ticks:[0,max/2,max],points:usable.map(p=>({...p,x:x(p.drift),y:y(p.visible_forest_ha)})),y};
 }
 function el(tag,attrs={},parent){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(parent)parent.append(e);return e;}
 function text(parent,x,y,value,cls,anchor='middle'){const t=el('text',{x,y,class:cls||'','text-anchor':anchor},parent);t.textContent=value;return t;}
 function sectorDiagram(container,{heading,cameras,labels}){
  container.replaceChildren();
  const size=168,c=size/2,r=64,svg=el('svg',{viewBox:`0 0 ${size} ${size}`,class:'sector-svg',role:'img'},container);
  el('circle',{cx:c,cy:c,r,class:'ring'},svg);el('circle',{cx:c,cy:c,r:r*.5,class:'ring faint'},svg);
  for(let d=0;d<360;d+=30){const [x1,y1]=polar(c,c,r,d),[x2,y2]=polar(c,c,r+(d%90?3:6),d);el('line',{x1,y1,x2,y2,class:'tick'},svg);}
  for(const [d,l] of [[0,'N'],[90,'E'],[180,'S'],[270,'W']]){const [x,y]=polar(c,c,r+13,d);text(svg,x,y+3.5,l,'cardinal');}
  const list=wedges(heading,cameras);
  list.filter(w=>!w.active).concat(list.filter(w=>w.active)).forEach(w=>el('path',{d:arcPath(c,c,r-1,w.from,w.width),class:'wedge'+(w.active?' active':' inactive')},svg));
  list.forEach(w=>{const [x,y]=polar(c,c,r*.72,w.centre);text(svg,x,y+3.5,labels[w.index][0],'wedge-label'+(w.active?'':' inactive'));});
  const [hx,hy]=polar(c,c,r+1,heading);el('line',{x1:c,y1:c,x2:hx,y2:hy,class:'needle'},svg);el('circle',{cx:c,cy:c,r:3,class:'hub'},svg);
  const title=el('title',{},svg);title.textContent=list.map(w=>`${labels[w.index]} ${Math.round(w.centre)}° ±${Math.round(w.width/2)}°${w.active?'':' · disconnected'}`).join(' · ');
 }
 function sensitivityChart(container,{points,format,tick,axis,current}){
  container.replaceChildren();
  const width=340,height=150,pad={top:20,right:26,bottom:26,left:50},g=sensitivityGeometry(points,width,height,pad);
  if(!g){container.append(Object.assign(document.createElement('p'),{className:'chart-empty small',textContent:'—'}));return;}
  const svg=el('svg',{viewBox:`0 0 ${width} ${height}`,class:'line-svg',role:'img','aria-label':axis},container);
  g.ticks.forEach(t=>{const y=g.y(t);el('line',{x1:pad.left,x2:width-pad.right,y1:y,y2:y,class:'grid'},svg);text(svg,pad.left-8,y+3.5,(tick||format)(t),'axis','end');});
  el('polyline',{points:g.points.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '),class:'series'},svg);
  g.points.forEach(p=>{const now=p.drift===current;el('circle',{cx:p.x,cy:p.y,r:now?5:3.5,class:'point'+(now?' current':'')},svg);const edge=p===g.points[0]?'start':p===g.points[g.points.length-1]?'end':'middle';text(svg,p.x+(edge==='start'?-4:edge==='end'?4:0),p.y-9,format(p.visible_forest_ha),'value'+(now?' current':''),edge);text(svg,p.x,height-8,`${Math.round(p.heading)}°`,'axis'+(now?' current':''));});
 }
 const api={polar,wedges,arcPath,niceMax,scale,accounting,sensitivityGeometry,sectorDiagram,sensitivityChart};
 root.PlacementCharts=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
