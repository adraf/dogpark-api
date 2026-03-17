import { createRouter, createWebHistory } from 'vue-router'
import ExploreView from '../views/ExploreView.vue'
import ParkView from '../views/ParkView.vue'
import FavouritesView from '../views/FavouritesView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',            name: 'explore',    component: ExploreView },
    { path: '/favourites',  name: 'favourites', component: FavouritesView },
    { path: '/park/:id',    name: 'park',       component: ParkView },
  ]
})
