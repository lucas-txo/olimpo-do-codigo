// Service worker do Olimpo do Código: guarda o app para abrir offline e trata o toque nas notificações.
// Páginas e dados que mudam (index.html, noticias.js, config.js) vêm da internet primeiro e usam a cópia
// guardada só se estiver sem sinal ou muito lento. O resto (ícones etc.) vem direto da cópia guardada.
const V='olimpo-v2',SHELL=['./','./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
const guarda=(rq,r)=>{if(r&&r.ok){const cp=r.clone();caches.open(V).then(c=>c.put(rq,cp))}return r};
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);if(u.origin!==location.origin)return;
  const fresco=u.pathname.endsWith('/')||/\/(index\.html|noticias\.js|config\.js)$/.test(u.pathname);
  if(fresco){
    e.respondWith(new Promise(res=>{
      const t=setTimeout(()=>caches.match(e.request,{ignoreSearch:true}).then(h=>{if(h)res(h)}),4000);
      fetch(e.request).then(r=>{clearTimeout(t);res(guarda(e.request,r))})
        .catch(()=>{clearTimeout(t);caches.match(e.request,{ignoreSearch:true}).then(h=>res(h||Response.error()))});
    }));
    return}
  e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>guarda(e.request,r))));
});
self.addEventListener('notificationclick',e=>{
  e.notification.close();
  e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(l=>{for(const c of l){if('focus' in c)return c.focus()}return clients.openWindow('./index.html')}))});
