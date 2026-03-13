<template>
  <aside class="sidebar">
    <!-- Quick filters -->
    <section class="section">
      <h3 class="section-label">Quick Filters</h3>
      <button
        v-for="f in quickFilters"
        :key="f.key"
        class="filter-btn"
        :class="{ active: store.filters.quick === f.key }"
        @click="store.setFilter('quick', f.key)"
      >
        <span class="dot" :style="{ background: f.color }" />
        {{ f.label }}
        <span class="count">{{ f.count }}</span>
      </button>
    </section>

    <!-- Price slider -->
    <section class="section">
      <h3 class="section-label">Max price / hour</h3>
      <div class="slider-wrap">
        <div class="slider-labels">
          <span>Free</span>
          <span class="slider-val">{{ priceLabel }}</span>
        </div>
        <input
          type="range" min="0" max="30" step="1"
          :value="store.filters.maxPrice"
          @input="e => { store.setFilter('maxPrice', +e.target.value); updateTrack(e.target) }"
          ref="priceSlider"
        />
      </div>
    </section>

    <!-- Size slider -->
    <section class="section">
      <h3 class="section-label">Minimum size (acres)</h3>
      <div class="slider-wrap">
        <div class="slider-labels">
          <span>Any</span>
          <span class="slider-val">{{ sizeLabel }}</span>
        </div>
        <input
          type="range" min="0" max="6" step="0.5"
          :value="store.filters.minSize"
          @input="e => { store.setFilter('minSize', +e.target.value); updateTrack(e.target) }"
          ref="sizeSlider"
        />
      </div>
    </section>

    <!-- County list -->
    <section class="section">
      <h3 class="section-label">County</h3>
      <div class="county-list">
        <div
          v-for="c in store.counties"
          :key="c.county"
          class="county-item"
          :class="{ active: store.filters.county === c.county }"
          @click="toggleCounty(c.county)"
        >
          {{ c.county }}
          <span class="county-count">{{ c.count }}</span>
        </div>
      </div>
    </section>
  </aside>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useParksStore } from '../stores/parks'

const store = useParksStore()

const priceSlider = ref(null)
const sizeSlider  = ref(null)

const quickFilters = computed(() => {
  const all  = store.allParks
  return [
    { key: 'all',      label: 'All parks',        color: '#3aaa75', count: all.length },
    { key: 'enclosed', label: 'Fully enclosed',   color: '#1a6fbb', count: all.filter(p => p.is_fully_enclosed).length },
    { key: 'free',     label: 'Free entry',       color: '#0e8a82', count: all.filter(p => p.is_free).length },
    { key: 'agility',  label: 'Agility equipment',color: '#3b8fd4', count: all.filter(p => (p.features||[]).includes('agility_equipment')).length },
    { key: 'lighting', label: 'Lighting',         color: '#c9920a', count: all.filter(p => (p.features||[]).includes('lighting')).length },
  ]
})

const priceLabel = computed(() => store.filters.maxPrice >= 30 ? 'All' : `£${store.filters.maxPrice}/hr`)
const sizeLabel  = computed(() => store.filters.minSize  === 0  ? 'Any' : `${store.filters.minSize}+ acres`)

function toggleCounty(c) {
  store.setFilter('county', store.filters.county === c ? null : c)
}

function updateTrack(el) {
  const pct = ((el.value - el.min) / (el.max - el.min) * 100).toFixed(1) + '%'
  el.style.setProperty('--pct', pct)
}

onMounted(() => {
  if (priceSlider.value) updateTrack(priceSlider.value)
  if (sizeSlider.value)  updateTrack(sizeSlider.value)
})
</script>

<style scoped>
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: white;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 16px 12px;
}

.section { margin-bottom: 22px; }

.section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: all 0.12s;
  margin-bottom: 2px;
}
.filter-btn:hover { background: var(--parchment); color: var(--text); }
.filter-btn.active { background: #dbeeff; border-color: #5aaae8; color: var(--text); font-weight: 500; }

.dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

.count {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-muted);
  background: var(--parchment);
  padding: 1px 6px;
  border-radius: 8px;
}

.slider-wrap { padding: 0 4px; }
.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.slider-val { color: var(--forest); font-weight: 600; }

input[type=range] {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 5px;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  background: linear-gradient(
    to right,
    var(--forest-mid) 0%,
    var(--forest-mid) var(--pct, 0%),
    #c5d8cb var(--pct, 0%),
    #c5d8cb 100%
  );
}
input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--forest-mid);
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(35,122,86,0.4);
  cursor: pointer;
}
input[type=range]::-moz-range-thumb {
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--forest-mid);
  border: 2px solid white;
  cursor: pointer;
}

.county-list { max-height: 200px; overflow-y: auto; }
.county-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 6px;
  color: var(--text-muted);
  transition: background 0.1s;
  margin-bottom: 1px;
}
.county-item:hover { background: var(--parchment); color: var(--text); }
.county-item.active { background: #dbeeff; color: var(--text); font-weight: 500; }
.county-count { color: #9aa6b0; font-size: 11px; }
</style>
