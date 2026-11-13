'use strict';
// Presentation rules shared by the browser and regression tests. Never coerce a
// missing, null, string or non-finite metric into a measured zero.
(function(root){
 const valid=value=>typeof value==='number'&&Number.isFinite(value);
 function number(value,lang='en',digits=0){return valid(value)?new Intl.NumberFormat(lang==='tr'?'tr-TR':'en-GB',{maximumFractionDigits:digits}).format(value):'—';}
 function headline(value,resolution,lang='en'){return valid(value)?(resolution===120?'≈':'')+number(resolution===120?Math.round(value/10)*10:Math.round(value),lang):'—';}
 function blind(metrics){
  if(!metrics)return {total:null,outside:null,occluded:null};
  const {blind_forest_ha:total,outside_fov_forest_ha:outside,occluded_forest_ha:occluded}=metrics;
  // Old/incomplete responses may contain only a total. Do not invent its parts.
  if(![total,outside,occluded].every(valid)||Math.abs(total-outside-occluded)>.0031)
   return {total:valid(total)?Math.round(total):null,outside:null,occluded:null};
  // Round components first so the visible accounting identity remains exact.
  const a=Math.round(outside),b=Math.round(occluded);
  return {total:a+b,outside:a,occluded:b};
 }
 function bestPair(pairs,scenario,priority=false){
  return pairs.filter(p=>valid(p[scenario]?.visible_forest_ha)&&(!priority||valid(p[scenario]?.priority_visible_ha))).sort((a,b)=>(priority?b[scenario].priority_visible_ha-a[scenario].priority_visible_ha:0)||b[scenario].visible_forest_ha-a[scenario].visible_forest_ha)[0]||null;
 }
 const api={valid,number,headline,blind,bestPair};root.PlacementMetrics=api;
 if(typeof module!=='undefined')module.exports=api;
})(globalThis);
