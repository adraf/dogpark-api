<template>
  <div class="park-view">
    <div class="back-bar">
      <PvButton icon="pi pi-arrow-left" label="Back" size="small" text @click="$router.back()" />
    </div>

    <div v-if="loading" class="state-wrap">
      <PvProgressSpinner style="width:40px;height:40px" strokeWidth="4" />
    </div>

    <div v-else-if="!park" class="state-wrap">
      <i class="pi pi-exclamation-circle" style="font-size:44px;color:var(--forest-light)" />
      <p>Park not found</p>
    </div>

    <div v-else class="content">
      <!-- Hero -->
      <div class="hero">
        <div class="hero-pattern" />
        <div class="hero-body">
          <div class="hero-badges">
            <span v-if="park.is_fully_enclosed" class="badge">
              <i class="pi pi-lock" /> Fully enclosed
            </span>
            <span v-if="park.is_free" class="badge free">
              <i class="pi pi-check-circle" /> Free entry
            </span>
          </div>
          <h1 class="hero-name">{{ park.name }}</h1>
          <div class="hero-loc">
            <i class="pi pi-map-marker" />
            {{ park.address }}<span v-if="park.postcode"> · {{ park.postcode }}</span>
          </div>
        </div>
        <button
          class="fav-btn"
          :class="{ active: store.isFavourite(park.id) }"
          @click="store.toggleFavourite(park.id)"
        >
          <i :class="['pi', store.isFavourite(park.id) ? 'pi-heart-fill' : 'pi-heart']" />
        </button>
      </div>

      <!-- Body -->
      <div class="body">
        <div class="left-col">

          <!-- Description -->
          <section v-if="park.description" class="card">
            <p class="description">{{ park.description }}</p>
          </section>

          <!-- Stats -->
          <section class="card">
            <h2 class="section-title">At a glance</h2>
            <div class="stats-grid">
              <div v-if="park.size_acres" class="stat">
                <i class="pi pi-expand" />
                <div><div class="stat-val">{{ park.size_acres }} acres</div><div class="stat-lbl">Size</div></div>
              </div>
              <div v-if="park.price_per_hour || park.is_free" class="stat">
                <i class="pi pi-tag" />
                <div>
                  <div class="stat-val" :class="{ free: park.is_free }">
                    {{ park.is_free ? 'Free' : `£${park.price_per_hour}/hr` }}
                  </div>
                  <div class="stat-lbl">Price</div>
                </div>
              </div>
              <div v-if="park.fence_height_m" class="stat">
                <i class="pi pi-minus" />
                <div>
                  <div class="stat-val">{{ park.fence_height_m }}m <small>({{ (park.fence_height_m * 3.28).toFixed(1) }}ft)</small></div>
                  <div class="stat-lbl">Fence height</div>
                </div>
              </div>
              <div v-if="park.rating" class="stat">
                <i class="pi pi-star-fill" style="color:var(--gold)" />
                <div>
                  <div class="stat-val">{{ park.rating }} <small>({{ park.review_count }} reviews)</small></div>
                  <div class="stat-lbl">Rating</div>
                </div>
              </div>
              <div v-if="park.max_dogs" class="stat">
                <i class="pi pi-users" />
                <div><div class="stat-val">{{ park.max_dogs }}</div><div class="stat-lbl">Max dogs / session</div></div>
              </div>
              <div v-if="park.opening_hours" class="stat">
                <i class="pi pi-clock" />
                <div><div class="stat-val small">{{ park.opening_hours }}</div><div class="stat-lbl">Opening hours</div></div>
              </div>
            </div>
          </section>

          <!-- Features -->
          <section v-if="park.features?.length" class="card">
            <h2 class="section-title">Facilities &amp; features</h2>
            <div class="features-grid">
              <span v-for="f in park.features" :key="f" class="feature-chip">
                <i :class="['pi', featureIcon(f)]" />
                {{ featureLabel(f) }}
              </span>
            </div>
          </section>

          <!-- Contact -->
          <section class="card">
            <h2 class="section-title">Contact</h2>
            <div class="contact-list">
              <a v-if="park.phone"   :href="`tel:${park.phone}`"       class="contact-row"><i class="pi pi-phone" />   {{ park.phone }}</a>
              <a v-if="park.email"   :href="`mailto:${park.email}`"    class="contact-row"><i class="pi pi-envelope" /> {{ park.email }}</a>
              <a v-if="park.website" :href="park.website" target="_blank" rel="noopener" class="contact-row">
                <i class="pi pi-globe" /> {{ park.website.replace(/^https?:\/\//, '') }}
              </a>
              <p v-if="!park.phone && !park.email && !park.website" style="font-size:13px;color:var(--text-muted)">
                No contact info available
              </p>
            </div>
          </section>
        </div>

        <!-- Map column -->
        <div class="right-col">
          <section class="card map-card">
            <h2 class="section-title">Location</h2>
            <div ref="miniMapEl" class="mini-map" />
            <a
              v-if="park.latitude && park.longitude"
              :href="`https://maps.google.com/?q=${park.latitude},${park.longitude}`"
              target="_blank" rel="noopener"
              class="maps-link"
            >
              <i class="pi pi-map-marker" /> Open in Google Maps
            </a>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import L from 'leaflet'
import { useParksStore } from '../stores/parks'
import { useFeatures } from '../composables/useFeatures'

const route  = useRoute()
const store  = useParksStore()
const { icon: featureIcon, label: featureLabel } = useFeatures()

const park      = ref(null)
const loading   = ref(true)
const miniMapEl = ref(null)
let miniMap     = null

async function load() {
  loading.value = true
  park.value    = await store.fetchPark(route.params.id)
  loading.value = false
}

function initMap() {
  if (!park.value?.latitude || !park.value?.longitude || !miniMapEl.value) return
  if (miniMap) { miniMap.remove(); miniMap = null }

  miniMap = L.map(miniMapEl.value, { scrollWheelZoom: false })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(miniMap)

  const icon = L.divIcon({
    className: '',
    html: `<div style="width:28px;height:28px;background:#237a56;border:2.5px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 2px 8px rgba(0,0,0,0.25)"></div>`,
    iconSize: [28, 28], iconAnchor: [14, 28],
  })

  L.marker([park.value.latitude, park.value.longitude], { icon })
    .addTo(miniMap)
    .bindPopup(park.value.name)
    .openPopup()

  miniMap.setView([park.value.latitude, park.value.longitude], 13)
}

onMounted(async () => { await load(); setTimeout(initMap, 150) })
onUnmounted(() => { if (miniMap) { miniMap.remove(); miniMap = null } })
watch(() => route.params.id, async () => { await load(); setTimeout(initMap, 150) })
</script>

<style scoped>
.park-view { display: flex; flex-direction: column; flex: 1; overflow-y: auto; background: var(--cream); }

.back-bar {
  padding: 8px 16px; background: white;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}

.state-wrap {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; flex: 1; gap: 12px;
  color: var(--text-muted); padding: 60px; font-size: 15px;
}

.hero {
  height: 200px;
  background: linear-gradient(135deg, #1a4a35 0%, #237a56 55%, #3aaa75 100%);
  position: relative; display: flex; align-items: flex-end; flex-shrink: 0;
}
.hero-pattern {
  position: absolute; inset: 0; opacity: 0.08;
  background-image:
    radial-gradient(circle at 15% 50%, white 1px, transparent 1px),
    radial-gradient(circle at 85% 20%, white 1px, transparent 1px),
    radial-gradient(circle at 50% 80%, white 1px, transparent 1px);
  background-size: 50px 50px;
}
.hero-body { padding: 20px 24px; position: relative; z-index: 1; }
.hero-badges { display: flex; gap: 6px; margin-bottom: 8px; }
.badge {
  background: rgba(255,255,255,0.92); color: var(--forest);
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 10px; display: flex; align-items: center; gap: 4px;
}
.badge.free { background: #d9f4e8; color: #0e5c33; }
.hero-name { font-size: 26px; font-weight: 700; color: white; font-family: Georgia, serif; line-height: 1.2; margin-bottom: 6px; }
.hero-loc { color: rgba(255,255,255,0.8); font-size: 13px; display: flex; align-items: center; gap: 6px; }

.fav-btn {
  position: absolute; top: 16px; right: 16px;
  background: rgba(255,255,255,0.92); border: none; border-radius: 50%;
  width: 40px; height: 40px; display: flex; align-items: center;
  justify-content: center; cursor: pointer; z-index: 2; transition: all 0.15s;
}
.fav-btn .pi { font-size: 18px; color: var(--text-muted); transition: color 0.15s; }
.fav-btn.active .pi { color: #e53935; }
.fav-btn:hover { background: white; transform: scale(1.08); }

.body { display: flex; gap: 20px; padding: 24px; align-items: flex-start; }
.left-col { flex: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.right-col { width: 320px; flex-shrink: 0; }

.card { background: white; border-radius: var(--radius); border: 1px solid var(--border); padding: 18px 20px; }
.section-title {
  font-size: 11px; font-weight: 700; letter-spacing: 0.6px;
  text-transform: uppercase; color: var(--text-muted); margin-bottom: 14px;
}
.description { font-size: 14px; color: var(--text-muted); line-height: 1.7; }

.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.stat {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; background: var(--parchment); border-radius: 8px;
}
.stat > .pi { font-size: 16px; color: var(--forest-mid); margin-top: 3px; flex-shrink: 0; }
.stat-val { font-size: 15px; font-weight: 600; color: var(--forest); line-height: 1.3; }
.stat-val.free { color: #0e5c33; }
.stat-val.small, .stat-val small { font-size: 13px; font-weight: 400; color: var(--text-muted); }
.stat-lbl { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.features-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.feature-chip {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; padding: 5px 10px; border-radius: 10px;
  background: var(--tag-bg); color: var(--tag-text);
}
.feature-chip .pi { font-size: 12px; }

.contact-list { display: flex; flex-direction: column; gap: 4px; }
.contact-row {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: var(--blue); text-decoration: none;
  padding: 8px 10px; border-radius: 8px; transition: background 0.12s;
}
.contact-row:hover { background: var(--parchment); }
.contact-row .pi { color: var(--forest-mid); font-size: 14px; width: 16px; text-align: center; }

.map-card { padding-bottom: 0; overflow: hidden; }
.mini-map { height: 260px; margin: 0 -20px; }
.maps-link {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px; font-size: 13px; font-weight: 500;
  color: var(--forest-mid); text-decoration: none; transition: background 0.12s;
}
.maps-link:hover { background: var(--parchment); }

@media (max-width: 900px) {
  .body { flex-direction: column; }
  .right-col { width: 100%; }
}
</style>
