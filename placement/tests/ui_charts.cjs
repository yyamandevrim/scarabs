const {test}=require('node:test');
const assert=require('node:assert/strict');
const c=require('../static/charts.js');
const m=require('../static/metrics.js');
test('camera wedges wrap north and preserve active mounting geometry',()=>{
 const w=c.wedges(350,[{yaw:20,hfov:80,active:true},{yaw:-70,hfov:60,active:false}]);
 assert.deepEqual(w[0],{index:0,active:true,centre:10,from:330,to:50,width:80});
 assert.equal(w[1].centre,280);assert.equal(w[1].active,false);
 const north=c.polar(0,0,10,0);assert.ok(Math.abs(north[0])<1e-10);assert.equal(north[1],-10);
});
test('accounting never invents missing parts and the chart total equals its labels',()=>{
 assert.equal(c.accounting({visible_forest_ha:10,blind_forest_ha:20},m.round,m.blind,120),null);
 const a=c.accounting({visible_forest_ha:12523.56,outside_fov_forest_ha:14431.68,occluded_forest_ha:.36,blind_forest_ha:14432.04},m.round,m.blind,120);
 assert.deepEqual(a,{visible:12520,outside:14430,occluded:0,total:26950});
});
test('sensitivity uses a common zero baseline, excludes missing points and plots true zero',()=>{
 const pad={top:10,right:10,bottom:20,left:30};
 assert.equal(c.sensitivityGeometry([{drift:0,visible_forest_ha:100}],300,150,pad),null);
 const g=c.sensitivityGeometry([{drift:-20,visible_forest_ha:0},{drift:0,visible_forest_ha:null},{drift:20,visible_forest_ha:120}],300,150,pad);
 assert.equal(g.points.length,2);assert.equal(g.points[0].x,30);assert.equal(g.points[0].y,130);
 assert.equal(g.points[1].x,290);assert.equal(g.max,200);
 assert.ok(g.points.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
});

const {appHarness}=require('./ui_app.cjs');
test('every selected scenario labels fixed canopy smoke sensitivity visibly and accessibly in EN/TR',async()=>{
 const h=await appHarness();try{
  const fixture={input:{height:600,heading:20},resolution_m:120,metrics:{},heading_sensitivity:[{drift:-20,heading:0,visible_forest_ha:80},{drift:0,heading:20,visible_forest_ha:100},{drift:20,heading:40,visible_forest_ha:120}]};
  for(const language of ['en','tr'])for(const scenario of ['canopy_smoke','canopy_ground','bare_smoke','bare_ground']){
   h.window.document.documentElement.lang=language;h.api.chart(fixture,scenario);
   const disclosure=h.window.document.querySelector('.sensitivity-details');
   for(const text of [disclosure.querySelector('summary').textContent,disclosure.textContent,disclosure.querySelector('svg').getAttribute('aria-label')]){
    assert.match(text,language==='tr'?/duman/i:/smoke/i);assert.match(text,language==='tr'?/taç/i:/canopy/i);
   }
   assert.match(disclosure.textContent,language==='tr'?/seçilen senaryodan bağımsız/i:/regardless of the selected scenario/i);
  }
 }finally{await h.close();}
});

test('partial elevation warns about unverified obstruction in EN/TR even with zero invalid forest targets',async()=>{
 const h=await appHarness();try{
  const fixture={input:{height:600,heading:20},resolution_m:120,metrics:{},unknown_forest_ha:0,unknown_elevation_in_window:true};
  for(const language of ['en','tr']){
   h.window.document.documentElement.lang=language;h.api.notes(fixture);
   const text=h.window.document.getElementById('uncertainty').textContent;
   assert.match(text,language==='tr'?/doğrulanmamış/i:/unverified/i);
   assert.match(text,language==='tr'?/engel/i:/obstruction/i);
   assert.match(text,language==='tr'?/ölçülmedi/i:/not been quantified/i);
   h.api.notes({...fixture,unknown_elevation_in_window:false});
   assert.doesNotMatch(h.window.document.getElementById('uncertainty').textContent,language==='tr'?/doğrulanmamış/i:/unverified/i);
  }
 }finally{await h.close();}
});
