/* CodeVocab service worker
   - Sayfalar: önce ağ, bağlantı yoksa önbellekteki uygulama kabuğu (/app).
   - Statik dosyalar (?v= ile sürümlü): önce önbellek, yoksa ağ.
   - /api/*: asla önbelleğe alınmaz (AI yanıtları her zaman canlı). */
const CACHE = "cv-shell-v3";
const SHELL = "/app";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.add(new Request(SHELL, { cache: "reload" }))).catch(() => {}),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;

  // Uygulama kabuğu (/app): önbellekteki sürüm ANINDA açılır, güncel sürüm arka planda indirilir.
  // Sunucu uykudan uyanırken (Vercel soğuk başlangıç) siyah ekranda beklemeyi bu önler.
  // Sorgu parametreli adresler (?q=, ?mode=, dil değişimi) her zaman ağdan gelir.
  const isShell = url.pathname === SHELL && (url.search === "" || url.search === "?source=pwa");
  if (req.mode === "navigate" && isShell) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const cached = await cache.match(SHELL);
        const network = fetch(req)
          .then((res) => {
            if (res.ok && !res.redirected) cache.put(SHELL, res.clone());
            return res;
          })
          .catch(() => cached);
        if (cached) {
          event.waitUntil(network);
          return cached;
        }
        return network;
      }),
    );
    return;
  }

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Yönlendirilmiş yanıtlar (/ → /app) önbelleğe yazılmaz; sadece temiz /app kabuğu
          if (res.ok && !res.redirected && url.pathname === SHELL) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(SHELL, copy));
          }
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true }).then((hit) => hit || caches.match(SHELL))),
    );
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then(
        (hit) =>
          hit ||
          fetch(req).then((res) => {
            if (res.ok && url.search.includes("v=")) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(req, copy));
            }
            return res;
          }),
      ),
    );
  }
});
