import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Toast from 'primevue/toast'

// PrimeVue components used across the app
import Button from 'primevue/button'
import Select from 'primevue/select'
import Paginator from 'primevue/paginator'
import ProgressSpinner from 'primevue/progressspinner'
import Badge from 'primevue/badge'
import Tag from 'primevue/tag'
import Chip from 'primevue/chip'
import Divider from 'primevue/divider'
import Skeleton from 'primevue/skeleton'

import FeatureIcon from './components/FeatureIcon.vue'
import AppIcon from './components/AppIcon.vue'
import router from './router'
import App from './App.vue'

import 'primeicons/primeicons.css'
import 'leaflet/dist/leaflet.css'
import './assets/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: '.dark',
      cssLayer: false
    }
  }
})
app.use(ToastService)
app.use(ConfirmationService)

// Register globally so all components can use without importing
app.component('PvButton', Button)
app.component('PvSelect', Select)
app.component('PvPaginator', Paginator)
app.component('PvProgressSpinner', ProgressSpinner)
app.component('PvBadge', Badge)
app.component('PvTag', Tag)
app.component('PvChip', Chip)
app.component('PvDivider', Divider)
app.component('PvSkeleton', Skeleton)
app.component('PvToast', Toast)
app.component('FeatureIcon', FeatureIcon)
app.component('AppIcon', AppIcon)

app.mount('#app')
