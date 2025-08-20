<template>
  <div class="space-y-12">
    <!-- Hero Section -->
    <div class="text-center py-12">
      <div class="mb-8">
        <h1 class="text-6xl font-bold mb-6">
          <span class="text-cosmic">Welcome to the Universe</span>
        </h1>
        <h2 class="text-4xl font-semibold text-aurora mb-4">
          of German Learning 🌌
        </h2>
      </div>
      <p class="text-xl text-gray-300 mb-8 max-w-2xl mx-auto leading-relaxed">
        Journey through space with AI-powered learning, featuring intelligent caching, 
        spaced repetition, and personalized progress tracking across the cosmos of German language.
      </p>
      
      <!-- Quick Stats -->
      <div class="flex justify-center space-x-8 mt-8">
        <div class="text-center">
          <div class="text-2xl font-bold text-cosmic">10,000+</div>
          <div class="text-sm text-gray-400">Words Cached</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-aurora">∞</div>
          <div class="text-sm text-gray-400">Learning Potential</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-cosmic">🚀</div>
          <div class="text-sm text-gray-400">Speed of Light</div>
        </div>
      </div>
    </div>
    
    <!-- Search Interface -->
    <div class="max-w-3xl mx-auto">
      <div class="glass-card p-8">
        <div class="text-center mb-6">
          <h3 class="text-2xl font-semibold text-white mb-2">Mission Control 🎯</h3>
          <p class="text-gray-400">Choose your learning mission and explore the German galaxy</p>
        </div>
        
        <div class="flex flex-wrap justify-center gap-4 mb-8">
          <button 
            @click="searchMode = 'word'" 
            :class="searchMode === 'word' ? 'btn-primary' : 'btn-secondary'"
            class="flex items-center space-x-2"
          >
            <span>🔍</span>
            <span>Word Analysis</span>
          </button>
          <button 
            @click="searchMode = 'sentence'" 
            :class="searchMode === 'sentence' ? 'btn-primary' : 'btn-secondary'"
            class="flex items-center space-x-2"
          >
            <span>🌍</span>
            <span>Sentence Translation</span>
          </button>
        </div>
        
        <div class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-3">
              {{ searchMode === 'word' ? '🚀 Launch Word Explorer:' : '🌌 Navigate Sentence Space:' }}
            </label>
            <div class="flex space-x-3">
              <input 
                v-model="searchQuery"
                type="text" 
                :placeholder="searchMode === 'word' ? 'e.g., gehen, Raumschiff, 宇宙' : 'e.g., I want to explore the stars'"
                class="input-field flex-1 text-lg"
                @keyup.enter="search"
              >
              <button 
                @click="search" 
                :disabled="!searchQuery.trim() || searchStore.isLoading"
                class="btn-primary min-w-[120px] flex items-center justify-center space-x-2"
              >
                <span v-if="searchStore.isLoading" class="loading-cosmic">🔄</span>
                <span v-else class="flex items-center space-x-1">
                  <span>🚀</span>
                  <span>Launch</span>
                </span>
              </button>
            </div>
          </div>
          
          <div v-if="error" class="glass-card bg-red-500/10 border-red-500/20 p-4">
            <div class="flex items-center space-x-2 text-red-400">
              <span>⚠️</span>
              <span>{{ error }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Results -->
    <div v-if="searchStore.lastWordResult && searchMode === 'word'" class="max-w-5xl mx-auto">
      <div class="glass-card p-8">
        <!-- Multiple Choice Selector -->
        <div v-if="searchStore.lastWordResult.multiple_choices" class="mb-6">
          <MultipleChoiceSelector 
            :choices="searchStore.lastWordResult.choices || []"
            :message="searchStore.lastWordResult.message || 'Multiple meanings found'"
            :original-query="searchStore.lastWordResult.original_query || searchStore.lastWordResult.original"
            @choice-selected="handleChoiceSelected"
          />
        </div>
        
        <!-- Regular Word Result -->
        <div v-else>
          <h3 class="text-2xl font-semibold text-cosmic mb-6 text-center">
            🔍 Word Analysis Results
          </h3>
          <WordResult :result="searchStore.lastWordResult" />
        </div>
      </div>
    </div>
    
    <div v-if="searchStore.lastSentenceResult && searchMode === 'sentence'" class="max-w-5xl mx-auto">
      <div class="glass-card p-8">
        <h3 class="text-2xl font-semibold text-aurora mb-6 text-center">
          🌍 Translation Mission Complete
        </h3>
        <SentenceResult :result="searchStore.lastSentenceResult" />
      </div>
    </div>
    
    <!-- Features Preview -->
    <div v-if="!searchStore.lastWordResult && !searchStore.lastSentenceResult" class="max-w-7xl mx-auto">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-cosmic mb-4">Explore Our Galaxy of Features 🌌</h3>
        <p class="text-gray-400">Discover the tools that will accelerate your German learning journey</p>
      </div>
      
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">🔍</div>
          <h3 class="text-xl font-semibold mb-3 text-cosmic">Smart Word Analysis</h3>
          <p class="text-gray-400 leading-relaxed">
            Advanced AI analysis with conjugation tables, translations, and contextual examples for any German word
          </p>
        </div>
        
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">⚡</div>
          <h3 class="text-xl font-semibold mb-3 text-aurora">Lightning Cache System</h3>
          <p class="text-gray-400 leading-relaxed">
            Instant responses for previously searched terms with our intelligent caching technology
          </p>
        </div>
        
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">🧠</div>
          <h3 class="text-xl font-semibold mb-3 text-cosmic">Spaced Repetition</h3>
          <p class="text-gray-400 leading-relaxed">
            Scientific learning algorithm that optimizes memory retention and long-term mastery
          </p>
        </div>
        
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">📝</div>
          <h3 class="text-xl font-semibold mb-3 text-aurora">AI Exam Generator</h3>
          <p class="text-gray-400 leading-relaxed">
            Dynamic exams with auto-grading, detailed feedback, and CEFR-aligned difficulty levels
          </p>
        </div>
        
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">📊</div>
          <h3 class="text-xl font-semibold mb-3 text-cosmic">Progress Analytics</h3>
          <p class="text-gray-400 leading-relaxed">
            Detailed insights into your learning journey with personalized recommendations
          </p>
        </div>
        
        <div class="card-cosmic text-center">
          <div class="text-4xl mb-4">🌟</div>
          <h3 class="text-xl font-semibold mb-3 text-aurora">Cosmic Experience</h3>
          <p class="text-gray-400 leading-relaxed">
            Beautiful, intuitive interface that makes learning German an interstellar adventure
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSearchStore, type WordChoice } from '@/stores/search'
import { useAuthStore } from '@/stores/auth'
import WordResult from '@/components/WordResult.vue'
import SentenceResult from '@/components/SentenceResult.vue'
import MultipleChoiceSelector from '@/components/MultipleChoiceSelector.vue'

const searchStore = useSearchStore()
const authStore = useAuthStore()

const searchMode = ref<'word' | 'sentence'>('word')
const searchQuery = ref('')
const error = ref('')

const search = async () => {
  if (!searchQuery.value.trim()) return
  
  if (!authStore.isAuthenticated) {
    error.value = 'Please login to use search features'
    return
  }
  
  error.value = ''
  
  try {
    if (searchMode.value === 'word') {
      await searchStore.analyzeWord(searchQuery.value.trim())
    } else {
      await searchStore.translateSentence(searchQuery.value.trim())
    }
  } catch (err: any) {
    error.value = err.message
  }
}

const handleChoiceSelected = async (choice: WordChoice) => {
  error.value = ''
  
  try {
    await searchStore.selectWordChoice(choice.lemma_id, choice.lemma)
  } catch (err: any) {
    error.value = err.message
  }
}
</script>