<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">🧠 SRS Review Station 🚀</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        Master German vocabulary through spaced repetition across the cosmos
      </p>
    </div>

    <!-- Review Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
      <div class="card-cosmic text-center">
        <div class="text-2xl mb-1">⏰</div>
        <div class="text-lg font-bold text-cosmic">{{ dueCards.length }}</div>
        <div class="text-sm text-gray-400">Due Now</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-2xl mb-1">✅</div>
        <div class="text-lg font-bold text-aurora">{{ sessionStats.correct }}</div>
        <div class="text-sm text-gray-400">Correct</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-2xl mb-1">❌</div>
        <div class="text-lg font-bold text-orange-400">{{ sessionStats.incorrect }}</div>
        <div class="text-sm text-gray-400">Incorrect</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-2xl mb-1">📊</div>
        <div class="text-lg font-bold text-cosmic">{{ Math.round(sessionStats.accuracy) }}%</div>
        <div class="text-sm text-gray-400">Accuracy</div>
      </div>
    </div>

    <!-- Review Card -->
    <div v-if="currentCard && !reviewComplete" class="max-w-2xl mx-auto">
      <div class="glass-card p-8">
        <!-- Progress Bar -->
        <div class="mb-6">
          <div class="flex justify-between text-sm text-gray-400 mb-2">
            <span>Review Progress</span>
            <span>{{ reviewedCards }} / {{ totalCards }}</span>
          </div>
          <div class="progress-cosmic">
            <div 
              class="progress-fill" 
              :style="{ width: progressPercentage + '%' }"
            ></div>
          </div>
        </div>

        <!-- Card Content -->
        <div class="text-center">
          <div class="mb-6">
            <div class="flex items-center justify-center space-x-4 mb-4">
              <div class="text-4xl font-bold text-white">
                {{ currentCard.lemma }}
              </div>
              <SpeechButton :text="currentCard.lemma" size="lg" />
            </div>
            <div class="text-sm text-gray-400 mb-2">
              {{ currentCard.pos }} • {{ currentCard.streak }} streak
            </div>
          </div>

          <!-- Show Answer Button -->
          <div v-if="!showAnswer" class="mb-8">
            <button @click="showAnswer = true" class="btn-primary px-8 py-3">
              🔍 Show Answer
            </button>
          </div>

          <!-- Answer Content -->
          <div v-else class="mb-8 space-y-4">
            <div v-if="currentCard.translations_en.length > 0">
              <div class="text-sm text-gray-400 mb-1">English:</div>
              <div class="flex items-center justify-center space-x-2">
                <div class="text-lg text-aurora">
                  {{ currentCard.translations_en.join(', ') }}
                </div>
                <SpeechButton :text="currentCard.translations_en.join(', ')" size="sm" lang="en-US" />
              </div>
            </div>
            
            <div v-if="currentCard.translations_zh.length > 0">
              <div class="text-sm text-gray-400 mb-1">Chinese:</div>
              <div class="flex items-center justify-center space-x-2">
                <div class="text-lg text-cosmic">
                  {{ currentCard.translations_zh.join(', ') }}
                </div>
                <SpeechButton :text="currentCard.translations_zh.join(', ')" size="sm" lang="zh-CN" />
              </div>
            </div>

            <div v-if="currentCard.examples && currentCard.examples.length > 0">
              <div class="text-sm text-gray-400 mb-1">Example:</div>
              <div class="flex items-center justify-center space-x-2 mb-2">
                <div class="text-gray-300 italic">
                  "{{ currentCard.examples[0].de }}"
                </div>
                <SpeechButton :text="currentCard.examples[0].de" size="sm" />
              </div>
              <div class="flex items-center justify-center space-x-2">
                <div class="text-sm text-gray-500">
                  {{ currentCard.examples[0].en }}
                </div>
                <SpeechButton v-if="currentCard.examples[0].en" :text="currentCard.examples[0].en" size="sm" lang="en-US" />
              </div>
              <div v-if="currentCard.examples[0].zh" class="flex items-center justify-center space-x-2 mt-1">
                <div class="text-sm text-gray-500">
                  {{ currentCard.examples[0].zh }}
                </div>
                <SpeechButton :text="currentCard.examples[0].zh" size="sm" lang="zh-CN" />
              </div>
            </div>

            <!-- Quality Buttons -->
            <div class="pt-6">
              <div class="text-sm text-gray-400 mb-4">How well did you know this word?</div>
              <div class="flex flex-wrap justify-center gap-3">
                <button 
                  @click="reviewCard(0)" 
                  class="btn-secondary bg-red-500/20 border-red-500/40 hover:bg-red-500/30 text-red-300"
                >
                  😵 Total Blackout
                </button>
                <button 
                  @click="reviewCard(1)" 
                  class="btn-secondary bg-orange-500/20 border-orange-500/40 hover:bg-orange-500/30 text-orange-300"
                >
                  😰 Hard
                </button>
                <button 
                  @click="reviewCard(3)" 
                  class="btn-secondary bg-yellow-500/20 border-yellow-500/40 hover:bg-yellow-500/30 text-yellow-300"
                >
                  🤔 Good
                </button>
                <button 
                  @click="reviewCard(4)" 
                  class="btn-secondary bg-green-500/20 border-green-500/40 hover:bg-green-500/30 text-green-300"
                >
                  😊 Easy
                </button>
                <button 
                  @click="reviewCard(5)" 
                  class="btn-secondary bg-purple-500/20 border-purple-500/40 hover:bg-purple-500/30 text-purple-300"
                >
                  🚀 Perfect
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Cards Available -->
    <div v-else-if="!reviewComplete && dueCards.length === 0" class="text-center py-12">
      <div class="glass-card p-8 max-w-2xl mx-auto">
        <div class="text-6xl mb-6">🌟</div>
        <h2 class="text-2xl font-semibold text-cosmic mb-4">All Caught Up!</h2>
        <p class="text-gray-400 mb-6">
          No cards are due for review right now. Great job staying on top of your studies!
        </p>
        
        <div class="space-y-4">
          <div class="text-sm text-gray-500">
            Next review in: {{ nextReviewTime }}
          </div>
          <div class="flex justify-center space-x-4">
            <router-link to="/dashboard" class="btn-primary">
              📊 View Dashboard
            </router-link>
            <router-link to="/" class="btn-secondary">
              🔍 Search Words
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Review Complete -->
    <div v-else-if="reviewComplete" class="text-center py-12">
      <div class="glass-card p-8 max-w-2xl mx-auto">
        <div class="text-6xl mb-6">🎉</div>
        <h2 class="text-2xl font-semibold text-cosmic mb-4">Review Session Complete!</h2>
        
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div class="text-2xl font-bold text-aurora">{{ sessionStats.correct }}</div>
            <div class="text-sm text-gray-400">Correct Answers</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-cosmic">{{ Math.round(sessionStats.accuracy) }}%</div>
            <div class="text-sm text-gray-400">Accuracy Rate</div>
          </div>
        </div>

        <div class="text-gray-400 mb-6">
          You reviewed {{ reviewedCards }} cards in {{ Math.round(sessionDuration / 60) }} minutes
        </div>

        <div class="flex justify-center space-x-4">
          <button @click="startNewSession" class="btn-primary">
            🔄 Review More
          </button>
          <router-link to="/dashboard" class="btn-secondary">
            📊 View Dashboard
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="loading-cosmic text-4xl mb-4">🌌</div>
      <p class="text-gray-400">Loading your cards from the cosmic database...</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="max-w-2xl mx-auto">
      <div class="glass-card bg-red-500/10 border-red-500/20 p-4">
        <div class="flex items-center space-x-2 text-red-400">
          <span>⚠️</span>
          <span>{{ error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import SpeechButton from '@/components/SpeechButton.vue'

const authStore = useAuthStore()

interface SRSCard {
  card_id: number
  lemma: string
  pos: string
  translations_en: string[]
  translations_zh: string[]
  examples: Array<{ de: string, en: string, zh: string }>
  streak: number
  days_overdue: number
}

// Reactive data
const loading = ref(false)
const error = ref('')
const dueCards = ref<SRSCard[]>([])
const currentCardIndex = ref(0)
const showAnswer = ref(false)
const reviewComplete = ref(false)
const sessionId = ref<number | null>(null)
const sessionStartTime = ref(Date.now())
const nextReviewTime = ref('Loading...')

const sessionStats = ref({
  correct: 0,
  incorrect: 0,
  total: 0,
  accuracy: 0
})

const API_BASE = 'http://localhost:8000'

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authStore.token}`,
  'Content-Type': 'application/json'
})

// Computed properties
const currentCard = computed(() => {
  return dueCards.value[currentCardIndex.value] || null
})

const totalCards = computed(() => dueCards.value.length)
const reviewedCards = computed(() => currentCardIndex.value)

const progressPercentage = computed(() => {
  if (totalCards.value === 0) return 0
  return Math.round((reviewedCards.value / totalCards.value) * 100)
})

const sessionDuration = computed(() => {
  return (Date.now() - sessionStartTime.value) / 1000
})

// Computed accuracy
const accuracy = computed(() => {
  const total = sessionStats.value.correct + sessionStats.value.incorrect
  if (total === 0) return 0
  return (sessionStats.value.correct / total) * 100
})

// Methods
const loadDueCards = async () => {
  if (!authStore.isAuthenticated) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch(`${API_BASE}/srs/due-cards?limit=20`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      dueCards.value = data.cards || []
      
      if (dueCards.value.length > 0) {
        await startLearningSession()
      } else {
        await loadNextReviewTime()
      }
    } else {
      error.value = 'Failed to load due cards'
    }
  } catch (err) {
    error.value = 'Network error loading cards'
  } finally {
    loading.value = false
  }
}

const startLearningSession = async () => {
  try {
    const response = await fetch(`${API_BASE}/srs/session/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ session_type: 'srs_review' })
    })
    
    if (response.ok) {
      const data = await response.json()
      sessionId.value = data.session_id
      sessionStartTime.value = Date.now()
    }
  } catch (err) {
    console.warn('Failed to start learning session:', err)
  }
}

