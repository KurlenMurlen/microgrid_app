// Basic service worker for offline-first caching
const CACHE_NAME = 'microgrid-cache-v1';
const PRECACHE = [
  '/',
  '/static/styles.css',
  '/static/favicon.svg',
];
self.addEventListener('install', (e)=>{
  e.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(PRECACHE)));
});
self.addEventListener('activate', (e)=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))));
});
self.addEventListener('fetch', (e)=>{
  const url = new URL(e.request.url);
  // Runtime cache static and model zip
  const isStatic = url.pathname.startsWith('/static/') || url.pathname === '/api/vosk/model';
  if (e.request.method === 'GET' && (isStatic || PRECACHE.includes(url.pathname))) {
    e.respondWith(
      caches.open(CACHE_NAME).then(async cache => {
        const cached = await cache.match(e.request);
        const fetchPromise = fetch(e.request).then(resp => {
          try { if (resp && resp.status === 200) cache.put(e.request, resp.clone()); } catch {}
          return resp;
        }).catch(()=>cached);
        return cached || fetchPromise;
      })
    );
  }
});
