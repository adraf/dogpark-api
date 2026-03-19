<template>
  <aside class="sidebar">

    <!-- Mobile header: search + close -->
    <div class="mobile-header">
      <div class="mobile-search">
        <AppIcon name="search" :size="15" class="msearch-icon" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Search parks..."
          @input="store.setFilter('search', searchTerm)"
        />
      </div>
      <button class="close-btn" @click="$emit('close')">
        <AppIcon name="close" :size="18" />
      </button>
    </div>

    <!-- Feature Filters (multi-select, derived from data) -->
    <section class="section">
      <h3 class="section-label">Features</h3>

      <div class="feature-filter-list" :class="{ expanded: featuresExpanded }">
        <label
          v-for="f in allFeatureFilters" :key="f.key"
          class="feature-check"
          :class="{ active: store.filters.features?.includes(f.key) }"
        >
          <input
            type="checkbox"
            :value="f.key"
            :checked="store.filters.features?.includes(f.key)"
            @change="toggleFeature(f.key)"
          />
          <FeatureIcon :feature-key="f.key" :size="15" />
          <span class="fc-label">{{ f.label }}</span>
          <span class="count">{{ f.count }}</span>
        </label>
      </div>

      <button v-if="allFeatureFilters.length > TOP_N" class="show-more-btn" @click="featuresExpanded = !featuresExpanded">
        <AppIcon :name="featuresExpanded ? 'collapse-arrow' : 'expand-arrow'" :size="14" />
        <span>{{ featuresExpanded ? 'Show less' : `Show ${allFeatureFilters.length - TOP_N} more` }}</span>
      </button>
    </section>

    <!-- Enclosed / Free toggles -->
    <section class="section">
      <h3 class="section-label">Type</h3>
      <label class="feature-check" :class="{ active: store.filters.enclosed }">
        <input type="checkbox" :checked="store.filters.enclosed" @change="store.setFilter('enclosed', !store.filters.enclosed)" />
        <AppIcon name="lock" :size="15" />
        <span class="fc-label">Fully enclosed</span>
        <span class="count">{{ enclosedCount }}</span>
      </label>
      <label class="feature-check" :class="{ active: store.filters.free }">
        <input type="checkbox" :checked="store.filters.free" @change="store.setFilter('free', !store.filters.free)" />
        <AppIcon name="check-mark" :size="15" />
        <span class="fc-label">Free entry</span>
        <span class="count">{{ freeCount }}</span>
      </label>
    </section>

    <!-- Price slider -->
    <section class="section">
      <h3 class="section-label">Max price / hour</h3>
      <div class="slider-wrap">
        <div class="slider-labels">
          <span>Free</span>
          <span class="slider-val">{{ priceLabel }}</span>
        </div>
        <input type="range" min="0" max="30" step="1"
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
        <input type="range" min="0" max="6" step="0.5"
          :value="store.filters.minSize"
          @input="e => { store.setFilter('minSize', +e.target.value); updateTrack(e.target) }"
          ref="sizeSlider"
        />
      </div>
    </section>

    <!-- County (unified scrollable list) -->
    <section class="section">
      <h3 class="section-label">County</h3>

      <div class="county-search">
        <AppIcon name="search" :size="13" class="csearch-icon" />
        <input v-model="countySearch" type="text" placeholder="Search counties..." />
      </div>

      <div class="county-list" :class="{ expanded: countyExpanded || countySearch }">
        <div
          v-for="c in filteredCounties" :key="c.county"
          class="county-item" :class="{ active: store.filters.county === c.county }"
          @click="toggleCounty(c.county)"
        >
          {{ c.county }}
          <span class="county-count">{{ c.count }}</span>
        </div>
        <div v-if="filteredCounties.length === 0" class="county-empty">No counties found</div>
      </div>

      <button v-if="!countySearch && sortedCounties.length > TOP_N" class="show-more-btn" @click="countyExpanded = !countyExpanded">
        <AppIcon :name="countyExpanded ? 'collapse-arrow' : 'expand-arrow'" :size="14" />
        <span>{{ countyExpanded ? 'Show less' : `Show ${sortedCounties.length - TOP_N} more` }}</span>
      </button>
    </section>


    <!-- Footer credit -->
    <div class="sidebar-footer">
      <p>Made by <a href="https://www.adamraffertywebdesign.com/" target="_blank" rel="noopener">Adam Rafferty Web Design</a></p>
      <p>Icons by <a href="https://icons8.com/" target="_blank" rel="noopener">icons8</a></p>
    </div>

  </aside>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useParksStore } from '../stores/parks'
