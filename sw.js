const CACHE='asnaf-v5-20261123';
const IMG='asnaf-img';
const IMG_MAX=1500;
const ASSETS=['./','index.html','qrcode.js','jsbarcode.min.js','zxing.min.js','data.pack','manifest.webmanifest','icon-192.png','icon-512.png','fonts/montserrat-latin.woff2','fonts/tajawal-400-arabic.woff2','fonts/tajawal-500-arabic.woff2','fonts/tajawal-700-arabic.woff2','fonts/tajawal-800-arabic.woff2','fonts/tajawal-400-latin.woff2','fonts/tajawal-500-latin.woff2','fonts/tajawal-700-latin.woff2','fonts/tajawal-800-latin.woff2'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS).catch(()=>{})));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE&&k!==IMG).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
async function trimImg(){const c=await caches.open(IMG);const ks=await c.keys();if(ks.length>IMG_MAX)for(const k of ks.slice(0,ks.length-IMG_MAX))await c.delete(k);}
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const url=new URL(r.url);
  // product images from Nahdi Online: keep a copy so they show offline too
  if(url.hostname==='ecombe.nahdionline.com'){
    e.respondWith(caches.open(IMG).then(c=>c.match(r).then(hit=>hit||fetch(r).then(res=>{if(res.ok||res.type==='opaque'){c.put(r,res.clone());trimImg();}return res;}))).catch(()=>Response.error()));
    return;
  }
  if(url.origin!==location.origin)return;
  const isDoc=r.mode==='navigate'||url.pathname.endsWith('/')||url.pathname.endsWith('index.html');
  if(isDoc){
    e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put('index.html',cp));return res;})
      .catch(()=>caches.match('index.html',{ignoreSearch:true})));
    return;
  }
  e.respondWith(caches.match(r,{ignoreSearch:true}).then(hit=>hit||fetch(r).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put(r,cp));return res;})));
});
