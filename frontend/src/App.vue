<template>
  <div class="app-shell">
    <TopBar />
    <div class="app-body">
      <Sidebar v-if="showSidebar" />
      <main class="app-main">
        <RouterView />
      </main>
    </div>
    <PvToast />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TopBar from './components/TopBar.vue'
import Sidebar from './components/Sidebar.vue'
import { useParksStore } from './stores/parks'

const route = useRoute()
const store = useParksStore()

const showSidebar = computed(() => route.name !== 'park')

// kick off data loading
store.init()
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.app-body  { display: flex; flex: 1; overflow: hidden; }
.app-main  { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
</style>
