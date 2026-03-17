<template>
  <div class="favourites">
    <div class="toolbar">
      <span class="result-count">
        <strong>{{ store.favouriteParks.length }}</strong> saved park{{ store.favouriteParks.length !== 1 ? 's' : '' }}
      </span>
    </div>

    <div class="content">
      <div v-if="store.favouriteParks.length === 0" class="empty">
        <i class="pi pi-heart" />
        <p>No favourites yet</p>
        <span>Tap the heart on any park to save it here</span>
        <RouterLink to="/">
          <PvButton label="Explore parks" icon="pi pi-compass" />
        </RouterLink>
      </div>
      <div v-else class="parks-grid">
        <ParkCard v-for="park in store.favouriteParks" :key="park.id" :park="park" />
      </div>
    </div>
  </div>
</template>

<script setup>
import ParkCard from '../components/ParkCard.vue'
import { useParksStore } from '../stores/parks'
const store = useParksStore()
</script>

<style scoped>
.favourites { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
.toolbar {
  padding: 10px 20px; background: white;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.result-count { font-size: 13px; color: var(--text-muted); }
.result-count strong { color: var(--text); }
.content { flex: 1; overflow-y: auto; padding: 20px; }
.empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; padding: 60px 20px;
  text-align: center; color: var(--text-muted);
}
.empty .pi { font-size: 48px; color: #e53935; }
.empty p { font-size: 16px; font-weight: 600; color: var(--text); }
.parks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 16px;
}
</style>
