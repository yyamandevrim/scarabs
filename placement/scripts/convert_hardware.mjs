/** Reproducible CAD conversion. Run from the temporary npm toolchain documented in assets/hardware/README.md. */
import fs from 'node:fs';
import path from 'node:path';
import {Document, NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup, weld, quantize} from '@gltf-transform/functions';
import {BufferGeometry, Float32BufferAttribute,Vector3,Ray,DoubleSide} from 'three';
import {MeshBVH} from 'three-mesh-bvh';
import {mergeVertices,toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';
const repo=path.resolve(process.argv[2]||'.');
const source=fs.readFileSync(path.join(repo,'assets/hardware/acorn.obj'),'utf8');
if(!source.includes('Units = meters'))throw Error('Recheck source units');
const vertices=[], fragments=new Map();let current;
for(const line of source.split('\n')){
 const fields=line.trim().split(/\s+/);
 if(fields[0]==='v')vertices.push(fields.slice(1).map(Number));
 if(fields[0]==='o'){current=Number(fields[1].slice(4));fragments.set(current,[]);}
 if(fields[0]==='f'){
  const face=fields.slice(1).map(s=>Number(s.split('/')[0])-1);
  for(let i=1;i<face.length-1;i++)fragments.get(current).push(face[0],face[i],face[i+1]);
 }
}
// Verified by the four-view colour render (see README). Fragments are surfaces, not components.
const groups={housing:[],camera_centre:[],camera_left:[],camera_right:[],plate_top:[],plate_bottom:[]};
for(const [id,indices] of fragments){
 const group=id<=16?'camera_centre':id>=131&&id<=147?'camera_left':id>=149&&id<=165?'camera_right':id>=189&&id<=206?'plate_top':id>=207?'plate_bottom':'housing';
 groups[group].push([id,indices]);
}
// Bake short-range hemispherical AO once, outside the browser.
const collisionPositions=[];for(const indices of fragments.values())for(const i of indices){const [x,y,z]=vertices[i];collisionPositions.push(x,z-.175,-y);}
const collision=new BufferGeometry();collision.setAttribute('position',new Float32BufferAttribute(collisionPositions,3));
const bvh=new MeshBVH(collision,{targetLeafSize:8}),ray=new Ray(),tangent=new Vector3(),bitangent=new Vector3(),n=new Vector3(),point=new Vector3();
function ambientColours(geo){const colours=new Float32Array(geo.attributes.position.count*3);for(let i=0;i<geo.attributes.position.count;i++){
 point.fromBufferAttribute(geo.attributes.position,i);n.fromBufferAttribute(geo.attributes.normal,i).normalize();tangent.set(0,1,0);if(Math.abs(n.y)>.9)tangent.set(1,0,0);tangent.cross(n).normalize();bitangent.crossVectors(n,tangent);ray.origin.copy(point).addScaledVector(n,.00025);let occlusion=0;
 for(let j=0;j<32;j++){const t=(j+.5)/32,r=Math.sqrt(t),a=j*2.399963229728653;ray.direction.copy(n).multiplyScalar(Math.sqrt(1-t)).addScaledVector(tangent,Math.cos(a)*r).addScaledVector(bitangent,Math.sin(a)*r);const hit=bvh.raycastFirst(ray,DoubleSide,.00015,.018);if(hit)occlusion+=1-hit.distance/.018;}
 // Contact finish at the actual plate seams and three arm roots, tapering over 8 mm.
 let contact=0;
 const taper=d=>Math.max(0,Math.min(1,(.008-d)/.005));
 for(const angle of [0,2*Math.PI/3,-2*Math.PI/3]){
  const radial=point.x*Math.sin(angle)+point.z*Math.cos(angle),across=point.x*Math.cos(angle)-point.z*Math.sin(angle);
  const d=Math.hypot(Math.max(0,Math.abs(across)-.0225),Math.max(0,-.068-point.y,point.y-.02),radial-.0381);
  contact=Math.max(contact,taper(d));
 }
 const seam=Math.min(Math.abs(point.y-.07),Math.abs(point.y+.0726));
 if(Math.hypot(point.x,point.z)<.065)contact=Math.max(contact,taper(seam)*.75);
 for(const x of [-.0055,.0055]){const d=Math.hypot(point.x-x,point.z,Math.min(Math.abs(point.y-.075),Math.abs(point.y+.075)));if(d<.01)contact=Math.max(contact,taper(Math.abs(d-.0035)));}
 const shade=(1-.62*occlusion/32)*(1-.15*contact);colours.set([shade,shade,shade],i*3);
 }return colours;}
const doc=new Document(),buffer=doc.createBuffer(),scene=doc.createScene();
const body=doc.createMaterial('Matte body').setBaseColorFactor([.64,.68,.70,1]).setMetallicFactor(0).setRoughnessFactor(1);
const arm=doc.createMaterial('Secondary plastic').setBaseColorFactor([.35,.4,.43,1]).setRoughnessFactor(.55);
const back=doc.createMaterial('Pod back').setBaseColorFactor([.65,.68,.65,1]).setRoughnessFactor(.62);
const face=doc.createMaterial('Camera face').setBaseColorFactor([.10,.14,.17,1]).setMetallicFactor(0).setRoughnessFactor(1);
function primitive(parts,material){
 const positions=[];
 for(const [,indices]of parts)for(const index of indices){const [x,y,z]=vertices[index];positions.push(x,z-.175,-y);}
 let geo=new BufferGeometry();geo.setAttribute('position',new Float32BufferAttribute(positions,3));
 // Crease utility hashes at 0.01 units: compute in millimetres, then restore metres.
 geo.scale(1000,1000,1000);geo=toCreasedNormals(geo,Math.PI/5);geo.scale(.001,.001,.001);
 geo=mergeVertices(geo,1e-6);
 const access=(name,array,type)=>doc.createAccessor(name).setBuffer(buffer).setType(type).setArray(array);
 const prim=doc.createPrimitive().setAttribute('POSITION',access('position',geo.attributes.position.array,'VEC3')).setAttribute('NORMAL',access('normal',geo.attributes.normal.array,'VEC3')).setAttribute('COLOR_0',access('ao',ambientColours(geo),'VEC3')).setIndices(access('index',new Uint16Array(geo.index.array),'SCALAR')).setMaterial(material);
 geo.dispose();return prim;
}
for(const [name,parts]of Object.entries(groups)){
 const mesh=doc.createMesh(name),dark=parts.filter(([id])=>[0,147,165].includes(id)),light=parts.filter(([id])=>![0,147,165].includes(id));
 const armSurfaces=light.filter(([id])=>(id>=4&&id<=16)||(id>=131&&id<=144&&id!==139)||(id>=149&&id<=162&&id!==157));
 const backs=light.filter(([id])=>[3,139,157].includes(id));
 const shell=light.filter(item=>!armSurfaces.includes(item)&&!backs.includes(item));
 if(backs.length)mesh.addPrimitive(primitive(backs,back));if(shell.length)mesh.addPrimitive(primitive(shell,body));if(armSurfaces.length)mesh.addPrimitive(primitive(armSurfaces,arm));if(dark.length)mesh.addPrimitive(primitive(dark,face));
 scene.addChild(doc.createNode(name).setMesh(mesh));
}
await doc.transform(weld(),dedup(),quantize({quantizePosition:14,quantizeNormal:10,quantizeColor:8}));
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const out=path.join(repo,'placement/static/hardware/acorn.glb');await io.write(out,doc);
console.log(JSON.stringify({vertices:vertices.length,fragments:fragments.size,logicalParts:Object.keys(groups),bytes:fs.statSync(out).size}));
