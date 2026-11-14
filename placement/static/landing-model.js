/* Local, on-demand CAD viewer. Bundle once; no runtime CDN or build step. */
import {Scene,Color,PerspectiveCamera,WebGLRenderer,AmbientLight,DirectionalLight,Group,Mesh,MeshStandardMaterial,MeshPhysicalMaterial,MeshBasicMaterial,LineBasicMaterial,Line,BufferGeometry,Float32BufferAttribute,Vector2,Vector3,Raycaster,DoubleSide,CanvasTexture,RepeatWrapping,SRGBColorSpace,PMREMGenerator,EquirectangularReflectionMapping,TubeGeometry,QuadraticBezierCurve3,CircleGeometry,RingGeometry,SphereGeometry,ACESFilmicToneMapping} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
export async function mountModel({selectPart}){
 const stage=document.querySelector('#model-stage'),canvas=document.querySelector('#model-canvas');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let renderer;
 try{const context=canvas.getContext('webgl2',{antialias:true,alpha:true,powerPreference:'low-power'});if(!context)throw Error();renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});}catch{throw Error('WebGL unavailable');}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x090e13,0);renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.9;
 const scene=new Scene(),assembly=new Group();scene.add(assembly);
 // A small procedural studio, filtered once. Softboxes stay visible in the glass.
 const room=new RoomEnvironment();const pmrem=new PMREMGenerator(renderer),environment=pmrem.fromScene(room,.025,.1,100);scene.environment=environment.texture;scene.environmentIntensity=.35;room.dispose();pmrem.dispose();
 scene.add(new AmbientLight(0xb7cbd8,.15));const light=new DirectionalLight(0xfff1e0,1.7);light.position.set(-.5,.8,.6);scene.add(light);
 const rim=new DirectionalLight(0x9fc6e8,.8);rim.position.set(.6,.35,-.7);scene.add(rim);
 const camera=new PerspectiveCamera(31,1,.01,10);
 const grain=document.createElement('canvas');grain.width=grain.height=64;const grain2d=grain.getContext('2d'),pixels=grain2d.createImageData(64,64);let seed=139;
 for(let i=0;i<pixels.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const value=220+(seed%35);pixels.data.set([value,value,value,255],i);}grain2d.putImageData(pixels,0,0);
 const roughnessMap=new CanvasTexture(grain);roughnessMap.wrapS=roughnessMap.wrapT=RepeatWrapping;
 const body=new MeshPhysicalMaterial({color:0xc7cbc4,roughness:.48,roughnessMap,bumpMap:roughnessMap,bumpScale:.000015,metalness:0,clearcoat:.15,clearcoatRoughness:.6,vertexColors:true,envMapIntensity:.85});
 const arm=new MeshStandardMaterial({color:0x536772,roughness:.56,metalness:0,vertexColors:true,envMapIntensity:.85});
 const plate=new MeshStandardMaterial({color:0xc7ccc8,roughness:.42,metalness:.08,vertexColors:true,envMapIntensity:.7});
 const face=new MeshStandardMaterial({color:0x172028,roughness:.38,metalness:.15,vertexColors:true});
 const lens=new MeshPhysicalMaterial({color:0x090f15,roughness:.035,metalness:0,clearcoat:1,clearcoatRoughness:.025,envMapIntensity:2.3});
 const lensCentre=new MeshPhysicalMaterial({color:0x030a10,roughness:.12,metalness:0,clearcoat:1,envMapIntensity:1.1});
 const highlight=new MeshStandardMaterial({color:0xb1d0dc,roughness:.48,vertexColors:true});
 const ropeMaterial=new MeshStandardMaterial({color:0x8a989c,roughness:1,bumpMap:roughnessMap,bumpScale:.00006});
 const activeFill=new MeshBasicMaterial({color:0x8fc3e3,opacity:.075,transparent:true,side:DoubleSide,depthWrite:false});
 const selectedFill=new MeshBasicMaterial({color:0x8fc3e3,opacity:.16,transparent:true,side:DoubleSide,depthWrite:false});
 const activeLine=new LineBasicMaterial({color:0x8fc3e3,transparent:true,opacity:.55});
 const parts={},meshes=[],geometries=new Set(),materials=new Set([body,arm,plate,face,lens,lensCentre,highlight,ropeMaterial,activeFill,selectedFill,activeLine]);
 let destroyed=false,lost=false,visible=true,frame=0,last=0,totalDraws=0,activeTime=0,lastDraw=0,drift=false,interacted=false,explode=0,explodeTarget=0,showFov=false,selectedPart=null;
 let priorDistance=.49;
 let targetOrbit=null;
 let yaw=.48,pitch=.78,distance=.6,velocityX=0,velocityY=0,settle=reduced.matches?1:0;
 const pointers=new Map();let start=null,pinchDistance=0;
 const defaults={yaw:.48,pitch:.78,distance:.6};
 const podPositions={centre:new Vector3(0,.045,.1081),left:new Vector3(-.0936,.045,-.054),right:new Vector3(.0936,.045,-.054)};
 const normals={centre:new Vector3(0,0,1),left:new Vector3(-.866,0,-.5),right:new Vector3(.866,0,-.5)};
 const offsets={housing:new Vector3(),camera_centre:new Vector3(0,0,.045),camera_left:new Vector3(-.04,0,-.023),camera_right:new Vector3(.04,0,-.023),plate_top:new Vector3(0,.045,0),plate_bottom:new Vector3(0,-.045,0)};
 const loader=new GLTFLoader();
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
  const dark=m.material.name==='Camera face';const mesh=new Mesh(geometry,dark?face:m.material.name==='Secondary plastic'?arm:name.startsWith('plate')?plate:body);mesh.userData={part:name,original:mesh.material};meshes.push(mesh);parts[name].add(mesh);

 });
 // Release loader resources after baking the six logical groups into metre coordinates.
 gltf.scene.traverse(m=>{if(m.isMesh){m.geometry.dispose();m.material.dispose();}});gltf=null;
 const line=(points,material)=>{const g=new BufferGeometry().setFromPoints(points);geometries.add(g);return new Line(g,material);};
 // Concentric material detail remains inside the existing 49mm pod face.
 for(const id of ['left','centre','right']){
  const normal=normals[id],centre=podPositions[id],group=parts['camera_'+id];
  const optical=(geometry,material,lift)=>{geometries.add(geometry);const mesh=new Mesh(geometry,material);mesh.position.copy(centre).addScaledVector(normal,lift);mesh.quaternion.setFromUnitVectors(new Vector3(0,0,1),normal);mesh.userData={part:'camera_'+id,original:material,optical:true};group.add(mesh);meshes.push(mesh);};
  optical(new RingGeometry(.0174,.0244,48),face,.00018);
  optical(new RingGeometry(.0145,.0173,48),lensCentre,.0003);
  const glass=new SphereGeometry(.0145,40,20);glass.scale(1,1,.14);optical(glass,lens,.0004);
  optical(new CircleGeometry(.006,40),lensCentre,.0025);
 }
 const bridle=new Group();assembly.add(bridle);
 const rope=(a,b)=>{const middle=a.clone().lerp(b,.5);middle.z+=.006;const g=new TubeGeometry(new QuadraticBezierCurve3(a,middle,b),12,.0004,5,false);geometries.add(g);return new Mesh(g,ropeMaterial);};
 for(const x of [-.0055,.0055])bridle.add(rope(new Vector3(x,.075,0),new Vector3(x*110,.7,.1)));
 bridle.add(rope(new Vector3(0,-.075,0),new Vector3(0,-1.2,0)));
 const sectors={};
 for(const id of ['left','centre','right']){
  const group=new Group(),heading=Math.atan2(normals[id].x,normals[id].z),positions=[],colours=[];
  const inner=.105,outer=.18,lower=.005,upper=.085;
  for(let i=0;i<40;i++){
   const a=heading+(i/40-.5)*Math.PI*2/3,b=heading+((i+1)/40-.5)*Math.PI*2/3;
   const p=(r,t,y)=>[Math.sin(t)*r,y,Math.cos(t)*r];
   for(const triangle of [[p(inner,a,.045),p(outer,a,upper),p(outer,b,upper)],[p(inner,a,.045),p(outer,b,upper),p(inner,b,.045)],[p(inner,a,.045),p(outer,b,lower),p(outer,a,lower)],[p(inner,a,.045),p(inner,b,.045),p(outer,b,lower)]]){
    for(const vertex of triangle){positions.push(...vertex);const radius=Math.hypot(vertex[0],vertex[2]);colours.push(.56,.76,.89, radius<.15?.24:.025);}
   }
  }
  const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(positions,3));geometry.setAttribute('color',new Float32BufferAttribute(colours,4));geometries.add(geometry);
  const material=new MeshBasicMaterial({color:[0x8fc3e3,0xadc6d4,0x6fa9c9][['centre','right','left'].indexOf(id)],vertexColors:true,transparent:true,side:DoubleSide,depthWrite:false,opacity:.7});materials.add(material);
  const fill=new Mesh(geometry,material);group.add(fill);
  const boundaries=[];for(const side of [-1,1]){const angle=heading+side*Math.PI/3;boundaries.push(new Vector3(Math.sin(angle)*inner,.045,Math.cos(angle)*inner),new Vector3(Math.sin(angle)*outer,upper,Math.cos(angle)*outer));}
  const outline=line([boundaries[0],boundaries[1]],activeLine);group.add(outline);
  const pod=podPositions[id];group.add(line([pod,new Vector3(normals[id].x*outer,.045,normals[id].z*outer)],activeLine));
  assembly.add(group);sectors[id]={group,fill,outline};group.visible=false;
 }
 const anchors={left:podPositions.left,centre:podPositions.centre,right:podPositions.right,eye:new Vector3(.0055,.075,0),housing:new Vector3(.048,-.025,.013)};
 const partFor=id=>['left','centre','right'].includes(id)?'camera_'+id:id==='eye'?'plate_top':'housing';
 function highlightPart(id,rotate=true){touch();selectedPart=id;for(const mesh of meshes)mesh.material=mesh.userData.part===partFor(id)&&!mesh.userData.optical&&mesh.userData.original!==face?highlight:mesh.userData.original;
  if(rotate&&normals[id]){const target=Math.atan2(normals[id].x,normals[id].z)+.12;targetOrbit={yaw:yaw+((target-yaw+Math.PI*3)%(Math.PI*2)-Math.PI),pitch:showFov?.65:.35,distance:showFov?.8:.6};}
  updateSectors();}
 function updateSectors(){for(const [id,s]of Object.entries(sectors)){s.group.visible=showFov;s.fill.material.opacity=selectedPart===id?1:.6;}request();}
 function updateLabels(){
  const rect=stage.getBoundingClientRect(),mobile=innerWidth<=760;
  const projected=[];
  for(const [id,anchor]of Object.entries(anchors)){
   const point=anchor.clone();assembly.localToWorld(point);
   const facing=!normals[id]||normals[id].clone().applyQuaternion(assembly.quaternion).dot(camera.position.clone().sub(point).normalize())>0;
   const p=point.project(camera),label=stage.querySelector('[data-part="'+id+'"]'),path=stage.querySelector('[data-leader="'+id+'"]');label.classList.toggle('facing-away',!facing);path.style.opacity=facing?'.7':'0';
   projected.push({id,label,path,facing,x:(p.x*.5+.5)*rect.width,y:(-p.y*.5+.5)*rect.height});
  }
  if(mobile){for(const p of projected)p.path.setAttribute('d','');return;}
  const cx=rect.width*.68;
  let minX=Infinity,maxX=-Infinity;
  for(const x of [-.107,.107])for(const y of [-.075,.078])for(const z of [-.08,.108]){const point=new Vector3(x,y,z);assembly.localToWorld(point);point.project(camera);const sx=(point.x*.5+.5)*rect.width;minX=Math.min(minX,sx);maxX=Math.max(maxX,sx);}
  for(const side of [-1,1]){
   const list=projected.filter(p=>(p.x<cx?-1:1)===side).sort((a,b)=>a.y-b.y);
   let lastY=82;
   for(let i=0;i<list.length;i++){
    const p=list[i],height=p.label.offsetHeight,width=p.label.offsetWidth;
    const top=Math.max(lastY,Math.min(p.y-height/2,rect.height-175-(list.length-i-1)*54));lastY=top+height+12;
    const left=side<0?Math.max(rect.width*.405,minX-width-18):Math.min(rect.width-width-28,maxX+18);
    p.label.style.left=left+'px';p.label.style.top=top+'px';
    const lx=side<0?left+width:left,ly=top+height/2,elbow=lx-side*16;
    p.path.setAttribute('d',p.facing?`M ${p.x} ${p.y} L ${elbow} ${ly} L ${lx} ${ly}`:'');
   }
  }
 }
 function draw(now){
  frame=0;if(destroyed||lost||!visible||document.hidden){last=0;return;}
  const elapsed=last?(now-last)/1000:1/60,dt=Math.min(elapsed,.04);last=now;activeTime+=elapsed;
  if(reduced.matches){settle=1;explode=explodeTarget;drift=false;velocityX=velocityY=0;}
  if(drift&&activeTime<5)yaw+=dt*.022;else drift=false;
  if(!pointers.size){yaw+=velocityX;pitch+=velocityY;velocityX*=.84;velocityY*=.84;}
  if(targetOrbit){const t=reduced.matches?1:Math.min(1,dt*8);yaw+=(targetOrbit.yaw-yaw)*t;pitch+=(targetOrbit.pitch-pitch)*t;distance+=(targetOrbit.distance-distance)*t;if(Math.abs(targetOrbit.yaw-yaw)+Math.abs(targetOrbit.pitch-pitch)+Math.abs(targetOrbit.distance-distance)<.001){({yaw,pitch,distance}=targetOrbit);targetOrbit=null;}}
  pitch=Math.max(-.6,Math.min(1.1,pitch));
  settle=Math.min(1,settle+dt/ .8);const eased=1-Math.pow(1-settle,3);
  assembly.rotation.y=(1-eased)*-.18;assembly.position.y=(1-eased)*.018;
  if(Math.abs(explodeTarget-explode)<.001)explode=explodeTarget;else explode+=(explodeTarget-explode)*Math.min(1,dt*13);
  for(const [name,g]of Object.entries(parts))g.position.copy(offsets[name]).multiplyScalar(explode);
  for(const [id,s]of Object.entries(sectors))s.group.position.copy(offsets['camera_'+id]).multiplyScalar(explode);
  bridle.visible=explode<.02;
  camera.position.set(Math.sin(yaw)*Math.cos(pitch)*distance,Math.sin(pitch)*distance,Math.cos(yaw)*Math.cos(pitch)*distance);camera.lookAt(0,0,0);camera.updateMatrixWorld();assembly.updateMatrixWorld(true);
  if(drift&&settle===1&&!pointers.size&&now-lastDraw<33){request();return;}lastDraw=now;renderer.render(scene,camera);stage.classList.add('ready');totalDraws++;updateLabels();
  if(targetOrbit||drift||settle<1||explode!==explodeTarget||Math.abs(velocityX)+Math.abs(velocityY)>.0001)request();else last=0;
 }
 function request(){if(!frame&&!destroyed&&!lost&&visible&&!document.hidden)frame=requestAnimationFrame(draw);}
 function touch(){interacted=true;drift=false;}
 function resize(){const r=stage.getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.setViewOffset(r.width,r.height,innerWidth>760?-r.width*.18:0,0,r.width,r.height);camera.updateProjectionMatrix();request();}
 const observer=new ResizeObserver(resize);observer.observe(stage);
 const intersection=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)request();else{cancelAnimationFrame(frame);frame=0;last=0;}},{threshold:0});intersection.observe(stage);
 const visibility=()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;last=0;}else request();};document.addEventListener('visibilitychange',visibility);
 const raycaster=new Raycaster();
 const clickPart=e=>{const r=canvas.getBoundingClientRect();raycaster.setFromCamera(new Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(meshes,false)[0];if(hit){const name=hit.object.userData.part,id=name.replace('camera_','');selectPart(name.startsWith('camera_')?id:name.startsWith('plate')?'eye':'housing');}};
 canvas.addEventListener('pointerdown',e=>{touch();targetOrbit=null;canvas.focus({preventScroll:true});pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});start={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);velocityX=velocityY=0;if(pointers.size===2){const [a,b]=[...pointers.values()];pinchDistance=Math.hypot(a.x-b.x,a.y-b.y);}});
 canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const prev=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2){const [a,b]=[...pointers.values()],d=Math.hypot(a.x-b.x,a.y-b.y);if(pinchDistance)distance=Math.max(.4,Math.min(.8,distance*pinchDistance/d));pinchDistance=d;}else{velocityX=-(e.clientX-prev.x)*.006;velocityY=e.pointerType==='touch'?0:(e.clientY-prev.y)*.004;yaw+=velocityX;pitch+=velocityY;}request();});
 const end=e=>{const click=pointers.size===1&&start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)<5;pointers.delete(e.pointerId);pinchDistance=0;if(e.type==='pointerup'&&click)clickPart(e);request();};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);velocityX=velocityY=0;});
 canvas.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();touch();distance=Math.max(.4,Math.min(.8,distance+e.deltaY*.001));request();},{passive:false});
 canvas.addEventListener('keydown',e=>{const keys={ArrowLeft:()=>yaw-=.12,ArrowRight:()=>yaw+=.12,ArrowUp:()=>pitch+=.08,ArrowDown:()=>pitch-=.08,'+':()=>distance=Math.max(.4,distance-.025),'=':()=>distance=Math.max(.4,distance-.025),'-':()=>distance=Math.min(.8,distance+.025)};if(keys[e.key]){e.preventDefault();touch();targetOrbit=null;keys[e.key]();request();}});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;cancelAnimationFrame(frame);frame=0;stage.classList.remove('ready');document.querySelector('#model-fallback').hidden=false;});
 canvas.addEventListener('webglcontextrestored',()=>{lost=false;request();document.querySelector('#model-fallback').hidden=true;});
 const api={highlight:highlightPart,toggleFov(value){touch();showFov=value;targetOrbit={yaw,pitch:value?.65:defaults.pitch,distance:value?.8:defaults.distance};updateSectors();},explode(value){touch();explodeTarget=value?1:0;request();},reset(){touch();showFov=false;selectedPart=null;targetOrbit={...defaults};velocityX=velocityY=0;for(const mesh of meshes)mesh.material=mesh.userData.original;updateSectors();},get stats(){return {draws:totalDraws,visible,lost,interacted,cameraViews:['left','centre','right'],selectedPart,exploded:explode,geometries:renderer.info.memory.geometries,calls:renderer.info.render.calls};},dispose(){destroyed=true;cancelAnimationFrame(frame);observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);for(const g of geometries)g.dispose();for(const m of materials)m.dispose();roughnessMap.dispose();environment.dispose();renderer.dispose();}};
 const pagehide=e=>{if(!e.persisted)api.dispose();};window.addEventListener('pagehide',pagehide);
 resize();updateSectors();window.acornModel=api;return api;
}
