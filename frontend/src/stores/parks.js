import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API = import.meta.env.DEV ? '/api' : ''
const PER_PAGE = 21

export const useParksStore = defineStore('parks', () => {
  // ── Data ──────────────────────────────────────────────
  const parks      = ref([])   // current page results
  const total      = ref(0)    // total matching parks
  const allParks   = ref([])   // all parks for map view + filters
  const counties   = ref([])
  const loading    = ref(false)
  const error      = ref(null)
  const page       = ref(1)

  // ── Favourites ────────────────────────────────────────
  const favourites = ref(new Set(JSON.parse(localStorage.getItem('safepaws_favs') || '[]')))

  function toggleFavourite(id) {
    if (favourites.value.has(id)) favourites.value.delete(id)
    else favourites.value.add(id)
    localStorage.setItem('safepaws_favs', JSON.stringify([...favourites.value]))
  }

  function isFavourite(id) { return favourites.value.has(id) }

  // ── Filters ───────────────────────────────────────────
  const filters = ref({
    search:   '',
    features: [],
    county:   null,
    sort:     'rating',
  })
  function setFilter(key, value) {
    filters.value[key] = value
    page.value = 1
    fetchPage()
  }

  function resetFilters() {
    filters.value = { search: '', features: [], county: null, sort: 'rating' }
    page.value = 1
    fetchPage()
  }

  // ── Build query params ────────────────────────────────
  function buildParams(pageNum = 1, perPage = PER_PAGE) {
    const f = filters.value
    const params = new URLSearchParams()
    params.set('page', pageNum)
    params.set('per_page', perPage)
    if (f.search)   params.set('q_search', f.search)
    if (f.county)   params.set('county', f.county)
    if (f.features.length) f.features.forEach(feat => params.append('feature', feat))
    params.set('sort', f.sort)
    return params
  }

  // ── Fetch current page ────────────────────────────────
  async function fetchPage(pageNum = page.value, retries = 3) {
    loading.value = true
    error.value   = null
    for (let i = 0; i < retries; i++) {
      try {
        const params = buildParams(pageNum)
        const res    = await fetch(`${API}/parks?${params}`)
        if (!res.ok) throw new Error(`API error ${res.status}`)
        const data   = await res.json()
        parks.value  = data.results
        total.value  = data.total
        page.value   = pageNum
        loading.value = false
        return
      } catch (e) {
        if (i < retries - 1) await new Promise(r => setTimeout(r, 1500))
        else error.value = e.message
      }
    }
    loading.value = false
  }

  function goToPage(p) { fetchPage(p) }

  // ── Fetch ALL for map view (no pagination) ────────────
  async function fetchAll() {
    try {
      const params = buildParams(1, 2000)
      const res    = await fetch(`${API}/parks?${params}`)
      if (!res.ok) return
      const data   = await res.json()
      allParks.value = data.results
      // If more pages, fetch them
      for (let p = 2; p <= data.pages; p++) {
        const r = await fetch(`${API}/parks?${buildParams(p, 2000)}`)
        if (r.ok) {
          const d = await r.json()
          allParks.value = [...allParks.value, ...d.results]
        }
      }
    } catch (e) {
      console.error('fetchAll error', e)
    }
  }

  // ── Fetch single park ─────────────────────────────────
  async function fetchPark(id) {
    try {
      const res = await fetch(`${API}/parks/${id}`)
      if (!res.ok) throw new Error()
      return await res.json()
    } catch {
      return parks.value.find(p => p.id === id) || allParks.value.find(p => p.id === id) || null
    }
  }

  async function fetchCounties() {
    try {
      const res  = await fetch(`${API}/counties`)
      counties.value = await res.json()
    } catch {}
  }

  // ── Derived ───────────────────────────────────────────
  const totalPages = computed(() => Math.ceil(total.value / PER_PAGE))

  const favouriteParks = computed(() =>
    allParks.value.filter(p => favourites.value.has(p.id))
  )

  const hasActiveFilters = computed(() => {
    const f = filters.value
    return f.search || f.county || (f.features && f.features.length > 0)
  })

  // ── Init ──────────────────────────────────────────────
  function init() {
    fetchPage(1)
    fetchCounties()
    fetchAll() // background fetch for sidebar counts and map
  }

  return {
    parks, total, allParks, counties, loading, error, page, totalPages,
    favourites, toggleFavourite, isFavourite,
    filters, setFilter, resetFilters, hasActiveFilters,
    fetchPage, goToPage, fetchAll, fetchPark, fetchCounties, init,
    favouriteParks,
    PER_PAGE,
  }
})
