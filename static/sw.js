const CACHE_NAME = 'entokmart-v1';
const STATIC_ASSETS = [
  '/',
  '/login',
  '/register',
  '/produk',
  '/manifest.json',
  '/static/css/bootstrap.min.css',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

const API_CACHE = 'entokmart-api-v1';

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME && key !== API_CACHE)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch event
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // API requests - network first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(API_CACHE).then((cache) => {
            cache.put(event.request, clone);
          });
          return response;
        })
        .catch(() => {
          return caches.match(event.request);
        })
    );
    return;
  }
  
  // Static assets - cache first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).then((fetchResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      })
    );
    return;
  }
  
  // Navigation requests - network first
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/offline.html').catch(() => {
            return new Response('Offline', { status: 503 });
          });
        })
    );
    return;
  }
  
  // Default - network first
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

// Push notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'EntokMart';
  const options = {
    body: data.body || 'Ada notifikasi baru',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/'
    },
    actions: [
      { action: 'open', title: 'Buka' },
      { action: 'close', title: 'Tutup' }
    ]
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    const url = event.notification.data.url || '/';
    event.waitUntil(clients.openWindow(url));
  }
});

// Background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-cart') {
    event.waitUntil(syncCart());
  }
});

async function syncCart() {
  // Sync cart when back online
  console.log('[SW] Syncing cart...');
}

module.exports = self;