import { FEATURE_LABELS } from '../composables/useFeatures'

defineEmits(['close'])

const store = useParksStore()

const searchTerm = ref(store.filters.search)
watch(() => store.filters.search, v => { searchTerm.value = v })

const priceSlider      = ref(null)
const sizeSlider       = ref(null)
const featuresExpanded = ref(false)
const countyExpanded   = ref(false)
const TOP_N = 5

// Derive all features present in the data, sorted by count
const allFeatureFilters = computed(() => {
  const counts = {}
  store.allParks.forEach(p => (p.features || []).forEach(f => {
    counts[f] = (counts[f] || 0) + 1
  }))
  return Object.entries(counts)
    .map(([key, count]) => ({ key, count, label: FEATURE_LABELS[key] || key }))
    .sort((a, b) => b.count - a.count)
})

const enclosedCount = computed(() => store.allParks.filter(p => p.is_fully_enclosed).length)
const freeCount     = computed(() => store.allParks.filter(p => p.is_free).length)
const countySearch   = ref('')
const sortedCounties  = computed(() => [...store.counties].sort((a, b) => a.county.localeCompare(b.county)))
const filteredCounties = computed(() => {
  const all = countySearch.value
    ? sortedCounties.value.filter(c => c.county.toLowerCase().includes(countySearch.value.toLowerCase()))
    : sortedCounties.value
  return countyExpanded.value || countySearch.value ? all : all.slice(0, TOP_N)
})

const priceLabel = computed(() => store.filters.maxPrice >= 30 ? 'All' : `£${store.filters.maxPrice}/hr`)
const sizeLabel  = computed(() => store.filters.minSize  === 0  ? 'Any' : `${store.filters.minSize}+ acres`)

function toggleFeature(key) {
  const current = store.filters.features || []
  const updated = current.includes(key)
    ? current.filter(f => f !== key)
    : [...current, key]
  store.setFilter('features', updated)
}

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
  width: 240px; flex-shrink: 0; background: white;
  border-right: 1px solid var(--border);
  overflow-y: auto; padding: 16px 12px;
  display: flex; flex-direction: column;
}
.section { margin-bottom: 22px; }
.section-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;
}

