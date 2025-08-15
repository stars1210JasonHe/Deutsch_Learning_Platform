<template>
  <button
    @click="toggleFavorite"
    :disabled="isLoading"
    class="favorite-btn"
    :class="{
      'favorite-active': isFavorite,
      'favorite-inactive': !isFavorite,
      'loading': isLoading
    }"
    :title="isFavorite ? 'Remove from favorites' : 'Add to favorites'"
  >
    <span v-if="isLoading" class="text-sm">⏳</span>
    <span v-else-if="isFavorite" class="text-lg">⭐</span>
    <span v-else class="text-lg">☆</span>
  </button>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFavoritesStore } from '@/stores/favorites'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  lemma: string
}>()

const favoritesStore = useFavoritesStore()
const authStore = useAuthStore()
const isFavorite = ref(false)
const isLoading = ref(false)
const error = ref('')

const checkFavoriteStatus = async () => {
  if (!authStore.isAuthenticated) return
  
  try {
    isFavorite.value = await favoritesStore.checkIfFavorite(props.lemma)
  } catch (err) {
    console.error('Error checking favorite status:', err)
  }
}

const toggleFavorite = async () => {
  if (!authStore.isAuthenticated) {
    error.value = 'Please login to use favorites'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    if (isFavorite.value) {
      await favoritesStore.removeFromFavorites(props.lemma)
      isFavorite.value = false
    } else {
      await favoritesStore.addToFavorites(props.lemma)
      isFavorite.value = true
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to update favorites'
    console.error('Error toggling favorite:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  checkFavoriteStatus()
})
</script>

<style scoped>
.favorite-btn {
  @apply p-2 rounded-full transition-all duration-200 hover:scale-110;
}

.favorite-active {
  @apply bg-yellow-100 text-yellow-600 hover:bg-yellow-200 border border-yellow-300;
}

.favorite-inactive {
  @apply bg-gray-100 text-gray-500 hover:bg-gray-200 border border-gray-300;
}

.favorite-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.loading {
  @apply animate-pulse;
}
</style>