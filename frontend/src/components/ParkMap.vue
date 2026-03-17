<template>
  <div class="map-outer">
    <div ref="mapEl" class="map-container" />
    <div class="map-legend">
      <div class="legend-item">
        <span class="legend-dot standard" />
        Park
      </div>
      <div class="legend-item">
        <span class="legend-dot favourite" />
        Favourited
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import { useRouter } from 'vue-router'
import { useParksStore } from '../stores/parks'

const props = defineProps({
  parks: { type: Array, required: true }
})

const mapEl  = ref(null)
const router = useRouter()
const store  = useParksStore()

let map     = null
let markers = []

// Fix Leaflet default icon path issue with Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function parkIcon(park) {
  const isFav = store.isFavourite(park.id)
  const color = isFav ? '#c9920a' : '#237a56'
  return L.divIcon({
    className: '',
    html: `<div style="
      width:28px; height:28px;
      background:${color};
      border:2.5px solid white;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
    "></div>`,
    iconSize:   [28, 28],
    iconAnchor: [14, 28],
    popupAnchor:[0, -30],
  })
}

function buildMarkers() {
  markers.forEach(m => m.remove())
  markers = []

  props.parks.forEach(park => {
    if (!park.latitude || !park.longitude) return

    const marker = L.marker([park.latitude, park.longitude], { icon: parkIcon(park) })

    const popup = L.popup({ maxWidth: 260, className: 'park-popup' }).setContent(`
      <div style="font-family:'Segoe UI',sans-serif;">
        <div style="font-weight:600;font-size:14px;margin-bottom:4px;color:#1a1a1a">${park.name}</div>
        <div style="font-size:12px;color:#5a6670;margin-bottom:8px">
          📍 ${park.town}, ${park.county}
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          ${park.is_free
            ? '<span style="font-size:11px;padding:2px 8px;border-radius:8px;background:#d9f4e8;color:#0e5c33;font-weight:500">Free</span>'
            : park.price_per_hour
              ? `<span style="font-size:11px;padding:2px 8px;border-radius:8px;background:#fff3d6;color:#7a5500;font-weight:500">£${park.price_per_hour}/hr</span>`
              : ''}
          ${park.size_acres
            ? `<span style="font-size:11px;padding:2px 8px;border-radius:8px;background:#dbeeff;color:#1a4f85;font-weight:500">${park.size_acres} acres</span>`
            : ''}
        </div>
        <button
          onclick="window._safepawsNav && window._safepawsNav('${park.id}')"
          style="
            width:100%;padding:7px 0;
            background:#237a56;color:white;
            border:none;border-radius:8px;
            font-size:13px;font-weight:500;
            cursor:pointer;
          "
        >View details →</button>
      </div>
    `)

    marker.bindPopup(popup)
    marker.addTo(map)
    markers.push(marker)
  })

  // Expose nav function for popup button
  window._safepawsNav = (id) => router.push(`/park/${id}`)
}

onMounted(() => {
  map = L.map(mapEl.value, {
    center: [54.5, -3.0],
    zoom:   6,
    zoomControl: true,
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map)

  buildMarkers()

  if (props.parks.length > 0) {
    const valid = props.parks.filter(p => p.latitude && p.longitude)
    if (valid.length) {
      const bounds = L.latLngBounds(valid.map(p => [p.latitude, p.longitude]))
      map.fitBounds(bounds, { padding: [40, 40] })
    }
  }
})

onUnmounted(() => {
  if (map) { map.remove(); map = null }
  delete window._safepawsNav
})

watch(() => props.parks, () => buildMarkers(), { deep: true })
watch(() => store.favourites.size, () => buildMarkers())
</script>

<style scoped>
.map-outer {
  flex: 1;
  overflow: hidden;
  position: relative;
}
.map-container {
  width: 100%;
  height: 100%;
}
.map-legend {
  position: absolute;
  bottom: 24px;
  right: 10px;
  z-index: 1000;
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.legend-dot {
  width: 14px; height: 14px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  flex-shrink: 0;
}
.legend-dot.standard  { background: #237a56; }
.legend-dot.favourite { background: #c9920a; }
</style>
