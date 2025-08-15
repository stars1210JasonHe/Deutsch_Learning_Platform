<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">⭐ My Favorites</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        Your starred words collection
      </p>
    </div>

    <!-- Loading -->
    <div v-if="favoritesStore.isLoading" class="text-center py-12">
      <div class="loading-cosmic text-4xl mb-4">🌌</div>
      <p class="text-gray-400">Loading your favorites...</p>
    </div>

    <!-- Error -->
    <div v-if="favoritesStore.error" class="max-w-2xl mx-auto">
      <div class="glass-card bg-red-500/10 border-red-500/20 p-6">
        <div class="flex items-center space-x-2 text-red-400 mb-4">
          <span>⚠️</span>
          <span class="font-semibold">Error</span>
        </div>
        <p class="text-gray-300">{{ favoritesStore.error }}</p>
        <div class="mt-4 flex justify-center">
          <button @click="favoritesStore.loadFavorites()" class="btn-secondary">Retry</button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!favoritesStore.isLoading && !favoritesStore.error && favoritesStore.favorites.length === 0" 
         class="text-center py-12">
      <div class="text-6xl mb-6">📚</div>
      <h2 class="text-2xl font-semibold text-cosmic mb-4">No Favorites Yet</h2>
      <p class="text-gray-400 mb-6 max-w-md mx-auto">
        Start exploring German words and click the star icon to add them to your favorites collection.
      </p>
      <router-link to="/" class="btn-primary">
        🔍 Start Searching
      </router-link>
    </div>

    <!-- Favorites List -->
    <div v-if="!favoritesStore.isLoading && favoritesStore.favorites.length > 0" class="max-w-4xl mx-auto">
      <div class="glass-card p-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-semibold text-cosmic">
            {{ favoritesStore.favorites.length }} Favorite{{ favoritesStore.favorites.length !== 1 ? 's' : '' }}
          </h2>
          <div class="flex space-x-4">
            <button @click="sortBy = 'added'" :class="sortBy === 'added' ? 'btn-primary' : 'btn-secondary'">
              📅 Recent
            </button>
            <button @click="sortBy = 'alpha'" :class="sortBy === 'alpha' ? 'btn-primary' : 'btn-secondary'">
              🔤 A-Z
            </button>
          </div>
        </div>

        <div class="grid gap-4">
          <div 
            v-for="favorite in sortedFavorites" 
            :key="favorite.id"
            class="border border-gray-600 rounded-lg p-4 hover:border-cosmic/50 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="flex items-center space-x-2">
                  <h3 class="text-xl font-semibold text-white">{{ favorite.lemma }}</h3>
                  <SpeechButton :text="favorite.lemma" size="sm" />
                  <button
                    @click="searchWord(favorite.lemma)"
                    class="text-cosmic hover:text-aurora transition-colors text-sm"
                    title="Search this word"
                  >
                    🔍
                  </button>
                </div>
                <div class="flex space-x-2">
                  <span v-if="favorite.pos" class="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                    {{ favorite.pos }}
                  </span>
                  <span v-if="favorite.cefr" class="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs">
                    {{ favorite.cefr }}
                  </span>
                </div>
              </div>
              <div class="flex items-center space-x-3">
                <span class="text-sm text-gray-400">
                  {{ formatDate(favorite.added_at) }}
                </span>
                <button
                  @click="removeFavorite(favorite.lemma)"
                  class="text-red-400 hover:text-red-300 transition-colors p-1"
                  title="Remove from favorites"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFavoritesStore } from '@/stores/favorites'
import { useSearchStore } from '@/stores/search'
import { useAuthStore } from '@/stores/auth'
import SpeechButton from '@/components/SpeechButton.vue'

const router = useRouter()
const favoritesStore = useFavoritesStore()
const searchStore = useSearchStore()
const authStore = useAuthStore()

const sortBy = ref<'added' | 'alpha'>('added')

const sortedFavorites = computed(() => {
  const favorites = [...favoritesStore.favorites]
  
  if (sortBy.value === 'alpha') {
    return favorites.sort((a, b) => a.lemma.localeCompare(b.lemma))
  } else {
    return favorites.sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime())
  }
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 1) {
    return 'Just now'
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}h ago`
  } else if (diffInHours < 24 * 7) {
    return `${Math.floor(diffInHours / 24)}d ago`
  } else {
    return date.toLocaleDateString()
  }
}

const searchWord = async (lemma: string) => {
  try {
    await searchStore.analyzeWord(lemma)
    router.push('/')
  } catch (error: any) {
    console.error('Failed to search word:', error)
  }
}

const removeFavorite = async (lemma: string) => {
  if (confirm(`Remove "${lemma}" from favorites?`)) {
    try {
      await favoritesStore.removeFromFavorites(lemma)
    } catch (error: any) {
      console.error('Failed to remove favorite:', error)
    }
  }
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  await favoritesStore.loadFavorites()
})
</script>