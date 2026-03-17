<template>
  <AppIcon v-if="slug" :name="slug" :size="size" :title="label" />
  <span v-else :title="label" style="font-size:13px;color:var(--text-muted)">?</span>
</template>

<script setup>
import { computed } from 'vue'
import { useFeatures } from '../composables/useFeatures'

const props = defineProps({
  featureKey: { type: String, required: true },
  size:       { type: Number, default: 18 },
})

const { iconFile, label: getLabel } = useFeatures()
const slug  = computed(() => iconFile(props.featureKey))
const label = computed(() => getLabel(props.featureKey))
</script>
