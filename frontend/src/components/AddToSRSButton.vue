<template>
  <button
    @click="addToSRS"
    :disabled="loading || isAdded"
    :class="[
      'flex items-center space-x-2 px-3 py-1 text-sm font-medium rounded-full transition-colors duration-200',
      isAdded ? 'bg-green-100 text-green-800 cursor-default' : 'bg-purple-100 text-purple-800 hover:bg-purple-200 active:bg-purple-300',
      loading ? 'opacity-50 cursor-wait' : ''
    ]"
    :title="isAdded ? 'Word added to SRS deck' : 'Add word to SRS deck for spaced repetition learning'"
  >
    <span v-if="loading" class="animate-spin">⏳</span>
    <span v-else-if="isAdded">✅</span>
    <span v-else>🧠</span>
    <span>{{ buttonText }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const props = defineProps<{
  lemma: string
}>()

const authStore = useAuthStore()
const loading = ref(false)
const isAdded = ref(false)
const error = ref('')

const buttonText = computed(() => {
  if (loading.value) return 'Adding...'
  if (isAdded.value) return 'In SRS'
  return 'Add to SRS'
})

const addToSRS = async () => {
  if (!authStore.isAuthenticated || loading.value || isAdded.value) return

  loading.value = true
  error.value = ''

  try {
    // First, we need to find the word's lemma_id from the database
    // Since we don't have direct access to the lemma_id in the WordResult,
    // we'll call the backend to add by lemma string, and let the backend handle the lookup
    
    const response = await axios.post('/srs/add-word-by-lemma', {
      lemma: props.lemma,
      initial_quality: 3 // Default quality for new cards
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })

    if (response.data.success) {
      isAdded.value = true
      // Show success feedback briefly
      setTimeout(() => {
        // Keep the button in "added" state permanently for this session
      }, 1000)
    }
  } catch (err: any) {
    console.error('Failed to add word to SRS:', err)
    
    if (err.response?.status === 400 && err.response?.data?.detail?.includes('already exists')) {
      // Word is already in SRS
      isAdded.value = true
    } else {
      error.value = err.response?.data?.detail || 'Failed to add word to SRS'
      // Show error briefly, then reset
      setTimeout(() => {
        error.value = ''
      }, 3000)
    }
  } finally {
    loading.value = false
  }
}
</script>