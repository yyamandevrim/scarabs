// Same v2 network-byte-order layout and CRC as station/station/lora/protocol.py.
export const fixture={station:1,boot:42,sequence:0,timestamp:1794664071,remaining:3591,contactAfter:12,event:'af27f33e9e244d9db8f18eb4276fd1ad',box:[.369347890218099,.016594286318178532,.9924474954605103,.7687586325186271],score:.5929273962974548,heading:0,hfov:120};
export const yaws={centre:0,right:120,left:-120};
export const cameraNames={centre:'Camera 1',right:'Camera 2',left:'Camera 3'};
export function bearing(camera){return (fixture.heading+yaws[camera]+360)%360;}
export function encodeSmoke(camera,sequence=0){
 const f=fixture,bytes=new Uint8Array(42),v=new DataView(bytes.buffer);bytes[0]=0xac;bytes[1]=0x21;v.setUint16(2,f.station);v.setUint32(4,f.boot);v.setUint16(8,sequence);v.setUint32(10,f.timestamp);v.setUint16(14,f.remaining);v.setUint16(16,0x8000|f.contactAfter);
 for(let i=0;i<16;i++)bytes[18+i]=parseInt(eventId(camera).slice(i*2,i*2+2),16);
 bytes[34]=['left','centre','right'].indexOf(camera)|128;v.setUint16(35,Math.round(bearing(camera)*100)%36000);bytes[37]=Math.round((f.box[2]-f.box[0])*255);bytes[38]=Math.round((f.box[3]-f.box[1])*255);bytes[39]=Math.round(f.score*100);
 let crc=0xffff;for(const value of bytes.slice(0,40)){crc^=value<<8;for(let i=0;i<8;i++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;crc&=0xffff;}v.setUint16(40,crc);return bytes;
}

export function encodeStatus(sequence=0,timestamp=fixture.timestamp,uptime=100,pending=0){
 const f=fixture,bytes=new Uint8Array(40),v=new DataView(bytes.buffer);bytes[0]=0xac;bytes[1]=0x24;v.setUint16(2,f.station);v.setUint32(4,f.boot);v.setUint16(8,sequence);v.setUint32(10,timestamp);v.setUint16(14,f.remaining);v.setUint16(16,0x8000|f.contactAfter);
 // The existing codec's test fixture supplies the camera-state bitmasks. This UI does not claim a stream count.
 bytes[18]=3;bytes[19]=0;v.setUint16(20,pending);v.setUint32(22,uptime);bytes[26]=255;v.setUint16(27,0);[-12000,0,12000].forEach((yaw,i)=>v.setInt16(29+i*2,yaw));bytes.set([120,120,120],35);
 let crc=0xffff;for(const value of bytes.slice(0,38)){crc^=value<<8;for(let i=0;i<8;i++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;crc&=0xffff;}v.setUint16(38,crc);return bytes;
}

// One current demonstration record drives the report, evidence and station panel.
export function eventId(){return fixture.event;}
export const demo=new EventTarget();
demo.camera='left';demo.decision=null;demo.received=false;
demo.select=function(camera){this.camera=camera;this.decision=null;this.received=false;this.dispatchEvent(new Event('change'));};
demo.decide=function(value){this.decision=value;this.dispatchEvent(new Event('change'));};
export const eventTime=()=>new Date(fixture.timestamp*1000).toISOString().slice(11,19)+' UTC';
