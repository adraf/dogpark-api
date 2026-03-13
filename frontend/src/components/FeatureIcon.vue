<!-- Renders an icons8 PNG if available, falls back to a pi icon -->
<template>
  <img
    v-if="imgSrc"
    :src="imgSrc"
    :alt="label"
    :title="label"
    class="feature-icon-img"
    :style="{ width: size + 'px', height: size + 'px' }"
    @error="imgError = true"
  />
  <i
    v-else
    :class="['pi', fallback]"
    :title="label"
    class="feature-icon-pi"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFeatures } from '../composables/useFeatures'

const props = defineProps({
  featureKey: { type: String, required: true },
  size:       { type: Number, default: 18 },
})

const { iconFile, iconFallback, label: getLabel } = useFeatures()

const imgError = ref(false)

const imgSrc  = computed(() => imgError.value ? null : iconFile(props.featureKey))
const fallback = computed(() => iconFallback(props.featureKey))
const label    = computed(() => getLabel(props.featureKey))
</script>

<style scoped>
.feature-icon-img {
  object-fit: contain;
  display: inline-block;
  flex-shrink: 0;
}
.feature-icon-pi {
  font-size: 14px;
  flex-shrink: 0;
}
</style>
