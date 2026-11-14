/* Local, on-demand CAD viewer. Bundle once; no runtime CDN or build step. */
import {Scene,Color,PerspectiveCamera,WebGLRenderer,AmbientLight,DirectionalLight,Group,Mesh,MeshStandardMaterial,MeshPhysicalMaterial,MeshBasicMaterial,LineBasicMaterial,Line,BufferGeometry,Float32BufferAttribute,Vector2,Vector3,Raycaster,DoubleSide,CanvasTexture,RepeatWrapping,SRGBColorSpace,PMREMGenerator,EquirectangularReflectionMapping,TubeGeometry,QuadraticBezierCurve3,CircleGeometry,ACESFilmicToneMapping} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
export async function mountModel({selectPart}){
 const stage=document.querySelector('#model-stage'),canvas=document.querySelector('#model-canvas');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let renderer;
 try{const context=canvas.getContext('webgl2',{antialias:true,alpha:true,powerPreference:'low-power'});if(!context)throw Error();renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});}catch{throw Error('WebGL unavailable');}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x090e13,0);renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
 const scene=new Scene(),assembly=new Group();scene.add(assembly);
 // A small procedural overcast studio: 256 × 128 pixels, filtered once into a 64px PMREM.
 const sky=document.createElement('canvas');sky.width=256;sky.height=128;const sky2d=sky.getContext('2d');
 const gradient=sky2d.createLinearGradient(0,0,0,128);gradient.addColorStop(0,'#d1e2ec');gradient.addColorStop(.45,'#91a7b5');gradient.addColorStop(.55,'#697c87');gradient.addColorStop(1,'#26353e');sky2d.fillStyle=gradient;sky2d.fillRect(0,0,256,128);
 sky2d.fillStyle='#eff5f7';sky2d.filter='blur(12px)';sky2d.fillRect(18,12,64,33);sky2d.filter='none';
 const environmentTexture=new CanvasTexture(sky);environmentTexture.colorSpace=SRGBColorSpace;environmentTexture.mapping=EquirectangularReflectionMapping;
 const pmrem=new PMREMGenerator(renderer),environment=pmrem.fromEquirectangular(environmentTexture);scene.environment=environment.texture;environmentTexture.dispose();pmrem.dispose();
 scene.add(new AmbientLight(0xb7cbd8,.3));const light=new DirectionalLight(0xf0f3f2,3.1);light.position.set(-.5,.8,.6);scene.add(light);
 const camera=new PerspectiveCamera(31,1,.01,10);
 const grain=document.createElement('canvas');grain.width=grain.height=64;const grain2d=grain.getContext('2d'),pixels=grain2d.createImageData(64,64);let seed=139;
 for(let i=0;i<pixels.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const value=220+(seed%35);pixels.data.set([value,value,value,255],i);}grain2d.putImageData(pixels,0,0);
 const roughnessMap=new CanvasTexture(grain);roughnessMap.wrapS=roughnessMap.wrapT=RepeatWrapping;
 const body=new MeshStandardMaterial({color:0xc8cdcf,roughness:.87,roughnessMap,bumpMap:roughnessMap,bumpScale:.000018,metalness:0,vertexColors:true,envMapIntensity:.6});
 const plate=new MeshStandardMaterial({color:0xb9c1c5,roughness:.55,metalness:.12,vertexColors:true,envMapIntensity:.7});
 const face=new MeshStandardMaterial({color:0x172028,roughness:.38,metalness:.15,vertexColors:true});
 const lens=new MeshPhysicalMaterial({color:0x08151f,roughness:.12,metalness:.25,clearcoat:1,clearcoatRoughness:.07,envMapIntensity:1.5});
 const lensCentre=new MeshPhysicalMaterial({color:0x182d3d,roughness:.08,metalness:.4,clearcoat:1,envMapIntensity:1.8});
 const highlight=new MeshStandardMaterial({color:0x8fc3e3,roughness:.7,vertexColors:true});
 const ropeMaterial=new MeshStandardMaterial({color:0x8a989c,roughness:1,bumpMap:roughnessMap,bumpScale:.00006});
 const activeFill=new MeshBasicMaterial({color:0x8fc3e3,opacity:.075,transparent:true,side:DoubleSide,depthWrite:false});
 const selectedFill=new MeshBasicMaterial({color:0x8fc3e3,opacity:.16,transparent:true,side:DoubleSide,depthWrite:false});
 const activeLine=new LineBasicMaterial({color:0x8fc3e3,transparent:true,opacity:.55});
 const parts={},meshes=[],geometries=new Set(),materials=new Set([body,plate,face,lens,lensCentre,highlight,ropeMaterial,activeFill,selectedFill,activeLine]);
 let destroyed=false,lost=false,visible=true,frame=0,last=0,totalDraws=0,activeTime=0,drift=!reduced.matches,interacted=false,explode=0,explodeTarget=0,showFov=false,selectedPart=null;
 let priorDistance=.49;
 let yaw=.93,pitch=.20,distance=.49,velocityX=0,velocityY=0,settle=reduced.matches?1:0;
 const pointers=new Map();let start=null,pinchDistance=0;
 const defaults={yaw:.93,pitch:.20,distance:.49};
 const podPositions={centre:new Vector3(0,.045,.1081),left:new Vector3(-.0936,.045,-.054),right:new Vector3(.0936,.045,-.054)};
 const normals={centre:new Vector3(0,0,1),left:new Vector3(-.866,0,-.5),right:new Vector3(.866,0,-.5)};
 const offsets={housing:new Vector3(),camera_centre:new Vector3(0,0,.045),camera_left:new Vector3(-.04,0,-.023),camera_right:new Vector3(.04,0,-.023),plate_top:new Vector3(0,.045,0),plate_bottom:new Vector3(0,-.045,0)};
 const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 let gltf;
 try{gltf=await loader.loadAsync('/static/hardware/acorn.glb');}catch(error){renderer.dispose();throw error;}
 gltf.scene.updateMatrixWorld(true);
 gltf.scene.traverse(m=>{
  if(!m.isMesh)return;
  let node=m;while(node.parent&&!(node.name in offsets))node=node.parent;
  const name=node.name;if(!(name in offsets))return;
  if(!parts[name]){parts[name]=new Group();assembly.add(parts[name]);}
  const geometry=m.geometry.clone().applyMatrix4(m.matrixWorld);geometries.add(geometry);
  const uv=[];for(let i=0;i<geometry.attributes.position.count;i++){const x=geometry.attributes.position.getX(i),y=geometry.attributes.position.getY(i),z=geometry.attributes.position.getZ(i),nx=Math.abs(geometry.attributes.normal.getX(i)),ny=Math.abs(geometry.attributes.normal.getY(i)),nz=Math.abs(geometry.attributes.normal.getZ(i));uv.push((nx>ny&&nx>nz?z:x)*140,(ny>nx&&ny>nz?z:y)*140);}geometry.setAttribute('uv',new Float32BufferAttribute(uv,2));
  const dark=m.material.name==='Camera face';const mesh=new Mesh(geometry,dark?face:name.startsWith('plate')?plate:body);mesh.userData={part:name,original:mesh.material};meshes.push(mesh);parts[name].add(mesh);

 });
 // Release loader resources after baking the six logical groups into metre coordinates.
 gltf.scene.traverse(m=>{if(m.isMesh){m.geometry.dispose();m.material.dispose();}});gltf=null;
 const line=(points,material)=>{const g=new BufferGeometry().setFromPoints(points);geometries.add(g);return new Line(g,material);};
 // Material detail stays within each existing 49mm camera face; no new pod or sensor.
 for(const id of ['left','centre','right']){
  const normal=normals[id],centre=podPositions[id];
  for(const [radius,material,lift]of [[.0208,lens,.00012],[.008,lensCentre,.00017]]){
   const g=new CircleGeometry(radius,48);geometries.add(g);const disc=new Mesh(g,material);disc.position.copy(centre).addScaledVector(normal,lift);disc.quaternion.setFromUnitVectors(new Vector3(0,0,1),normal);disc.userData={part:'camera_'+id,original:material};parts['camera_'+id].add(disc);meshes.push(disc);
  }
 }
 const bridle=new Group();assembly.add(bridle);
 const rope=(a,b)=>{const middle=a.clone().lerp(b,.5);middle.z+=.006;const g=new TubeGeometry(new QuadraticBezierCurve3(a,middle,b),12,.0006,5,false);geometries.add(g);return new Mesh(g,ropeMaterial);};
 for(const x of [-.0055,.0055])bridle.add(rope(new Vector3(x,.075,0),new Vector3(x*110,.7,.1)));
 bridle.add(rope(new Vector3(0,-.075,0),new Vector3(0,-1.2,0)));
 const sectors={};
 for(const id of ['left','centre','right']){
  const group=new Group(),origin=new Vector3(0,.045,0),normal=normals[id],heading=Math.atan2(normal.x,normal.z);
  // A short, translucent sector volume remains readable at the shallow drawing angle.
  // Each third shows the owner-specified combined observation model, aligned to a CAD pod.
  const rings=[[],[]],radius=.16;
  for(let i=0;i<=16;i++){const a=heading+(i/16-.5)*Math.PI*2/3;for(let j=0;j<2;j++)rings[j].push(new Vector3(origin.x+Math.sin(a)*radius,origin.y+(j?1:-1)*.003,origin.z+Math.cos(a)*radius));}
  const pos=[],tri=(a,b,c)=>{for(const p of [a,b,c])pos.push(p.x,p.y,p.z);};
  for(let i=0;i<16;i++){tri(origin,rings[0][i],rings[0][i+1]);tri(origin,rings[1][i+1],rings[1][i]);tri(rings[0][i],rings[1][i],rings[1][i+1]);tri(rings[0][i],rings[1][i+1],rings[0][i+1]);}
  for(const i of [0,16])tri(origin,rings[0][i],rings[1][i]);
  const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(pos,3));geometries.add(g);
  const outlinePoints=[origin,rings[0][0],...rings[0].slice(1),origin,rings[1][0],...rings[1].slice(1),origin,rings[0][0],rings[1][0],origin,rings[0][16],rings[1][16]];
  const fill=new Mesh(g,activeFill),outline=line(outlinePoints,activeLine);group.add(fill,outline);assembly.add(group);sectors[id]={group,fill,outline};group.visible=false;
 }
 const anchors={left:podPositions.left,centre:podPositions.centre,right:podPositions.right,eye:new Vector3(.0055,.075,0),housing:new Vector3(.048,-.025,.013)};
 const partFor=id=>['left','centre','right'].includes(id)?'camera_'+id:id==='eye'?'plate_top':'housing';
 function highlightPart(id){touch();selectedPart=id;for(const mesh of meshes)mesh.material=mesh.userData.part===partFor(id)?highlight:mesh.userData.original;updateSectors();}
 function updateSectors(){for(const [id,s]of Object.entries(sectors)){s.group.visible=showFov;s.fill.material=selectedPart===id?selectedFill:activeFill;s.outline.material=activeLine;s.outline.computeLineDistances();}request();}
 function updateLabels(){
  const rect=stage.getBoundingClientRect(),mobile=rect.width<600&&innerWidth<=760;
  for(const [id,anchor]of Object.entries(anchors)){
   const p=anchor.clone().addScaledVector(offsets[partFor(id)],explode);assembly.localToWorld(p);
   const facing=!normals[id]||normals[id].clone().applyQuaternion(assembly.quaternion).dot(camera.position.clone().sub(p).normalize())>-.025;
   const label=stage.querySelector('[data-part="'+id+'"]'),path=stage.querySelector('[data-leader="'+id+'"]');
   label.classList.toggle('facing-away',!facing&&!mobile);
   if(!facing||mobile){path.setAttribute('d','');continue;}
   const projected=p.project(camera),x=(projected.x*.5+.5)*rect.width,y=(-projected.y*.5+.5)*rect.height;
   const lr=label.getBoundingClientRect(),lx=lr.left-rect.left+ (lr.left-rect.left<rect.width/2?lr.width:0),ly=lr.top-rect.top+lr.height/2;
   const elbow=lx+(x>lx?16:-16);path.setAttribute('d',`M ${x-2} ${y} a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0 M ${x} ${y} L ${elbow} ${ly} L ${lx} ${ly}`);
  }
 }
 function draw(now){
  frame=0;if(destroyed||lost||!visible||document.hidden){last=0;return;}
  const dt=last?Math.min((now-last)/1000,.04):1/60;last=now;activeTime+=dt;
  if(reduced.matches){settle=1;explode=explodeTarget;drift=false;velocityX=velocityY=0;}
  if(drift&&activeTime<5)yaw+=dt*.022;else drift=false;
  if(!pointers.size){yaw+=velocityX;pitch+=velocityY;velocityX*=.84;velocityY*=.84;}
  pitch=Math.max(-.28,Math.min(.65,pitch));
  settle=Math.min(1,settle+dt/ .8);const eased=1-Math.pow(1-settle,3);
  assembly.rotation.y=(1-eased)*-.18;assembly.position.y=(1-eased)*.018;
  if(Math.abs(explodeTarget-explode)<.001)explode=explodeTarget;else explode+=(explodeTarget-explode)*Math.min(1,dt*13);
  for(const [name,g]of Object.entries(parts))g.position.copy(offsets[name]).multiplyScalar(explode);
  for(const [id,s]of Object.entries(sectors))s.group.position.copy(offsets['camera_'+id]).multiplyScalar(explode);
  bridle.visible=explode<.02;
  camera.position.set(Math.sin(yaw)*Math.cos(pitch)*distance,Math.sin(pitch)*distance,Math.cos(yaw)*Math.cos(pitch)*distance);camera.lookAt(0,0,0);camera.updateMatrixWorld();assembly.updateMatrixWorld(true);
  renderer.render(scene,camera);stage.classList.add('ready');totalDraws++;updateLabels();
  if(drift||settle<1||explode!==explodeTarget||Math.abs(velocityX)+Math.abs(velocityY)>.0001)request();else last=0;
 }
 function request(){if(!frame&&!destroyed&&!lost&&visible&&!document.hidden)frame=requestAnimationFrame(draw);}
 function touch(){interacted=true;drift=false;document.querySelector('#drag-hint').hidden=true;}
 function resize(){const r=stage.getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();request();}
 const observer=new ResizeObserver(resize);observer.observe(stage);
 const intersection=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)request();else{cancelAnimationFrame(frame);frame=0;last=0;}},{threshold:0});intersection.observe(stage);
 const visibility=()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;last=0;}else request();};document.addEventListener('visibilitychange',visibility);
 const raycaster=new Raycaster();
 const clickPart=e=>{const r=canvas.getBoundingClientRect();raycaster.setFromCamera(new Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(meshes,false)[0];if(hit){const name=hit.object.userData.part,id=name.replace('camera_','');selectPart(name.startsWith('camera_')?id:name.startsWith('plate')?'eye':'housing');}};
 canvas.addEventListener('pointerdown',e=>{touch();canvas.focus({preventScroll:true});pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});start={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);velocityX=velocityY=0;if(pointers.size===2){const [a,b]=[...pointers.values()];pinchDistance=Math.hypot(a.x-b.x,a.y-b.y);}});
 canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const prev=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2){const [a,b]=[...pointers.values()],d=Math.hypot(a.x-b.x,a.y-b.y);if(pinchDistance)distance=Math.max(.36,Math.min(.64,distance*pinchDistance/d));pinchDistance=d;}else{velocityX=-(e.clientX-prev.x)*.006;velocityY=e.pointerType==='touch'?0:(e.clientY-prev.y)*.004;yaw+=velocityX;pitch+=velocityY;}request();});
 const end=e=>{const click=pointers.size===1&&start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)<5;pointers.delete(e.pointerId);pinchDistance=0;if(e.type==='pointerup'&&click)clickPart(e);request();};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);velocityX=velocityY=0;});
 canvas.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();touch();distance=Math.max(.36,Math.min(.64,distance+e.deltaY*.001));request();},{passive:false});
 canvas.addEventListener('keydown',e=>{const keys={ArrowLeft:()=>yaw-=.12,ArrowRight:()=>yaw+=.12,ArrowUp:()=>pitch+=.08,ArrowDown:()=>pitch-=.08,'+':()=>distance=Math.max(.36,distance-.025),'=':()=>distance=Math.max(.36,distance-.025),'-':()=>distance=Math.min(.64,distance+.025)};if(keys[e.key]){e.preventDefault();touch();keys[e.key]();request();}});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;cancelAnimationFrame(frame);frame=0;stage.classList.remove('ready');document.querySelector('#model-fallback').hidden=false;});
 canvas.addEventListener('webglcontextrestored',()=>{lost=false;request();document.querySelector('#model-fallback').hidden=true;});
 const api={highlight:highlightPart,toggleFov(value){touch();showFov=value;if(value){priorDistance=distance;distance=Math.max(distance,.61);}else distance=priorDistance;updateSectors();},explode(value){touch();explodeTarget=value?1:0;request();},reset(){touch();({yaw,pitch,distance}=defaults);velocityX=velocityY=0;explodeTarget=0;request();},get stats(){return {draws:totalDraws,visible,lost,interacted,cameraViews:['left','centre','right'],selectedPart,exploded:explode,geometries:renderer.info.memory.geometries,calls:renderer.info.render.calls};},dispose(){destroyed=true;cancelAnimationFrame(frame);observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);for(const g of geometries)g.dispose();for(const m of materials)m.dispose();roughnessMap.dispose();environment.dispose();renderer.dispose();}};
 const pagehide=e=>{if(!e.persisted)api.dispose();};window.addEventListener('pagehide',pagehide);
 resize();updateSectors();window.acornModel=api;return api;
}
