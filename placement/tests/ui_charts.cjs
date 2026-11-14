const {test}=require('node:test');
const assert=require('node:assert/strict');
const c=require('../static/charts.js');
const m=require('../static/metrics.js');
test('accounting never invents missing parts and the chart total equals its labels',()=>{
 assert.equal(c.accounting({visible_forest_ha:10,blind_forest_ha:20},m.round,m.blind,120),null);
 const a=c.accounting({visible_forest_ha:12523.56,outside_fov_forest_ha:14431.68,occluded_forest_ha:.36,blind_forest_ha:14432.04},m.round,m.blind,120);
 assert.deepEqual(a,{visible:12520,outside:14430,occluded:0,total:26950});
});
