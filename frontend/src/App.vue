<template>
  <div class="app-shell">
    <TopBar :sidebar-open="sidebarOpen" @toggle-sidebar="sidebarOpen = !sidebarOpen" />

    <!-- Mobile overlay -->
    <Transition name="overlay">
      <div v-if="sidebarOpen && isMobile" class="mobile-overlay" @click="sidebarOpen = false" />
    </Transition>

    <div class="app-body">
      <Sidebar
        v-if="showSidebar"
        :class="{ 'sidebar-open': sidebarOpen, 'sidebar-mobile': isMobile }"
        @close="sidebarOpen = false"
      />
      <main class="app-main">
        <RouterView />
      </main>
    </div>
    <PvToast />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import TopBar from './components/TopBar.vue'
import Sidebar from './components/Sidebar.vue'
import { useParksStore } from './stores/parks'

const route = useRoute()
const store = useParksStore()

const sidebarOpen = ref(false)
const windowWidth = ref(window.innerWidth)

const isMobile   = computed(() => windowWidth.value < 768)
const showSidebar = computed(() => route.name !== 'park')

function onResize() {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) sidebarOpen.value = false
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  store.init()
})
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.app-body  { display: flex; flex: 1; overflow: hidden; position: relative; }
.app-main  { flex: 1; overflow: hidden; display: flex; flex-direction: column; }

.mobile-overlay {
  position: fixed; inset: 0; z-index: 40;
  background: rgba(0,0,0,0.4);
}
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.25s; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
</style>
