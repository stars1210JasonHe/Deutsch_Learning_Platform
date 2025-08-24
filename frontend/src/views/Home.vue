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
        
        <!-- Translate Mode Toggle (only for word mode) -->
        <div v-if="searchMode === 'word'" class="flex justify-center mb-6">
          <div class="glass-card bg-purple-500/10 border-purple-500/20 p-4 rounded-lg">
            <label class="flex items-center space-x-3 cursor-pointer">
              <input 
                v-model="translateMode" 
                type="checkbox" 
                class="sr-only"
              >
              <div 
                :class="translateMode ? 'bg-purple-600' : 'bg-gray-600'"
                class="relative inline-block w-12 h-6 transition-colors duration-200 ease-in-out rounded-full"
              >
                <div 
                  :class="translateMode ? 'translate-x-6' : 'translate-x-0'"
                  class="inline-block w-6 h-6 transition-transform duration-200 ease-in-out transform bg-white rounded-full"
                ></div>
              </div>
              <span class="text-white font-medium">
                <span class="mr-2">🌐</span>
                Translate Mode
              </span>
              <span class="text-gray-400 text-sm">
                (Auto-detect language → German)
              </span>
            </label>
          </div>
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
                :placeholder="getPlaceholderText()"
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
    
    <!-- Translation Results -->
    <div v-if="searchStore.lastTranslateResult && searchMode === 'word' && translateMode" class="max-w-5xl mx-auto">
      <div class="glass-card p-8">
        <h3 class="text-2xl font-semibold text-purple-400 mb-6 text-center">
          🌐 Translation & Analysis Results
        </h3>
        
        <!-- Translation Info -->
        <div class="mb-6 p-4 glass-card bg-purple-500/10 border-purple-500/20">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
              <span class="text-gray-300">Original:</span>
              <span class="font-medium text-white">{{ searchStore.lastTranslateResult.original_text }}</span>
            </div>
            <div class="flex items-center space-x-2 text-sm">
              <span class="text-gray-400">{{ searchStore.lastTranslateResult.detected_language_name }}</span>
              <span class="text-green-400">{{ Math.round(searchStore.lastTranslateResult.confidence * 100) }}%</span>
            </div>
          </div>
          
          <!-- Multiple Translation Options -->
          <div v-if="searchStore.lastTranslateResult.is_ambiguous && !searchStore.lastTranslateResult.selected_translation">
            <div class="text-yellow-400 mb-3">Multiple translations found:</div>
            <div class="grid gap-2">
              <button 
                v-for="option in searchStore.lastTranslateResult.german_translations" 
                :key="option.german_word"
                @click="selectTranslation(option.german_word)"
                class="p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
              >
                <div class="font-medium text-white">{{ option.german_word }}</div>
                <div class="text-sm text-gray-400">{{ option.context }} ({{ option.pos }})</div>
              </button>
            </div>
          </div>
          
          <!-- Selected Translation -->
          <div v-else-if="searchStore.lastTranslateResult.selected_translation" class="flex items-center space-x-3">
            <span class="text-gray-300">German:</span>
            <span class="font-medium text-purple-400 text-lg">{{ searchStore.lastTranslateResult.selected_translation }}</span>
          </div>
        </div>
        
        <!-- Word Results (if translation selected and found) -->
        <div v-if="searchStore.lastTranslateResult.search_results && searchStore.lastTranslateResult.search_results.results.length > 0">
          <WordResult :result="searchStore.lastTranslateResult.search_results.results[0]" />
        </div>
        
        <!-- No results found -->
        <div v-else-if="searchStore.lastTranslateResult.selected_translation && searchStore.lastTranslateResult.search_results" 
             class="text-center py-8 text-gray-400">
          <div class="text-4xl mb-4">🤷‍♂️</div>
          <div>No German word found for "{{ searchStore.lastTranslateResult.selected_translation }}" in our database</div>
        </div>
        
        <!-- Error Message -->
        <div v-if="searchStore.lastTranslateResult.error_message" 
             class="glass-card bg-red-500/10 border-red-500/20 p-4 text-red-400 text-center">
          {{ searchStore.lastTranslateResult.error_message }}
        </div>
      </div>
    </div>

    <!-- Regular Word Results -->
    <div v-if="searchStore.lastWordResult && searchMode === 'word' && !translateMode" class="max-w-5xl mx-auto">
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
const translateMode = ref(false)

const getPlaceholderText = () => {
  if (searchMode.value === 'sentence') {
    return 'e.g., I want to explore the stars'
  } else if (translateMode.value) {
    return 'e.g., hello, cat, beautiful, 你好, 猫, 美丽'
  } else {
    return 'e.g., gehen, Raumschiff, schön'
  }
}

const search = async () => {
  if (!searchQuery.value.trim()) return
  
  if (!authStore.isAuthenticated) {
    error.value = 'Please login to use search features'
    return
  }
  
  error.value = ''
  
  try {
    if (searchMode.value === 'word') {
      if (translateMode.value) {
        await searchStore.translateSearch(searchQuery.value.trim())
      } else {
        await searchStore.analyzeWord(searchQuery.value.trim())
      }
    } else {
      await searchStore.translateSentence(searchQuery.value.trim())
    }
  } catch (err: any) {
    error.value = err.message
  }
}

const selectTranslation = async (germanWord: string) => {
  error.value = ''
  
  try {
    await searchStore.selectTranslation(searchQuery.value.trim(), germanWord)
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