'use strict';
// Presentation rules shared by the browser and regression tests. Never coerce a
// missing, null, string or non-finite metric into a measured zero.
(function(root){
 const valid=value=>typeof value==='number'&&Number.isFinite(value);
 function number(value,lang='en',digits=0){return valid(value)?new Intl.NumberFormat(lang==='tr'?'tr-TR':'en-GB',{maximumFractionDigits:digits}).format(value):'—';}
 function headline(value,resolution,lang='en'){return valid(value)?(resolution===120?'≈':'')+number(resolution===120?Math.round(value/10)*10:Math.round(value),lang):'—';}
 // Quick 120 m cells are 1.44 ha each: whole hectares would overstate precision.
 const step=resolution=>resolution===120?10:1;
 const round=(value,resolution)=>valid(value)?Math.round(value/step(resolution))*step(resolution):null;
 function share(metrics){return valid(metrics?.viewed_area_ha)&&metrics.viewed_area_ha>0&&valid(metrics.water_share_pct)?metrics.water_share_pct:null;}
 function blind(metrics,resolution){
  if(!metrics)return {total:null,outside:null,occluded:null};
  const {blind_forest_ha:total,outside_fov_forest_ha:outside,occluded_forest_ha:occluded}=metrics;
  // Old/incomplete responses may contain only a total. Do not invent its parts.
  if(![total,outside,occluded].every(valid)||Math.abs(total-outside-occluded)>.0031)
   return {total:round(total,resolution),outside:null,occluded:null};
  // Round components first so the visible accounting identity remains exact.
  const a=round(outside,resolution),b=round(occluded,resolution);
  return {total:a+b,outside:a,occluded:b};
 }
 function bestPair(pairs,scenario,priority=false){
  return pairs.filter(p=>valid(p[scenario]?.visible_forest_ha)&&(!priority||valid(p[scenario]?.priority_visible_ha))).sort((a,b)=>(priority?b[scenario].priority_visible_ha-a[scenario].priority_visible_ha:0)||b[scenario].visible_forest_ha-a[scenario].visible_forest_ha)[0]||null;
 }
 function priorityValue(result,scenario){return result?.input?.priority?result.metrics?.[scenario]?.priority_visible_ha:null;}
 const api={valid,number,headline,round,share,blind,bestPair,priorityValue};root.PlacementMetrics=api;
 if(typeof module!=='undefined')module.exports=api;
})(globalThis);
