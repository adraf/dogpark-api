import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API = import.meta.env.DEV ? '/api' : ''

export const useParksStore = defineStore('parks', () => {
  // ── Raw data ──────────────────────────────────────────
  const allParks   = ref([])
  const counties   = ref([])
  const stats      = ref(null)
  const loading    = ref(false)
  const error      = ref(null)

  // ── Favourites (persisted) ────────────────────────────
  const favourites = ref(new Set(JSON.parse(localStorage.getItem('safepaws_favs') || '[]')))

  function toggleFavourite(id) {
    if (favourites.value.has(id)) favourites.value.delete(id)
    else favourites.value.add(id)
    localStorage.setItem('safepaws_favs', JSON.stringify([...favourites.value]))
  }

  function isFavourite(id) {
    return favourites.value.has(id)
  }

  // ── Filters ───────────────────────────────────────────
  const filters = ref({
    search:   '',
    features: [],    // array of feature keys (AND logic)
    enclosed: false,
    free:     false,
    county:   null,
    maxPrice: 30,
    minSize:  0,
    sort:     'rating',
  })

  function setFilter(key, value) {
    filters.value[key] = value
  }

  function resetFilters() {
    filters.value = { search: '', features: [], enclosed: false, free: false, county: null, maxPrice: 30, minSize: 0, sort: 'rating' }
  }

  // ── Derived ───────────────────────────────────────────
  const filteredParks = computed(() => {
    let result = allParks.value.filter(p => {
      const f = filters.value
      if (f.search) {
        const t = f.search.toLowerCase()
        if (!p.name.toLowerCase().includes(t) &&
            !p.town.toLowerCase().includes(t) &&
            !p.county.toLowerCase().includes(t) &&
            !(p.postcode || '').toLowerCase().includes(t)) return false
      }
      if (f.county   && p.county !== f.county)  return false
      if (f.enclosed && !p.is_fully_enclosed)    return false
      if (f.free     && !p.is_free)              return false
      if (f.features.length && !f.features.every(feat => (p.features || []).includes(feat))) return false
      if (f.maxPrice < 30 && !p.is_free && (p.price_per_hour || 999) > f.maxPrice) return false
      if (f.minSize  > 0  && (p.size_acres || 0) < f.minSize) return false
      return true
    })

    const s = filters.value.sort
    result.sort((a, b) => {
      if (s === 'rating') return (b.rating || 0) - (a.rating || 0)
      if (s === 'price')  return (a.price_per_hour || 999) - (b.price_per_hour || 999)
      if (s === 'size')   return (b.size_acres || 0) - (a.size_acres || 0)
      return a.name.localeCompare(b.name)
    })
    return result
  })

  const favouriteParks = computed(() =>
    allParks.value.filter(p => favourites.value.has(p.id))
  )

  const countByFeature = computed(() => {
    const counts = {}
    allParks.value.forEach(p => (p.features || []).forEach(f => {
      counts[f] = (counts[f] || 0) + 1
    }))
    return counts
  })

  // ── Fetch ─────────────────────────────────────────────
  async function fetchAll() {
    loading.value = true
    error.value   = null
    try {
      const res  = await fetch(`${API}/parks?per_page=500`)
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      allParks.value = data.results
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchPark(id) {
    try {
      const res = await fetch(`${API}/parks/${id}`)
      if (!res.ok) throw new Error()
      return await res.json()
    } catch {
      return allParks.value.find(p => p.id === id) || null
    }
  }

  async function fetchCounties() {
    try {
      const res  = await fetch(`${API}/counties`)
      counties.value = await res.json()
    } catch {}
  }

  async function fetchStats() {
    try {
      const res = await fetch(`${API}/stats`)
      stats.value = await res.json()
    } catch {}
  }

  function init() {
    fetchAll()
    fetchCounties()
    fetchStats()
  }

  return {
    allParks, counties, stats, loading, error,
    favourites, toggleFavourite, isFavourite,
    filters, setFilter, resetFilters,
    filteredParks, favouriteParks, countByFeature,
    fetchAll, fetchPark, fetchCounties, fetchStats, init,
  }
})
