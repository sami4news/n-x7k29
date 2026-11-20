/* HOME PLUS+ — عامل الخدمة: يجعل الموقع يفتح بسرعة وبلا اتصال، ويتيح الإشعارات والتثبيت.
   القاعدة: الشبكة أولًا (لتصل آخر نسخة دائمًا)، فإن تأخرت أو انقطعت نرجع لآخر نسخة محفوظة. لا نلمس طلبات المواقع الأخرى ولا الصور الخارجية. */
const V = "hp-v1";
const SHELL = ["./", "index.html", "manifest.webmanifest"];
self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(caches.open(V).then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {})))));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
const key = u => new Request(u.origin + u.pathname);   /* بلا معاملات الاستعلام: لا تتراكم نسخ news.json?123 */
async function netFirst(req, ms) {
  const u = new URL(req.url), cache = await caches.open(V);
  const net = fetch(req).then(r => { if (r && r.ok) cache.put(key(u), r.clone()).catch(() => {}); return r; });
  try {
    const r = await Promise.race([net, new Promise((_, rej) => setTimeout(() => rej(new Error("slow")), ms))]);
    if (r && r.ok) return r;
    const old = await cache.match(key(u));   /* ردّ الخادم بخطأ (404/5xx): الأفضل آخر نسخة سليمة محفوظة */
    return old || r;
  } catch (e) {
    const hit = await cache.match(key(u));
    if (hit) { net.catch(() => {}); return hit; }   /* تُكمل الشبكة تحديث النسخة المحفوظة في الخلفية */
    return net;
  }
}
self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin !== location.origin) return;
  if (u.pathname.endsWith("/sw.js")) return;
  if (r.mode === "navigate" && (u.pathname.endsWith("/") || u.pathname.endsWith("/index.html"))) e.respondWith(netFirst(new Request(u.origin + u.pathname.replace(/[^/]*$/, "") + "index.html", { cache: "no-store" }), 4000));
  else if (/\.(json|woff2|webmanifest|jpg|jpeg|png|ico|html)$/i.test(u.pathname)) e.respondWith(netFirst(r, /\.json$/i.test(u.pathname) ? 6000 : 8000));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(cs => {
    for (const c of cs) { if ("focus" in c) return c.focus(); }
    return self.clients.openWindow("./");
  }));
});
