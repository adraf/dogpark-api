<template>
  <div class="explore">
    <!-- Toolbar -->
    <div class="toolbar">
      <span class="result-count">
        <strong>{{ store.filteredParks.length }}</strong> parks found
      </span>

      <PvSelect
        v-model="sort"
        :options="sortOptions"
        option-label="label"
        option-value="value"
        class="sort-select"
        @change="store.setFilter('sort', sort)"
      />

      <div class="view-toggle">
        <button class="view-btn" :class="{ active: view === 'list' }" @click="view = 'list'">
          <i class="pi pi-list" /> List
        </button>
        <button class="view-btn" :class="{ active: view === 'map' }" @click="view = 'map'">
          <i class="pi pi-map" /> Map
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading">
      <PvProgressSpinner style="width:36px;height:36px" strokeWidth="4" />
      <span>Loading parks…</span>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="error-banner">
      <i class="pi pi-exclamation-triangle" />
      Cannot connect to the API. Make sure uvicorn is running on port 8000.
      <PvButton label="Retry" icon="pi pi-refresh" size="small" @click="store.fetchAll()" style="margin-left:8px" />
    </div>

    <!-- List view -->
    <div v-else-if="view === 'list'" class="list-content">
      <div v-if="store.filteredParks.length === 0" class="empty">
        <i class="pi pi-search-minus" />
        <p>No parks match your filters</p>
        <PvButton label="Clear filters" icon="pi pi-filter-slash" size="small" outlined @click="store.resetFilters()" />
      </div>
      <template v-else>
        <div class="parks-grid">
          <ParkCard v-for="park in paginated" :key="park.id" :park="park" />
        </div>
        <PvPaginator
          v-if="store.filteredParks.length > perPage"
          :rows="perPage"
          :totalRecords="store.filteredParks.length"
          :first="(page - 1) * perPage"
          @page="e => page = e.page + 1"
          class="paginator"
        />
      </template>
    </div>

    <!-- Map view -->
    <ParkMap v-else :parks="store.filteredParks" class="map-view" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ParkCard from '../components/ParkCard.vue'
import ParkMap from '../components/ParkMap.vue'
import { useParksStore } from '../stores/parks'

const store   = useParksStore()
const view    = ref('list')
const sort    = ref('rating')
const page    = ref(1)
const perPage = 21

const sortOptions = [
  { label: 'Top rated',     value: 'rating' },
  { label: 'Lowest price',  value: 'price'  },
  { label: 'Largest first', value: 'size'   },
  { label: 'A–Z',           value: 'name'   },
]

const paginated = computed(() => {
  const start = (page.value - 1) * perPage
  return store.filteredParks.slice(start, start + perPage)
})
</script>

<style scoped>
.explore { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

.toolbar {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 20px;
  background: white;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.result-count { font-size: 13px; color: var(--text-muted); }
.result-count strong { color: var(--text); }
.sort-select { font-size: 13px; min-width: 150px; }

.view-toggle { display: flex; gap: 6px; margin-left: auto; }
.view-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: 7px;
  border: 1.5px solid #c8d4cc; background: white;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  cursor: pointer; transition: all 0.15s;
}
.view-btn .pi { font-size: 13px; }
.view-btn:hover:not(.active) { border-color: var(--forest-mid); color: var(--text); }
.view-btn.active { background: var(--forest-mid); border-color: var(--forest-mid); color: white; font-weight: 600; }

.loading {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; flex: 1;
  font-size: 14px; color: var(--text-muted);
}

.error-banner {
  margin: 16px; padding: 14px 16px;
  background: #fff3cd; border: 1px solid #ffc107;
  border-radius: 10px; font-size: 13px; color: #856404;
  display: flex; align-items: center; gap: 8px;
}

.list-content { flex: 1; overflow-y: auto; padding: 20px; }

.empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 60px 20px; gap: 14px;
  color: var(--text-muted); text-align: center;
}
.empty .pi { font-size: 44px; color: var(--forest-light); }
.empty p { font-size: 15px; color: var(--text); }

.parks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 16px;
}
.paginator { margin-top: 20px; }
.map-view { flex: 1; }
</style>
