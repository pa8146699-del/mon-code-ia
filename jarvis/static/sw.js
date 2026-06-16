// Service worker minimal — rend l'app installable
self.addEventListener('fetch', e => e.respondWith(fetch(e.request)));
