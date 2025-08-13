<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-bold text-gray-900">Search History</h1>
    
    <div class="bg-white rounded-lg shadow-md p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-gray-800">Your Recent Searches</h2>
        <button @click="loadHistory" class="btn-secondary">
          Refresh
        </button>
      </div>
      
      <div v-if="isLoading" class="text-center py-8 text-gray-500">
        Loading your search history...
      </div>
      
      <div v-else-if="searchStore.searchHistory.length === 0" class="text-center py-8 text-gray-500">
        No search history yet. Start searching to build your personalized history!
      </div>
      
      <div v-else class="space-y-3">
        <div 
          v-for="item in searchStore.searchHistory" 
          :key="item.id"
          class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          <div class="flex-1">
            <div class="flex items-center space-x-3">
              <span 
                class="px-2 py-1 text-xs rounded-full"
                :class="getTypeColor(item.query_type)"
              >
                {{ formatQueryType(item.query_type) }}
              </span>
              <span class="font-medium text-gray-900">{{ item.query_text }}</span>
            </div>
            <p class="text-sm text-gray-500 mt-1">
              {{ formatDate(item.timestamp) }}
            </p>
          </div>
          
          <div class="flex items-center space-x-2">
            <button 
              @click="searchAgain(item)"
              class="text-primary-600 hover:text-primary-800 text-sm font-medium"
            >
              Search Again
            </button>
            <button 
              @click="deleteItem(item.id)"
              class="text-red-600 hover:text-red-800 text-sm"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSearchStore } from '@/stores/search'
import { useRouter } from 'vue-router'

const searchStore = useSearchStore()
const router = useRouter()
const isLoading = ref(false)

const loadHistory = async () => {
  isLoading.value = true
  try {
    await searchStore.getSearchHistory()
  } catch (error) {
    console.error('Failed to load history:', error)
  } finally {
    isLoading.value = false
  }
}

const deleteItem = async (id: number) => {
  if (confirm('Are you sure you want to delete this search history item?')) {
    try {
      await searchStore.deleteHistoryItem(id)
    } catch (error) {
      console.error('Failed to delete item:', error)
    }
  }
}

const searchAgain = async (item: any) => {
  try {
    if (item.query_type.includes('word')) {
      await searchStore.analyzeWord(item.query_text)
    } else if (item.query_type.includes('sentence')) {
      await searchStore.translateSentence(item.query_text)
    }
    router.push('/')
  } catch (error) {
    console.error('Search failed:', error)
  }
}

const getTypeColor = (type: string) => {
  if (type.includes('word')) return 'bg-blue-100 text-blue-800'
  if (type.includes('sentence')) return 'bg-green-100 text-green-800'
  return 'bg-gray-100 text-gray-800'
}

const formatQueryType = (type: string) => {
  if (type.includes('word')) return 'Word'
  if (type.includes('sentence')) return 'Sentence'
  return type
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadHistory()
})
</script>