'use strict';
(function(root){
 function accounting(metrics,round,blind,resolution){
  if(!metrics)return null;
  const visible=round(metrics.visible_forest_ha,resolution),split=blind(metrics,resolution);
  if(![visible,split.outside,split.occluded].every(v=>typeof v==='number'&&Number.isFinite(v)))return null;
  return {visible,occluded:split.occluded,outside:split.outside,total:visible+split.occluded+split.outside};
 }
 const api={accounting};root.PlacementCharts=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
