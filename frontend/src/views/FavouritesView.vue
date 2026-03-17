<template>
  <div class="favourites">
    <div class="toolbar">
      <span class="result-count">
        <strong>{{ store.favouriteParks.length }}</strong> saved park{{ store.favouriteParks.length !== 1 ? 's' : '' }}
      </span>
      <div class="view-toggle">
        <button class="view-btn" :class="{ active: view === 'list' }" @click="view = 'list'">
          <AppIcon name="list" :size="15" /> <span class="btn-text">List</span>
        </button>
        <button class="view-btn" :class="{ active: view === 'map' }" @click="view = 'map'">
          <AppIcon name="map" :size="15" /> <span class="btn-text">Map</span>
        </button>
      </div>
    </div>

    <div v-if="view === 'list'" class="content">
      <div v-if="store.favouriteParks.length === 0" class="empty">
        <AppIcon name="heart" :size="48" />
        <p>No favourites yet</p>
        <span>Tap the heart on any park to save it here</span>
        <RouterLink to="/">
          <PvButton label="Explore parks">
            <template #icon><AppIcon name="compass" :size="15" /></template>
          </PvButton>
        </RouterLink>
      </div>
      <div v-else class="parks-grid">
        <ParkCard v-for="park in store.favouriteParks" :key="park.id" :park="park" />
      </div>
    </div>

    <ParkMap v-else :parks="store.favouriteParks" class="map-view" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ParkCard from '../components/ParkCard.vue'
import ParkMap from '../components/ParkMap.vue'
import { useParksStore } from '../stores/parks'

const store = useParksStore()
const view  = ref('list')
</script>

<style scoped>
.favourites { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

.toolbar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 20px; background: white;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.result-count { font-size: 13px; color: var(--text-muted); }
.result-count strong { color: var(--text); }

.view-toggle { display: flex; gap: 6px; margin-left: auto; }
.view-btn {
  display: flex; align-items: center; gap: 6px; padding: 0 16px;
  height: 34px; border-radius: 7px;
  border: 1.5px solid #c8d4cc; background: white;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  cursor: pointer; transition: all 0.15s;
}
.view-btn:hover:not(.active) { border-color: var(--forest-mid); color: var(--text); }
.view-btn.active { background: var(--forest-mid); border-color: var(--forest-mid); color: white; font-weight: 600; }
.view-btn.active :deep(.app-icon) { filter: brightness(0) invert(1); }

.content { flex: 1; overflow-y: auto; padding: 20px; scrollbar-width: none; }
.content::-webkit-scrollbar { display: none; }

.empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; padding: 60px 20px;
  text-align: center; color: var(--text-muted);
}
.empty p { font-size: 16px; font-weight: 600; color: var(--text); }

.parks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 16px;
}

.map-view { flex: 1; }

@media (max-width: 767px) {
  .toolbar { padding: 8px 12px; }
  .result-count { display: none; }
  .parks-grid { grid-template-columns: 1fr; }
  .view-btn { padding: 0 12px; }
}
</style>
