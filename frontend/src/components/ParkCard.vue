<template>
  <div class="park-card" @click="$router.push(`/park/${park.id}`)">
    <div class="card-img">
      <div class="card-img-pattern" />
      <button
        class="fav-btn" :class="{ active: store.isFavourite(park.id) }"
        @click.stop="store.toggleFavourite(park.id)"
        :title="store.isFavourite(park.id) ? 'Remove from favourites' : 'Add to favourites'"
      >
        <AppIcon :name="store.isFavourite(park.id) ? 'heart' : 'heart-1'" :size="16" />
      </button>
      <span v-if="park.is_fully_enclosed" class="card-badge">
        <AppIcon name="lock" :size="12" /> Fully enclosed
      </span>
    </div>

    <div class="card-body">
      <div class="card-name">{{ park.name }}</div>
      <div class="card-loc">
        <AppIcon name="location" :size="13" />
        {{ park.town }}, {{ park.county }}
      </div>

      <div class="card-meta">
        <span v-if="park.is_free" class="pill free">Free</span>
        <span v-else-if="park.price_per_hour" class="pill price">£{{ park.price_per_hour }}/hr</span>
        <span v-if="park.size_acres" class="pill size">{{ park.size_acres }} acres</span>
        <span v-if="park.fence_height_m" class="pill">{{ park.fence_height_m }}m fence</span>
      </div>

      <div class="card-footer">
        <div class="stars">
          <AppIcon
            v-for="n in 5" :key="n"
            name="star"
            :size="13"
            :dim="n > Math.round(park.rating || 0)"
          />
        </div>
        <span class="rating-text">{{ park.rating || '—' }} ({{ park.review_count || 0 }})</span>
        <div class="feat-icons">
          <FeatureIcon
            v-for="f in (park.features || []).slice(0, 4)" :key="f"
            :feature-key="f" :size="18"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useParksStore } from '../stores/parks'
defineProps({ park: { type: Object, required: true } })
const store = useParksStore()
</script>

<style scoped>
.park-card {
  background: white; border-radius: 12px; border: 1px solid var(--border);
  overflow: hidden; cursor: pointer; transition: all 0.15s;
}
.park-card:hover {
  transform: translateY(-2px); border-color: var(--forest-light);
  box-shadow: 0 4px 16px rgba(26,74,53,0.12);
}
.card-img {
  height: 96px;
  background: linear-gradient(135deg, #1a4a35 0%, #237a56 55%, #3aaa75 100%);
  position: relative; display: flex; align-items: flex-end; padding: 8px 10px;
}
.card-img-pattern {
  position: absolute; inset: 0; opacity: 0.1;
  background-image:
    radial-gradient(circle at 20% 50%, white 1px, transparent 1px),
    radial-gradient(circle at 80% 20%, white 1px, transparent 1px),
    radial-gradient(circle at 60% 80%, white 1px, transparent 1px);
  background-size: 40px 40px;
}
.fav-btn {
  position: absolute; top: 8px; right: 8px; z-index: 2;
  background: rgba(255,255,255,0.92); border: none; border-radius: 50%;
  width: 30px; height: 30px; display: flex; align-items: center;
  justify-content: center; cursor: pointer; transition: all 0.15s;
}
.fav-btn:hover { background: white; transform: scale(1.1); }

.card-badge {
  background: rgba(255,255,255,0.92); color: var(--forest);
  font-size: 10px; font-weight: 600; padding: 3px 8px;
  border-radius: 8px; position: relative; z-index: 1;
  display: flex; align-items: center; gap: 4px;
}
.card-body { padding: 11px 12px; }
.card-name {
  font-size: 14px; font-weight: 600; color: var(--text);
  font-family: Georgia, serif; margin-bottom: 3px;
}
.card-loc {
  font-size: 12px; color: var(--text-muted);
  display: flex; align-items: center; gap: 4px; margin-bottom: 8px;
}
.card-meta { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
.pill { font-size: 11px; padding: 3px 8px; border-radius: 8px; background: var(--tag-bg); color: var(--tag-text); font-weight: 500; }
.pill.price { background: #fff3d6; color: #7a5500; }
.pill.free  { background: #d9f4e8; color: #0e5c33; }
.pill.size  { background: #dbeeff; color: #1a4f85; }
.card-footer { display: flex; align-items: center; gap: 6px; }
.stars { display: flex; gap: 1px; }
.rating-text { font-size: 12px; color: var(--text-muted); }
.feat-icons { display: flex; gap: 5px; margin-left: auto; align-items: center; }
</style>
