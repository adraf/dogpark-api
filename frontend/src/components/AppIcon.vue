<template>
  <img
    :src="`/icons8/icons8-${name}-50.png`"
    :alt="name"
    :title="title || name"
    class="app-icon"
    :style="{ width: size + 'px', height: size + 'px', opacity: dim ? 0.35 : 1 }"
    draggable="false"
  />
</template>

<script setup>
defineProps({
  name:  { type: String, required: true },  // slug between icons8- and -50.png
  size:  { type: Number, default: 18 },
  title: { type: String, default: '' },
  dim:   { type: Boolean, default: false }, // for empty stars etc
})
</script>

<style scoped>
.app-icon {
  object-fit: contain;
  display: inline-block;
  flex-shrink: 0;
  vertical-align: middle;
}
</style>