const reviewCard = async (quality: number) => {
  if (!currentCard.value) return
  
  try {
    const response = await fetch(`${API_BASE}/srs/review-card`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        card_id: currentCard.value.card_id,
        quality: quality,
        response_time_ms: Math.round(sessionDuration.value * 1000)
      })
    })
    
    if (response.ok) {
      // Update stats
      if (quality >= 3) {
        sessionStats.value.correct++
      } else {
        sessionStats.value.incorrect++
      }
      
      sessionStats.value.total++
      
      // Move to next card
      currentCardIndex.value++
      showAnswer.value = false
      
      // Check if review is complete
      if (currentCardIndex.value >= dueCards.value.length) {
        reviewComplete.value = true
        await endLearningSession()
      }
    } else {
      error.value = 'Failed to submit review'
    }
  } catch (err) {
    error.value = 'Network error submitting review'
  }
}

const endLearningSession = async () => {
  if (!sessionId.value) return
  
  try {
    await fetch(`${API_BASE}/srs/session/end`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId.value,
        questions_answered: sessionStats.value.total,
        correct_answers: sessionStats.value.correct,
        topics_covered: ['vocabulary_review'],
        words_practiced: dueCards.value.slice(0, currentCardIndex.value).map(card => card.card_id)
      })
    })
  } catch (err) {
    console.warn('Failed to end learning session:', err)
  }
}

