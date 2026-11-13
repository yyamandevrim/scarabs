const {test}=require('node:test');
const assert=require('node:assert/strict');
const m=require('../static/metrics.js');
test('missing and not computed are distinct from a real zero in both languages',()=>{
 for(const lang of ['en','tr']){
  for(const value of [undefined,null,NaN,Infinity,'0'])assert.equal(m.number(value,lang),'—');
  assert.equal(m.number(0,lang),'0');
  assert.equal(m.headline(null,120,lang),'—');
 }
});
test('legacy blind total cannot fabricate two zero components',()=>{
 assert.deepEqual(m.blind({blind_forest_ha:7335.24}),{total:7335,outside:null,occluded:null});
 assert.deepEqual(m.blind({blind_forest_ha:7335.24,outside_fov_forest_ha:0,occluded_forest_ha:0}),{total:7335,outside:null,occluded:null});
});
test('rounded parts always sum to the displayed total, including real zero occlusion',()=>{
 for(const [outside,occluded] of [[7335.24,0],[14431.68,.36],[14491.68,10689.28],[.6,.6],[0,0]]){
  const split=m.blind({blind_forest_ha:outside+occluded,outside_fov_forest_ha:outside,occluded_forest_ha:occluded});
  assert.equal(split.total,split.outside+split.occluded);
 }
 assert.equal(m.blind({blind_forest_ha:7335.24,outside_fov_forest_ha:7335.24,occluded_forest_ha:0}).occluded,0);
});
test('best pair is independent of current selection and honours priority',()=>{
 const p=[{pair:[0,1],canopy_smoke:{visible_forest_ha:770,priority_visible_ha:20}},{pair:[0,2],canopy_smoke:{visible_forest_ha:2845,priority_visible_ha:10}}];
 assert.equal(m.bestPair(p,'canopy_smoke'),p[1]);
 assert.equal(m.bestPair(p,'canopy_smoke',true),p[0]);
 assert.equal(m.bestPair([{canopy_smoke:{}}],'canopy_smoke'),null);
});
test('headline precision follows quick versus detailed resolution',()=>{
 assert.equal(m.headline(12523.56,120),'≈12,520');
 assert.equal(m.headline(12511.8,40),'12,512');
 assert.equal(m.number(12523.56,'tr'),'12.524');
});

test('absent priority area is uncomputed even if a legacy response contains zero',()=>{
 const old={input:{priority:null},metrics:{canopy_smoke:{priority_visible_ha:0}}};
 assert.equal(m.priorityValue(old,'canopy_smoke'),null);
 const calculated={input:{priority:[[24,60],[25,60],[24,61]]},metrics:{canopy_smoke:{priority_visible_ha:0}}};
 assert.equal(m.priorityValue(calculated,'canopy_smoke'),0);
});