/* Feature checkboxes */
.feature-filter-list {
  max-height: calc(5 * 34px); /* show exactly TOP_N rows */
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.feature-filter-list.expanded {
  max-height: 400px;
  overflow-y: auto;
}

.feature-check {
  display: flex; align-items: center; gap: 7px;
  padding: 5px 8px; border-radius: 8px; cursor: pointer;
  font-size: 12px; color: var(--text-muted);
  transition: background 0.12s; margin-bottom: 2px;
  user-select: none;
}
.feature-check:hover { background: var(--parchment); color: var(--text); }
.feature-check.active { background: #dbeeff; color: var(--text); font-weight: 500; }
.feature-check input[type=checkbox] { display: none; }
.fc-label { flex: 1; }
.count {
  font-size: 11px; color: var(--text-muted);
  background: var(--parchment); padding: 1px 6px; border-radius: 8px;
  flex-shrink: 0;
}
.feature-check.active .count { background: white; }

/* Show more button */
.show-more-btn {
  display: flex; align-items: center; gap: 5px;
  width: 100%; padding: 5px 8px; margin-top: 4px;
  background: none; border: none; cursor: pointer;
  font-size: 12px; color: var(--forest-mid); font-weight: 500;
  border-radius: 6px; transition: background 0.12s;
}
.show-more-btn:hover { background: var(--parchment); }

/* County search */
.county-search {
  position: relative; display: flex; align-items: center; margin-bottom: 6px;
}
.csearch-icon { position: absolute; left: 8px; opacity: 0.4; pointer-events: none; }
.county-search input {
  width: 100%; padding: 5px 10px 5px 26px;
  border-radius: 8px; border: 1px solid var(--border);
  font-size: 12px; outline: none; color: var(--text);
  background: var(--parchment);
}
.county-search input:focus { border-color: var(--forest-mid); background: white; }
.county-empty { font-size: 12px; color: var(--text-muted); padding: 6px 10px; }

/* County list — unified, scrolls as one */
.county-list {
  max-height: calc(5 * 28px);
  overflow: hidden;
  transition: max-height 0.3s ease;
}
.county-list.expanded {
  max-height: 400px;
  overflow-y: auto;
}
.county-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 10px; font-size: 12px; cursor: pointer;
  border-radius: 6px; color: var(--text-muted);
  transition: background 0.1s; margin-bottom: 1px;
}
.county-item:hover { background: var(--parchment); color: var(--text); }
.county-item.active { background: #dbeeff; color: var(--text); font-weight: 500; }
.county-count { color: #9aa6b0; font-size: 11px; }

/* Sliders */
.slider-wrap { padding: 0 4px; }
.slider-labels {
  display: flex; justify-content: space-between;
  font-size: 12px; color: var(--text-muted); margin-bottom: 6px;
}
.slider-val { color: var(--forest); font-weight: 600; }
input[type=range] {
  width: 100%; -webkit-appearance: none; appearance: none;
  height: 5px; border-radius: 3px; outline: none; cursor: pointer;
  background: linear-gradient(to right,
    var(--forest-mid) 0%, var(--forest-mid) var(--pct, 0%),
    #c5d8cb var(--pct, 0%), #c5d8cb 100%);
}
input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 16px; height: 16px;
  border-radius: 50%; background: var(--forest-mid);
  border: 2px solid white; box-shadow: 0 1px 4px rgba(35,122,86,0.4); cursor: pointer;
}

/* Mobile header */
.mobile-header {
  display: none;
  align-items: center;
  gap: 8px;
  padding: 10px 4px 14px;
  margin-bottom: 4px;
  border-bottom: 1px solid var(--border);
}
.mobile-search {
  flex: 1; position: relative;
  display: flex; align-items: center;
}
.msearch-icon {
  position: absolute; left: 10px; opacity: 0.4; pointer-events: none;
}
.mobile-search input {
  width: 100%; padding: 7px 12px 7px 32px;
  border-radius: 16px; border: 1px solid var(--border);
  font-size: 13px; outline: none; color: var(--text);
  background: var(--parchment);
}
.mobile-search input:focus { border-color: var(--forest-mid); background: white; }
.close-btn {
  background: none; border: none; cursor: pointer;
  padding: 4px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-muted);
}
.close-btn:hover { background: var(--parchment); }

/* ── Mobile sidebar drawer ── */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    top: 59px; left: 0; bottom: 0;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    box-shadow: none;
    width: 280px;
  }
  .sidebar.sidebar-open {
    transform: translateX(0);
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
  }
  .mobile-header { display: flex; }
}

/* Footer credit */
.sidebar-footer {
  margin-top: auto;
  padding: 16px 10px 8px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sidebar-footer p {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}
.sidebar-footer a {
  color: var(--forest-mid);
  text-decoration: none;
  font-weight: 500;
}
.sidebar-footer a:hover {
  text-decoration: underline;
}
</style>
