<template>
  <header class="topbar">
    <!-- Burger (mobile only) -->
    <button class="burger" @click="$emit('toggle-sidebar')" aria-label="Menu">
      <AppIcon :name="sidebarOpen ? 'close' : 'menu'" :size="22" />
    </button>

    <RouterLink to="/" class="logo">
      <AppIcon name="secure" :size="22" />
      <span class="logo-text">SafePaws UK</span>
    </RouterLink>

    <!-- Search (hidden on mobile — lives in sidebar drawer instead) -->
    <div class="search-wrap desktop-only">
      <AppIcon name="search" :size="16" class="search-icon" />
      <input
        v-model="searchTerm"
        type="text"
        placeholder="Search by name, town, or county..."
        @input="store.setFilter('search', searchTerm)"
      />
    </div>

    <nav class="nav-tabs">
      <RouterLink to="/" class="nav-tab" :class="{ active: route.name === 'explore' }">
        <AppIcon name="compass" :size="15" />
        <span class="tab-text">Explore</span>
      </RouterLink>
      <RouterLink to="/favourites" class="nav-tab" :class="{ active: route.name === 'favourites' }">
        <AppIcon name="heart" :size="15" />
        <span class="tab-text">Favourites</span>
        <span v-if="store.favourites.size" class="fav-badge">{{ store.favourites.size }}</span>
      </RouterLink>
    </nav>
  </header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useParksStore } from '../stores/parks'

defineProps({ sidebarOpen: { type: Boolean, default: false } })
defineEmits(['toggle-sidebar'])

const route      = useRoute()
const store      = useParksStore()
const searchTerm = ref(store.filters.search)

watch(() => store.filters.search, v => { searchTerm.value = v })
</script>

<style scoped>
.topbar {
  display: flex; align-items: center; gap: 12px;
  height: 56px; padding: 0 16px;
  background: var(--forest);
  border-bottom: 3px solid var(--gold);
  flex-shrink: 0;
}

/* Burger — mobile only */
.burger {
  display: none;
  background: none; border: none; cursor: pointer;
  padding: 4px; border-radius: 6px; flex-shrink: 0;
  align-items: center; justify-content: center;
}
.burger :deep(.app-icon) { filter: brightness(0) invert(1); }

.logo {
  display: flex; align-items: center; gap: 8px;
  color: white; font-size: 18px; font-weight: 600;
  font-family: Georgia, serif; text-decoration: none; white-space: nowrap;
}

.search-wrap {
  flex: 1; max-width: 480px; position: relative;
  display: flex; align-items: center;
}
.search-icon {
  position: absolute; left: 12px; opacity: 0.6;
  pointer-events: none; filter: brightness(0) invert(1);
}
.search-wrap input {
  width: 100%; padding: 8px 16px 8px 36px;
  border-radius: 20px; border: none;
  background: rgba(255,255,255,0.13); color: white;
  font-size: 14px; outline: none;
}
.search-wrap input::placeholder { color: rgba(255,255,255,0.45); }
.search-wrap input:focus { background: rgba(255,255,255,0.22); }

.nav-tabs { display: flex; gap: 4px; margin-left: auto; }
.nav-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.25);
  color: rgba(255,255,255,0.75); font-size: 13px;
  text-decoration: none; transition: all 0.15s;
}
.nav-tab :deep(.app-icon) { filter: brightness(0) invert(1); opacity: 0.75; }
.nav-tab:hover { background: rgba(255,255,255,0.1); color: white; }
.nav-tab.active { background: var(--gold); color: var(--forest); border-color: var(--gold); font-weight: 600; }
.nav-tab.active :deep(.app-icon) { filter: none; opacity: 1; }

.fav-badge {
  background: var(--forest); color: white;
  font-size: 10px; font-weight: 700;
  padding: 1px 5px; border-radius: 8px; margin-left: 2px;
}

/* ── Mobile ── */
@media (max-width: 767px) {
  .burger { display: flex; }
  .logo-text { font-size: 16px; }
  .desktop-only { display: none; }
  .tab-text { display: none; }
  .nav-tab { padding: 6px 10px; }
}
</style>
