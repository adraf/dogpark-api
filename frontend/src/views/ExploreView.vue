<template>
  <div class="explore">
    <div class="toolbar">
      <span class="result-count">
        <strong>{{ store.filteredParks.length }}</strong> parks found
      </span>
      <PvSelect
        v-model="sort" :options="sortOptions"
        option-label="label" option-value="value"
        class="sort-select" @change="store.setFilter('sort', sort)"
      />
      <Transition name="fade">
        <button v-if="hasActiveFilters" class="clear-btn" @click="store.resetFilters()">
          <AppIcon name="clear-filters" :size="14" />
          Clear filters
        </button>
      </Transition>

      <div class="view-toggle">
        <button class="view-btn" :class="{ active: view === 'list' }" @click="view = 'list'">
          <AppIcon name="list" :size="15" /> List
        </button>
        <button class="view-btn" :class="{ active: view === 'map' }" @click="view = 'map'">
          <AppIcon name="map" :size="15" /> Map
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="loading">
      <PvProgressSpinner style="width:36px;height:36px" strokeWidth="4" />
      <span>Loading parks…</span>
    </div>

    <div v-else-if="store.error" class="error-banner">
      <AppIcon name="error" :size="18" />
      Cannot connect to the API. Make sure uvicorn is running on port 8000.
      <PvButton label="Retry" size="small" @click="store.fetchAll()" style="margin-left:8px">
        <template #icon><AppIcon name="reboot" :size="14" /></template>
      </PvButton>
    </div>

    <div v-else-if="view === 'list'" class="list-content">
      <div v-if="store.filteredParks.length === 0" class="empty">
        <AppIcon name="search" :size="44" />
        <p>No parks match your filters</p>
        <PvButton label="Clear filters" size="small" outlined @click="store.resetFilters()">
          <template #icon><AppIcon name="clear-filters" :size="14" /></template>
        </PvButton>
      </div>
      <template v-else>
        <div class="parks-grid">
          <ParkCard v-for="park in paginated" :key="park.id" :park="park" />
        </div>
        <PvPaginator
          v-if="store.filteredParks.length > perPage"
          :rows="perPage" :totalRecords="store.filteredParks.length"
          :first="(page - 1) * perPage"
          @page="e => page = e.page + 1"
          class="paginator"
        />
      </template>
    </div>

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

const hasActiveFilters = computed(() => {
  const f = store.filters
  return f.search || f.county || f.enclosed || f.free ||
         (f.features && f.features.length > 0) ||
         f.maxPrice < 30 || f.minSize > 0
})

const paginated = computed(() => {
  const start = (page.value - 1) * perPage
  return store.filteredParks.slice(start, start + perPage)
})
</script>

<style scoped>
.explore { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
.toolbar {
  display: flex; align-items: center; gap: 12px; padding: 10px 20px;
  background: white; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.result-count { font-size: 13px; color: var(--text-muted); }
.result-count strong { color: var(--text); }
.sort-select { font-size: 13px; min-width: 150px; height: 34px; }
:deep(.p-select) { height: 34px; font-size: 13px; }
:deep(.p-select-label) { font-size: 13px; padding-top: 0; padding-bottom: 0; display: flex; align-items: center; }
.clear-btn {
  display: flex; align-items: center; gap: 6px;
  height: 34px; padding: 0 12px; border-radius: 7px;
  border: 1.5px solid #f0b429;
  background: #fff9e6; color: #7a5500;
  font-size: 13px; font-weight: 500; cursor: pointer;
  transition: all 0.15s; white-space: nowrap;
}
.clear-btn:hover { background: #ffefc0; border-color: #c9920a; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.92); }

.view-toggle { display: flex; gap: 6px; margin-left: auto; }
.view-btn {
  display: flex; align-items: center; gap: 6px; padding: 0 16px;
  height: 34px; border-radius: 7px;
  border: 1.5px solid #c8d4cc; background: white;
  font-size: 13px; font-weight: 500; color: var(--text-muted); cursor: pointer; transition: all 0.15s;
}
.view-btn:hover:not(.active) { border-color: var(--forest-mid); color: var(--text); }
.view-btn.active { background: var(--forest-mid); border-color: var(--forest-mid); color: white; font-weight: 600; }
.view-btn.active :deep(.app-icon) { filter: brightness(0) invert(1); }
.loading { display: flex; align-items: center; justify-content: center; gap: 12px; flex: 1; font-size: 14px; color: var(--text-muted); }
.error-banner {
  margin: 16px; padding: 14px 16px; background: #fff3cd; border: 1px solid #ffc107;
  border-radius: 10px; font-size: 13px; color: #856404; display: flex; align-items: center; gap: 8px;
}
.list-content { flex: 1; overflow-y: auto; padding: 20px; }
.empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; gap: 14px; color: var(--text-muted); text-align: center; }
.empty p { font-size: 15px; color: var(--text); }
.parks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px; }
.paginator { margin-top: 20px; }
.map-view { flex: 1; }
</style>