const loadNextReviewTime = async () => {
  try {
    const response = await fetch(`${API_BASE}/srs/stats`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      const minutes = data.next_review_in_minutes
      
      if (minutes && minutes > 0) {
        if (minutes < 60) {
          nextReviewTime.value = `${minutes} minutes`
        } else {
          const hours = Math.round(minutes / 60)
          nextReviewTime.value = `${hours} hours`
        }
      } else {
        nextReviewTime.value = 'Soon'
      }
    }
  } catch (err) {
    nextReviewTime.value = 'Unknown'
  }
}

const startNewSession = () => {
  // Reset session state
  currentCardIndex.value = 0
  showAnswer.value = false
  reviewComplete.value = false
  sessionStats.value = { correct: 0, incorrect: 0, total: 0, accuracy: 0 }
  
  // Reload cards
  loadDueCards()
}

// Lifecycle hooks
onMounted(() => {
  loadDueCards()
})

onUnmounted(() => {
  // End session if user leaves page
  if (sessionId.value && !reviewComplete.value) {
    endLearningSession()
  }
})

// Update accuracy reactively using watcher
watch(() => [sessionStats.value.correct, sessionStats.value.total], () => {
  sessionStats.value.accuracy = sessionStats.value.total > 0 
    ? (sessionStats.value.correct / sessionStats.value.total) * 100 
    : 0
}, { immediate: true })
</script>