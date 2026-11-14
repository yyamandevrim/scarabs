const {test}=require('node:test');
const assert=require('node:assert/strict');
const c=require('../static/charts.js');
const m=require('../static/metrics.js');
test('accounting never invents missing parts and the chart total equals its labels',()=>{
 assert.equal(c.accounting({visible_forest_ha:10,blind_forest_ha:20},m.round,m.blind,120),null);
 const a=c.accounting({visible_forest_ha:12523.56,outside_fov_forest_ha:14431.68,occluded_forest_ha:.36,blind_forest_ha:14432.04},m.round,m.blind,120);
 assert.deepEqual(a,{visible:12520,outside:14430,occluded:0,total:26950});
});

const {appHarness}=require('./ui_app.cjs');
test('shared measured zeros are omitted without hiding unknown breakdown values',async()=>{
 const h=await appHarness();try{
  const metrics={visible_forest_ha:100,blind_forest_ha:20,outside_fov_forest_ha:20,occluded_forest_ha:0,water_view_ha:30,viewed_area_ha:150,water_share_pct:20};
  const fixture={input:{priority:null},resolution_m:40,metrics:{canopy_smoke:metrics,canopy_ground:{visible_forest_ha:0}}};
  h.api.breakdown([fixture,fixture]);
  const rows=()=>[...h.window.document.querySelectorAll('#more-comparison tbody tr')].map(r=>r.textContent);
  assert.ok(!rows().some(r=>r.startsWith('Occluded')));
  assert.ok(!rows().some(r=>r.startsWith('Canopy · ground')));
  const unknown={...fixture,metrics:{...fixture.metrics,canopy_smoke:{...metrics,occluded_forest_ha:null}}};
  h.api.breakdown([fixture,unknown]);
  assert.ok(rows().some(r=>r.startsWith('Occluded')&&r.includes('—')),'unknown values must remain visibly uncomputed');
 }finally{await h.close();}
});
