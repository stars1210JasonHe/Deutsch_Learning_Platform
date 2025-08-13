<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <!-- Word Not Found - Show Suggestions -->
    <div v-if="result.found === false" class="text-center">
      <div class="text-6xl mb-4">🤔</div>
      <h2 class="text-2xl font-bold text-gray-900 mb-4">{{ result.original }}</h2>
      <p class="text-gray-600 mb-6">{{ result.message || "Word not found" }}</p>
      
      <div v-if="result.suggestions && result.suggestions.length > 0" class="space-y-4">
        <h3 class="text-lg font-semibold text-gray-700">Did you mean one of these?</h3>
        <div class="grid gap-3">
          <button
            v-for="(suggestion, index) in result.suggestions"
            :key="suggestion.word"
            @click="selectSuggestion(suggestion.word)"
            class="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
            :disabled="isLoading"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-gray-900">{{ suggestion.word }}</span>
                <span class="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {{ suggestion.pos }}
                </span>
              </div>
              <span class="text-sm text-gray-500">{{ suggestion.meaning }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Word Found - Show Analysis -->
    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-bold text-gray-900">{{ result.original }}</h2>
        <div class="flex space-x-2">
          <span 
            v-if="result.cached" 
            class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full"
          >
            Cached
          </span>
          <span 
            v-if="result.source" 
            class="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full"
          >
            {{ result.source }}
          </span>
        </div>
      </div>
    
      <div class="space-y-6">
      <!-- Part of Speech & Basic Info -->
      <div v-if="result.pos || result.article">
        <div class="flex flex-wrap gap-4">
          <span v-if="result.pos" class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
            {{ result.pos }}
          </span>
          <span v-if="result.article" class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
            {{ result.article }}
          </span>
          <span v-if="result.plural" class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm">
            Plural: {{ result.plural }}
          </span>
        </div>
      </div>
      
      <!-- Translations -->
      <div class="grid md:grid-cols-2 gap-6">
        <div v-if="result.translations_en.length">
          <h3 class="font-semibold text-gray-700 mb-2">English</h3>
          <ul class="space-y-1">
            <li v-for="translation in result.translations_en" :key="translation" 
                class="text-gray-600">
              • {{ translation }}
            </li>
          </ul>
        </div>
        
        <div v-if="result.translations_zh.length">
          <h3 class="font-semibold text-gray-700 mb-2">中文</h3>
          <ul class="space-y-1">
            <li v-for="translation in result.translations_zh" :key="translation" 
                class="text-gray-600">
              • {{ translation }}
            </li>
          </ul>
        </div>
      </div>
      
      <!-- Conjugation Tables (for verbs) -->
      <div v-if="result.tables && result.pos === 'verb'" class="space-y-4">
        <h3 class="font-semibold text-gray-700">Conjugation</h3>
        
        <div class="grid md:grid-cols-2 gap-4">
          <div v-if="result.tables.praesens" class="border rounded-lg p-4">
            <h4 class="font-medium text-gray-600 mb-2">Präsens</h4>
            <div class="space-y-1 text-sm">
              <div v-for="(form, person) in result.tables.praesens" :key="person">
                <span class="text-gray-500">{{ person }}:</span> 
                <span class="ml-2 font-medium">{{ form }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="result.tables.praeteritum" class="border rounded-lg p-4">
            <h4 class="font-medium text-gray-600 mb-2">Präteritum</h4>
            <div class="space-y-1 text-sm">
              <div v-for="(form, person) in result.tables.praeteritum" :key="person">
                <span class="text-gray-500">{{ person }}:</span> 
                <span class="ml-2 font-medium">{{ form }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Example Sentence -->
      <div v-if="result.example" class="bg-gray-50 rounded-lg p-4">
        <h3 class="font-semibold text-gray-700 mb-3">Example</h3>
        <div class="space-y-2">
          <p class="text-gray-800"><strong>DE:</strong> {{ result.example.de }}</p>
          <p class="text-gray-600"><strong>EN:</strong> {{ result.example.en }}</p>
          <p v-if="result.example.zh" class="text-gray-600"><strong>ZH:</strong> {{ result.example.zh }}</p>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSearchStore } from '@/stores/search'

const searchStore = useSearchStore()
const { isLoading, selectSuggestedWord } = searchStore

const selectSuggestion = async (word: string) => {
  try {
    await selectSuggestedWord(word)
  } catch (error: any) {
    console.error('Failed to select suggestion:', error)
  }
}
interface WordAnalysis {
  original: string
  found?: boolean
  pos?: string
  article?: string
  plural?: string
  tables?: any
  translations_en: string[]
  translations_zh: string[]
  example?: {
    de: string
    en: string
    zh: string
  }
  cached: boolean
  source?: string
  suggestions?: Array<{
    word: string
    pos: string
    meaning: string
  }>
  message?: string
}

defineProps<{
  result: WordAnalysis
}>()
</script>