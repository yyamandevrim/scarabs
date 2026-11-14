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

test('quick-mode figures round to 10 ha and the blind split still sums exactly',()=>{
 assert.equal(m.round(769.56,120),770);
 assert.equal(m.round(769.56,40),770);
 assert.equal(m.round(12523.56,40),12524);
 assert.equal(m.round(undefined,120),null);
 for(const [outside,occluded] of [[7335.24,0],[14410.64,4.9],[10750.36,14488.68],[5,5]]){
  const split=m.blind({blind_forest_ha:outside+occluded,outside_fov_forest_ha:outside,occluded_forest_ha:occluded},120);
  assert.equal(split.total,split.outside+split.occluded);
  assert.equal(split.outside%10,0);
 }
});

test('water share is not computed when no area is in view',()=>{
 assert.equal(m.share({viewed_area_ha:0,water_share_pct:0}),null);
 assert.equal(m.share({water_share_pct:0}),null);
 assert.equal(m.share({viewed_area_ha:120,water_share_pct:0}),0);
 assert.equal(m.share({viewed_area_ha:120,water_share_pct:83.7}),83.7);
});

test('percent places the sign correctly in Turkish without fabricating missing values',()=>{
 assert.equal(m.percent(84,'tr'),'%84');
 assert.equal(m.percent(84,'en'),'84%');
 assert.equal(m.percent(null,'tr'),'—');
 assert.equal(m.percent(0,'tr'),'%0');
});

test('priority pairs rounded to zero have no best pair or total-forest overlap bar',()=>{
 const pairs=[{pair:[0,1],canopy_smoke:{visible_forest_ha:770,priority_visible_ha:.1,overlap_forest_ha:500}},{pair:[0,2],canopy_smoke:{visible_forest_ha:2845,priority_visible_ha:.2,overlap_forest_ha:100}}];
 assert.equal(m.bestPair(pairs,'canopy_smoke',true,120),null);
 assert.deepEqual(m.pairBars(pairs,'canopy_smoke',true,120),[{visible:0,overlap:0},{visible:0,overlap:0}]);
});

test('signed display uses a mathematical minus, preserving locale formatting',()=>{
 assert.equal(m.number(-70,'en'),'−70');
 assert.equal(m.number(-70,'tr'),'−70');
});

test('equal positive priority selects higher total forest and full ties retain input order',()=>{
 const pairs=[{pair:[0,1],canopy_smoke:{priority_visible_ha:10.24,visible_forest_ha:9964.64}},{pair:[1,2],canopy_smoke:{priority_visible_ha:10.24,visible_forest_ha:10682.24}},{pair:[0,2],canopy_smoke:{priority_visible_ha:10.24,visible_forest_ha:10682.24}}];
 assert.equal(m.bestPair(pairs,'canopy_smoke',true,120),pairs[1]);
 assert.equal(m.bestPair(pairs,'canopy_smoke',true,40),pairs[1]);
 assert.deepEqual(pairs.map(p=>p.pair),[[0,1],[1,2],[0,2]]);
 assert.equal(m.bestPair([{canopy_smoke:{visible_forest_ha:1000}},{canopy_smoke:{priority_visible_ha:null,visible_forest_ha:2000}}],'canopy_smoke',true),null);
});
test('ranking uses computed priority before total even within one displayed rounding bucket',()=>{
 const pairs=[{canopy_smoke:{priority_visible_ha:10.1,visible_forest_ha:2000}},{canopy_smoke:{priority_visible_ha:10.2,visible_forest_ha:1000}}];
 assert.equal(m.bestPair(pairs,'canopy_smoke',true,120),pairs[1]);
});
