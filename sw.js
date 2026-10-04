// عامل خدمة خفيف: لا يخزّن شيئًا (حتى لا تظهر نسخة قديمة من الموقع)، وظيفته تمكين التثبيت والإشعارات فقط
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(clients.matchAll({type: "window", includeUncontrolled: true}).then(l => l.length ? l[0].focus() : clients.openWindow("./")));
});
