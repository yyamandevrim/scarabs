/* Local, on-demand CAD viewer. Bundle once; no runtime CDN or build step. */
import {Scene,Color,PerspectiveCamera,WebGLRenderer,AmbientLight,DirectionalLight,Group,Mesh,MeshStandardMaterial,MeshPhysicalMaterial,MeshBasicMaterial,LineBasicMaterial,Line,LineSegments,EdgesGeometry,PlaneGeometry,BufferGeometry,Float32BufferAttribute,Vector2,Vector3,Raycaster,DoubleSide,CanvasTexture,RepeatWrapping,SRGBColorSpace,TubeGeometry,QuadraticBezierCurve3,CircleGeometry,RingGeometry,SphereGeometry,ACESFilmicToneMapping} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {loadStudio,podFinish,printTexture,lensNormal} from './landing-surfaces.js';
export async function mountModel({selectPart}){
 const stage=document.querySelector('#model-stage'),canvas=document.querySelector('#model-canvas');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let renderer;
 try{const context=canvas.getContext('webgl2',{antialias:true,alpha:true,powerPreference:'low-power'});if(!context)throw Error();renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});}catch{throw Error('WebGL unavailable');}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x090e13,0);renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.9;
 const scene=new Scene(),assembly=new Group();scene.add(assembly);
 // Filtering happens offline; the small cube already includes its roughness mip chain.
 const [environment,wordmark]=await Promise.all([loadStudio(),printTexture()]);scene.environment=environment;scene.environmentIntensity=.55;
 scene.add(new AmbientLight(0xb7cbd8,.15));const light=new DirectionalLight(0xfff1e0,1.7);light.position.set(-.5,.8,.6);scene.add(light);
 const rim=new DirectionalLight(0x9fc6e8,.8);rim.position.set(.6,.35,-.7);scene.add(rim);
 const camera=new PerspectiveCamera(31,1,.01,10);
 const grain=document.createElement('canvas');grain.width=grain.height=64;const grain2d=grain.getContext('2d'),pixels=grain2d.createImageData(64,64);let seed=139;
 for(let i=0;i<pixels.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const value=220+(seed%35);pixels.data.set([value,value,value,255],i);}grain2d.putImageData(pixels,0,0);
 const roughnessMap=new CanvasTexture(grain);roughnessMap.wrapS=roughnessMap.wrapT=RepeatWrapping;
 const body=new MeshStandardMaterial({color:0xcfd2ca,roughness:.65,roughnessMap,bumpMap:roughnessMap,bumpScale:.00004,metalness:0,vertexColors:true,envMapIntensity:.85});
 const arm=new MeshStandardMaterial({color:0x2a3138,roughness:.45,metalness:0,vertexColors:true,envMapIntensity:.9,transparent:false,opacity:1,depthWrite:true});
 const plate=new MeshStandardMaterial({color:0xc7ccc8,roughness:.55,metalness:.08,vertexColors:true,envMapIntensity:.7});
 const face=new MeshStandardMaterial({color:0x0b1016,roughness:.68,metalness:0,vertexColors:true,envMapIntensity:.45});
 const opticalNormal=lensNormal();
 const lens=new MeshPhysicalMaterial({color:0x090f15,roughness:.08,metalness:0,clearcoat:.8,clearcoatRoughness:.06,envMapIntensity:.8,specularIntensity:.65,normalMap:opticalNormal,clearcoatNormalMap:opticalNormal,transparent:true,opacity:.85});
 const lensCentre=new MeshStandardMaterial({color:0x030a10,roughness:.18,metalness:0,envMapIntensity:.15});
 const finish=podFinish(),back=new MeshStandardMaterial({color:0xcfd2cc,map:finish.map,roughness:.62,bumpMap:finish.bump,bumpScale:.00013,vertexColors:true,envMapIntensity:.9});
 const print=new MeshStandardMaterial({map:wordmark,transparent:true,roughness:.8,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1});
 const seamLine=new LineBasicMaterial({color:0x66706b,transparent:true,opacity:.2}),selectionLine=new LineBasicMaterial({color:0x8fc3e3,transparent:true,opacity:.9});
 const ropeMaterial=new MeshStandardMaterial({color:0x8a989c,roughness:1,bumpMap:roughnessMap,bumpScale:.00006});
 const activeLine=new LineBasicMaterial({color:0x8fc3e3,transparent:true,opacity:.55});
 const parts={},meshes=[],geometries=new Set(),materials=new Set([body,arm,plate,face,lens,lensCentre,back,print,seamLine,selectionLine,ropeMaterial,activeLine]);
 let warmed=false,destroyed=false,lost=false,visible=true,frame=0,last=0,totalDraws=0,interacted=false,showFov=false,selectedPart=null;
 const selectionEdges=[],labelRay=new Raycaster();let resizeFrame=0,lastWidth=0,lastHeight=0;
 let targetOrbit=null;
 let yaw=1.05,pitch=.5,distance=.64,velocityX=0,velocityY=0,settle=reduced.matches?1:0;
 const zoomMin=()=>showFov?.88:(innerWidth>760?.58:.52);
 const pointers=new Map();let start=null,pinchDistance=0;
 const defaults={yaw:1.05,pitch:.5,distance:.64};
 const podPositions={centre:new Vector3(0,.045,.1081),left:new Vector3(-.0936,.045,-.054),right:new Vector3(.0936,.045,-.054)};
 const normals={centre:new Vector3(0,0,1),left:new Vector3(-Math.sqrt(3)/2,0,-.5),right:new Vector3(Math.sqrt(3)/2,0,-.5)};
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
  const dark=m.material.name==='Camera face',isBack=m.material.name==='Pod back',isArm=m.material.name==='Secondary plastic';
  if(isBack){const id=name.replace('camera_',''),normal=normals[id],uv=[];for(let i=0;i<geometry.attributes.position.count;i++){const x=geometry.attributes.position.getX(i),y=geometry.attributes.position.getY(i),z=geometry.attributes.position.getZ(i);uv.push((x*normal.z-z*normal.x)/.066+.5,(y-.045)/.066+.5);}geometry.setAttribute('uv',new Float32BufferAttribute(uv,2));}
  const mesh=new Mesh(geometry,dark?face:isBack?back:isArm?arm:name.startsWith('plate')?plate:body);mesh.userData={part:name,original:mesh.material};meshes.push(mesh);parts[name].add(mesh);
  if((name.startsWith('camera_')&&!dark&&!isArm)||name==='housing'||name==='plate_top'){const edges=new EdgesGeometry(geometry,30);geometries.add(edges);const selected=new LineSegments(edges,selectionLine);selected.visible=false;selected.userData.part=name;parts[name].add(selected);selectionEdges.push(selected);if(isBack)parts[name].add(new LineSegments(edges,seamLine));}

 });
 // Release loader resources after baking the six logical groups into metre coordinates.
 gltf.scene.traverse(m=>{if(m.isMesh){m.geometry.dispose();m.material.dispose();}});gltf=null;
 const line=(points,material)=>{const g=new BufferGeometry().setFromPoints(points);geometries.add(g);return new Line(g,material);};
 // Concentric material detail remains inside the existing 49mm pod face.
 for(const id of ['left','centre','right']){
  const normal=normals[id],centre=podPositions[id],group=parts['camera_'+id];
  const optical=(geometry,material,lift)=>{geometries.add(geometry);const mesh=new Mesh(geometry,material);mesh.position.copy(centre).addScaledVector(normal,lift);mesh.quaternion.setFromUnitVectors(new Vector3(0,0,1),normal);mesh.userData={part:'camera_'+id,original:material,optical:true};group.add(mesh);meshes.push(mesh);};
  optical(new RingGeometry(.0174,.0244,48),face,.00018);
  optical(new RingGeometry(.0144,.0173,64),lensCentre,.0003);
  optical(new RingGeometry(.0132,.0144,64),face,.00045);
  const glass=new SphereGeometry(.0132,40,20);glass.scale(1,1,.025);const glassUv=[];for(let i=0;i<glass.attributes.position.count;i++)glassUv.push(glass.attributes.position.getX(i)/.0264+.5,glass.attributes.position.getY(i)/.0264+.5);glass.setAttribute('uv',new Float32BufferAttribute(glassUv,2));optical(glass,lens,.0006);
  optical(new CircleGeometry(.0048,40),lensCentre,.00055);
 }
 const printGeometry=new PlaneGeometry(.032,.0104);geometries.add(printGeometry);const mark=new Mesh(printGeometry,print);mark.rotation.x=-Math.PI/2;mark.position.set(0,.07512,.023);assembly.add(mark);
 const bridle=new Group();assembly.add(bridle);
 const rope=(a,b)=>{const middle=a.clone().lerp(b,.5);middle.z+=.0015;const g=new TubeGeometry(new QuadraticBezierCurve3(a,middle,b),12,.0004,5,false);geometries.add(g);return new Mesh(g,ropeMaterial);};
 for(const x of [-.0055,.0055])bridle.add(rope(new Vector3(x,.074,0),new Vector3(x*60,.9,.04)));
 bridle.add(rope(new Vector3(.0055,-.075,0),new Vector3(.0055,-1.2,0)));
 const sectors={};
 for(const id of ['left','centre','right']){
  const group=new Group(),heading=Math.atan2(normals[id].x,normals[id].z),positions=[],inner=.065,outer=.19;
  const p=(r,t)=>[Math.sin(t)*r,.045,Math.cos(t)*r];
  for(let i=0;i<48;i++){const a=heading+(i/48-.5)*Math.PI*2/3,b=heading+((i+1)/48-.5)*Math.PI*2/3;positions.push(...p(inner,a),...p(outer,a),...p(outer,b),...p(inner,a),...p(outer,b),...p(inner,b));}
  const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(positions,3));geometries.add(geometry);
  const material=new MeshBasicMaterial({color:[0x8fc3e3,0xb2cbd9,0x72a8ca][['centre','right','left'].indexOf(id)],transparent:true,side:DoubleSide,depthWrite:false,opacity:.08});materials.add(material);
  const fill=new Mesh(geometry,material);group.add(fill);
  for(const side of [-1,1]){const angle=heading+side*Math.PI/3;group.add(line([new Vector3(...p(inner,angle)),new Vector3(...p(outer,angle))],activeLine));}
  const arc=[];for(let i=0;i<=48;i++)arc.push(new Vector3(...p(outer,heading+(i/48-.5)*Math.PI*2/3)));group.add(line(arc,activeLine));
  group.add(line([podPositions[id],new Vector3(...p(outer,heading))],activeLine));assembly.add(group);sectors[id]={group,fill};group.visible=false;
 }
 const anchors={left:podPositions.left,centre:podPositions.centre,right:podPositions.right,eye:new Vector3(.0055,.075,0),housing:new Vector3(.025,-.025,.0381)};
 const partFor=id=>!id?null:['left','centre','right'].includes(id)?'camera_'+id:id==='eye'?'plate_top':'housing';
 function highlightPart(id,rotate=true){touch();selectedPart=id;for(const edge of selectionEdges)edge.visible=edge.userData.part===partFor(id);
  if(rotate&&normals[id]){const target=Math.atan2(normals[id].x,normals[id].z)+.12;targetOrbit={yaw:yaw+Math.atan2(Math.sin(target-yaw),Math.cos(target-yaw)),pitch:showFov?1.05:.35,distance:showFov?.92:.64};}
  updateSectors();}
 function updateSectors(){stage.classList.toggle('fields-visible',showFov);for(const [id,s]of Object.entries(sectors)){s.group.visible=showFov;s.fill.material.opacity=selectedPart===id?.18:.08;}request();}
 function updateLabels(){
  const rect=stage.getBoundingClientRect(),mobile=innerWidth<=760;
  const projected=[];
  for(const [id,anchor]of Object.entries(anchors)){
   const point=anchor.clone();assembly.localToWorld(point);
   const surfaceNormal=normals[id]||(id==='eye'?new Vector3(0,1,0):new Vector3(0,0,1));
   const toPoint=point.clone().sub(camera.position),distance=toPoint.length();labelRay.set(camera.position,toPoint.normalize());labelRay.far=Math.max(0,distance-.002);
   const facing=surfaceNormal.clone().applyQuaternion(assembly.quaternion).dot(camera.position.clone().sub(point).normalize())>-.25&&!labelRay.intersectObjects(meshes,false).length;
   const p=point.project(camera),label=stage.querySelector('[data-part="'+id+'"]'),path=stage.querySelector('[data-leader="'+id+'"]');label.classList.toggle('facing-away',!!normals[id]&&!facing);path.style.opacity=facing?'.7':'0';
   projected.push({id,label,path,facing,x:(p.x*.5+.5)*rect.width,y:(-p.y*.5+.5)*rect.height});
  }
  for(const [id,normal]of Object.entries(normals)){const point=normal.clone().multiplyScalar(.166);point.y=.045;assembly.localToWorld(point);point.project(camera);const label=stage.querySelector('[data-fov-label="'+id+'"]');label.hidden=!showFov||!mobile;label.style.left=(point.x*.5+.5)*rect.width+'px';label.style.top=(-point.y*.5+.5)*rect.height+'px';}
  if(mobile){for(const p of projected)p.path.setAttribute('d','');return;}
  if(showFov){
   for(const p of projected){
    if(normals[p.id]){const point=normals[p.id].clone().multiplyScalar(.166);point.y=.045;assembly.localToWorld(point);point.project(camera);p.label.style.left=((point.x*.5+.5)*rect.width-p.label.offsetWidth/2)+'px';p.label.style.top=((-point.y*.5+.5)*rect.height-p.label.offsetHeight/2)+'px';p.path.setAttribute('d','');}
    else{const left=rect.width-p.label.offsetWidth-28,top=rect.height*(p.id==='eye'?.3:.49);p.label.style.left=left+'px';p.label.style.top=top+'px';p.path.setAttribute('d',p.facing?`M ${p.x} ${p.y} L ${left-16} ${top+22} L ${left} ${top+22}`:'');}
   }return;
  }
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
    p.path.setAttribute('d',p.facing?`M ${p.x} ${p.y}m -2 0 a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0 M ${p.x} ${p.y} L ${elbow} ${ly} L ${lx} ${ly}`:'');
   }
  }
 }
 function draw(now){
  frame=0;if(destroyed||lost||!visible||document.hidden){last=0;return;}
  const elapsed=last?(now-last)/1000:1/60,dt=Math.min(elapsed,.04);last=now;
  if(reduced.matches){settle=1;velocityX=velocityY=0;}
  if(!pointers.size){const damping=Math.exp(-elapsed*11),travel=(1-damping)/(1-Math.exp(-11/60));yaw+=velocityX*travel;pitch+=velocityY*travel;velocityX*=damping;velocityY*=damping;}
  if(targetOrbit){const t=reduced.matches?1:1-Math.exp(-elapsed*12);yaw+=(targetOrbit.yaw-yaw)*t;pitch+=(targetOrbit.pitch-pitch)*t;distance+=(targetOrbit.distance-distance)*t;if(Math.abs(targetOrbit.yaw-yaw)+Math.abs(targetOrbit.pitch-pitch)+Math.abs(targetOrbit.distance-distance)<.001){({yaw,pitch,distance}=targetOrbit);targetOrbit=null;}}
  pitch=Math.max(-.6,Math.min(1.1,pitch));
  settle=Math.min(1,settle+elapsed/1.6);const eased=1-Math.pow(1-settle,3);
  assembly.rotation.y=Math.sin(Math.PI*(settle*settle*(3-2*settle)))*.35;assembly.position.y=0;
  camera.position.set(Math.sin(yaw)*Math.cos(pitch)*distance,Math.sin(pitch)*distance,Math.cos(yaw)*Math.cos(pitch)*distance);camera.lookAt(0,0,0);camera.updateMatrixWorld();assembly.updateMatrixWorld(true);
  renderer.render(scene,camera);stage.classList.add('ready');totalDraws++;updateLabels();
  if(targetOrbit||settle<1||Math.abs(velocityX)+Math.abs(velocityY)>.0001)request();else last=0;
 }
 function request(){if(warmed&&!frame&&!destroyed&&!lost&&visible&&!document.hidden)frame=requestAnimationFrame(draw);}
 function touch(){if(settle<1){yaw-=assembly.rotation.y;settle=1;assembly.rotation.y=0;}interacted=true;stage.classList.add('interacted');}
 function resize(){const r=stage.getBoundingClientRect();if(r.width===lastWidth&&r.height===lastHeight)return;lastWidth=r.width;lastHeight=r.height;renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.setViewOffset(r.width,r.height,innerWidth>760?-r.width*.18:0,0,r.width,r.height);camera.updateProjectionMatrix();request();}
 const observer=new ResizeObserver(()=>{if(!resizeFrame)resizeFrame=requestAnimationFrame(()=>{resizeFrame=0;resize();});});observer.observe(stage);
 const intersection=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible)request();else{cancelAnimationFrame(frame);frame=0;last=0;}},{threshold:0});intersection.observe(stage);
 const keyboardInput=()=>{delete canvas.dataset.pointer;};document.addEventListener('keydown',keyboardInput);
 const visibility=()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;last=0;}else request();};document.addEventListener('visibilitychange',visibility);
 const raycaster=new Raycaster();
 const clickPart=e=>{const r=canvas.getBoundingClientRect();raycaster.setFromCamera(new Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(meshes,false)[0];if(hit){const name=hit.object.userData.part,id=name.replace('camera_','');selectPart(name.startsWith('camera_')?id:name.startsWith('plate')?'eye':'housing');}};
 canvas.addEventListener('pointerdown',e=>{touch();targetOrbit=null;canvas.dataset.pointer='1';canvas.focus({preventScroll:true,focusVisible:false});pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});start={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);velocityX=velocityY=0;if(pointers.size===2){const [a,b]=[...pointers.values()];pinchDistance=Math.hypot(a.x-b.x,a.y-b.y);}});
 canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const prev=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2){const [a,b]=[...pointers.values()],d=Math.hypot(a.x-b.x,a.y-b.y);if(pinchDistance)distance=Math.max(zoomMin(),Math.min(.92,distance*pinchDistance/d));pinchDistance=d;}else{velocityX=-(e.clientX-prev.x)*.006;velocityY=e.pointerType==='touch'?0:(e.clientY-prev.y)*.004;yaw+=velocityX;pitch+=velocityY;}request();});
 const end=e=>{const click=pointers.size===1&&start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)<5;pointers.delete(e.pointerId);pinchDistance=0;if(e.type==='pointerup'&&click)clickPart(e);request();};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);velocityX=velocityY=0;});
 canvas.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();touch();targetOrbit=null;distance=Math.max(zoomMin(),Math.min(.92,distance+e.deltaY*.001));request();},{passive:false});
 canvas.addEventListener('keydown',e=>{delete canvas.dataset.pointer;const keys={ArrowLeft:()=>yaw-=.12,ArrowRight:()=>yaw+=.12,ArrowUp:()=>pitch+=.08,ArrowDown:()=>pitch-=.08,'+':()=>distance=Math.max(zoomMin(),distance-.025),'=':()=>distance=Math.max(zoomMin(),distance-.025),'-':()=>distance=Math.min(.92,distance+.025)};if(keys[e.key]){e.preventDefault();touch();targetOrbit=null;keys[e.key]();request();}});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;cancelAnimationFrame(frame);frame=0;stage.classList.remove('ready');document.querySelector('#model-fallback').hidden=false;});
 canvas.addEventListener('webglcontextrestored',()=>{lost=false;request();document.querySelector('#model-fallback').hidden=true;});
 const api={highlight:highlightPart,toggleFov(value){touch();showFov=value;targetOrbit={yaw,pitch:value?1.05:defaults.pitch,distance:value?.92:defaults.distance};updateSectors();},reset(){touch();showFov=false;selectedPart=null;targetOrbit={...defaults,yaw:yaw+Math.atan2(Math.sin(defaults.yaw-yaw),Math.cos(defaults.yaw-yaw))};velocityX=velocityY=0;for(const edge of selectionEdges)edge.visible=false;updateSectors();},get stats(){return {draws:totalDraws,visible,lost,interacted,cameraViews:['left','centre','right'],selectedPart,geometries:renderer.info.memory.geometries,calls:renderer.info.render.calls};},dispose(){destroyed=true;cancelAnimationFrame(frame);cancelAnimationFrame(resizeFrame);observer.disconnect();intersection.disconnect();document.removeEventListener('visibilitychange',visibility);document.removeEventListener('keydown',keyboardInput);for(const g of geometries)g.dispose();for(const m of materials)m.dispose();roughnessMap.dispose();finish.map.dispose();finish.bump.dispose();opticalNormal.dispose();wordmark.dispose();environment.dispose();renderer.dispose();}};
 const pagehide=e=>{if(!e.persisted)api.dispose();};window.addEventListener('pagehide',pagehide);
 resize();await renderer.compileAsync(scene,camera);warmed=true;updateSectors();window.acornModel=api;return api;
}
