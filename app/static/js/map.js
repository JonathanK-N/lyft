// Minimal Leaflet wrapper used across pages (with robust geolocation)
window.AppMap = (function () {
  let map;
  const state = {
    markers: new Map(),
    routeLayer: null,
    fallbackCenter: [45.3715014, -71.8590381], // ICC Sherbrooke – 219 Rue Queen
  };

  function setFallbackCenter(lat, lon){
    state.fallbackCenter = [lat, lon];
  }

  function create(elId, { center, zoom = 13 } = {}) {
    const el = document.getElementById(elId);
    if (!el) throw new Error(`Map element not found: ${elId}`);
    const initial = center && Array.isArray(center) ? center : state.fallbackCenter;
    map = L.map(elId).setView(initial, zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    return map;
  }

  async function locate() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) return reject(new Error('Geolocation indisponible'));
      const optsHi = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
      const optsLo = { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 };
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
        (err) => {
          navigator.geolocation.getCurrentPosition(
            (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
            () => reject(err),
            optsLo
          );
        },
        optsHi
      );
    });
  }

  async function locateAndCenter() {
    try {
      const ll = await locate();
      try {
        const c = map ? map.getCenter() : state.fallbackCenter;
        const d = distanceKm(c, ll);
        if (d > 5000) throw new Error('Outlier location');
      } catch(_) {}
      if (map) map.setView(ll, Math.max(map.getZoom(), 14));
      addOrMoveMarker('me', ll, { label: 'Moi' });
      return ll;
    } catch (e) {
      if (map) map.setView(state.fallbackCenter, Math.max(map.getZoom(), 14));
      return state.fallbackCenter;
    }
  }

  function addMarker(latlng, { label } = {}) {
    const m = L.marker(latlng).addTo(map);
    if (label) m.bindPopup(label).openPopup();
    return m;
  }

  function addOrMoveMarker(key, latlng, { label } = {}) {
    const existing = state.markers.get(key);
    if (existing) {
      existing.setLatLng(latlng);
      if (label) existing.bindPopup(label);
      return existing;
    }
    const m = addMarker(latlng, { label });
    state.markers.set(key, m);
    return m;
  }

  function clearRoute() {
    if (state.routeLayer) {
      map.removeLayer(state.routeLayer);
      state.routeLayer = null;
    }
  }

  async function route(from, to) {
    try {
      const url = `https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;
      const res = await fetch(url);
      const data = await res.json();
      const coords = data.routes?.[0]?.geometry?.coordinates;
      if (!coords) return;
      clearRoute();
      const latlngs = coords.map(([lng, lat]) => [lat, lng]);
      state.routeLayer = L.polyline(latlngs, { color: '#3b5bdb', weight: 5, opacity: .85 }).addTo(map);
      map.fitBounds(state.routeLayer.getBounds(), { padding: [30, 30] });
    } catch (e) {
      console.warn('Routing unavailable', e);
    }
  }

  function distanceKm(a, b){
    const toRad = (x)=>x*Math.PI/180;
    const [lat1, lon1] = a, [lat2, lon2] = b;
    const R=6371, dLat=toRad(lat2-lat1), dLon=toRad(lon2-lon1);
    const s = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
    return 2*R*Math.asin(Math.sqrt(s));
  }

  return { create, locate, locateAndCenter, addMarker, addOrMoveMarker, clearRoute, route, setFallbackCenter };
})();

