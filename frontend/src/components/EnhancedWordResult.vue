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
                <span class="ml-2 text-sm px-2 py-1 rounded-full"
                      :class="getPosClass(suggestion.pos)">
                  {{ getPosDisplay(suggestion.pos) }}
                </span>
              </div>
              <span class="text-sm text-gray-500">{{ suggestion.meaning }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Word Found - Clean Layout Like Screenshot -->
    <div v-else>
      <!-- Header with Word and Speech/Favorite buttons -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <h1 class="text-2xl font-bold text-gray-900">{{ result.original }}</h1>
            <SpeechButton :text="result.original" size="sm" />
            <button class="text-gray-400 hover:text-gray-600">⭐</button>
          </div>
        </div>
      </div>

      <!-- Base Form (if different from searched word) -->
      <div class="mb-4">
        <h2 class="text-xl font-semibold text-gray-800">{{ result.lemma || result.original }}</h2>
        
        <!-- POS Badge -->
        <span class="inline-block mt-1 px-2 py-1 text-sm rounded"
              :class="getPosClass(result.pos || result.upos)">
          {{ getPosDisplay(result.pos || result.upos, result.verb_props) }}
        </span>
      </div>

      <!-- Meaning Section -->
      <div class="mb-6">
        <h3 class="font-semibold text-gray-700 mb-2">Meaning</h3>
        
        <!-- English Translation -->
        <div v-if="result.translations_en && result.translations_en.length > 0" class="mb-2">
          <span class="font-medium text-gray-600">EN:</span> 
          <span class="text-gray-800">{{ result.translations_en.join(', ') }}</span>
        </div>
        
        <!-- Chinese Translation -->
        <div v-if="result.translations_zh && result.translations_zh.length > 0">
          <span class="font-medium text-gray-600">中文:</span> 
          <span class="text-gray-800">{{ result.translations_zh.join('、') }}</span>
        </div>
      </div>

      <!-- More English/Chinese Translations (if available) -->
      <div v-if="hasMoreTranslations" class="mb-6 grid md:grid-cols-2 gap-6">
        <div v-if="result.translations_en && result.translations_en.length > 1">
          <h3 class="font-semibold text-gray-700 mb-2">More English Translations</h3>
          <ul class="space-y-1">
            <li v-for="translation in result.translations_en.slice(1)" :key="translation" class="text-gray-600">
              • {{ translation }}
            </li>
          </ul>
        </div>
        
        <div v-if="result.translations_zh && result.translations_zh.length > 1">
          <h3 class="font-semibold text-gray-700 mb-2">更多中文翻译</h3>
          <ul class="space-y-1">
            <li v-for="translation in result.translations_zh.slice(1)" :key="translation" class="text-gray-600">
              • {{ translation }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Verb Properties -->
      <div v-if="result.verb_props && result.pos === 'verb'" class="mb-6">
        <h3 class="font-semibold text-gray-700 mb-3">Verb Properties</h3>
        <div class="flex flex-wrap gap-2">
          <span v-if="result.verb_props.separable" class="bg-orange-100 text-orange-800 px-3 py-1 rounded text-sm font-medium">
            Separable
          </span>
          <span v-if="result.verb_props.reflexive" class="bg-teal-100 text-teal-800 px-3 py-1 rounded text-sm font-medium">
            Reflexive
          </span>
          <span v-if="result.verb_props.aux" class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded text-sm font-medium">
            {{ result.verb_props.aux }} (auxiliary)
          </span>
          <span v-if="result.verb_props.regularity" class="bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm font-medium">
            {{ result.verb_props.regularity }}
          </span>
          <span v-if="result.verb_props.partizip_ii" class="bg-green-100 text-green-800 px-3 py-1 rounded text-sm font-medium">
            {{ result.verb_props.partizip_ii }}
          </span>
        </div>
      </div>

      <!-- Conjugation Tables (for verbs) - Matching Screenshot Layout -->
      <div v-if="result.tables && (result.pos === 'verb' || result.upos === 'VERB')" class="space-y-4">
        <h3 class="font-semibold text-gray-700">Conjugation</h3>
        
        <!-- Three main tenses in a row like the screenshot -->
        <div class="grid md:grid-cols-3 gap-4">
          <!-- Präsens (Present) -->
          <div v-if="result.tables.praesens" class="border rounded-lg p-4 bg-blue-50 border-blue-200">
            <h4 class="font-medium text-blue-800 mb-3">Präsens (Present)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.praesens.ich" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ich</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.ich }}</span>
              </div>
              <div v-if="result.tables.praesens.du" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">du</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.du }}</span>
              </div>
              <div v-if="result.tables.praesens.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">er/sie/es</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.praesens.wir" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">wir</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.wir }}</span>
              </div>
              <div v-if="result.tables.praesens.ihr" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ihr</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.ihr }}</span>
              </div>
              <div v-if="result.tables.praesens.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">sie/Sie</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.sie_Sie }}</span>
              </div>
            </div>
          </div>
          
          <!-- Präteritum (Simple Past) -->
          <div v-if="result.tables.praeteritum" class="border rounded-lg p-4 bg-green-50 border-green-200">
            <h4 class="font-medium text-green-800 mb-3">Präteritum (Simple Past)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.praeteritum.ich" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ich</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.ich }}</span>
              </div>
              <div v-if="result.tables.praeteritum.du" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">du</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.du }}</span>
              </div>
              <div v-if="result.tables.praeteritum.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">er/sie/es</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.praeteritum.wir" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">wir</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.wir }}</span>
              </div>
              <div v-if="result.tables.praeteritum.ihr" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ihr</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.ihr }}</span>
              </div>
              <div v-if="result.tables.praeteritum.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">sie/Sie</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Perfekt (Present Perfect) -->
          <div v-if="result.tables.perfekt" class="border rounded-lg p-4 bg-purple-50 border-purple-200">
            <h4 class="font-medium text-purple-800 mb-3">Perfekt (Present Perfect)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.perfekt.ich" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ich</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.ich }}</span>
              </div>
              <div v-if="result.tables.perfekt.du" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">du</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.du }}</span>
              </div>
              <div v-if="result.tables.perfekt.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">er/sie/es</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.perfekt.wir" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">wir</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.wir }}</span>
              </div>
              <div v-if="result.tables.perfekt.ihr" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">ihr</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.ihr }}</span>
              </div>
              <div v-if="result.tables.perfekt.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-16 font-medium">sie/Sie</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.sie_Sie }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Example Section -->
      <div v-if="result.example" class="mt-6 bg-gray-50 rounded-lg p-4">
        <h3 class="font-semibold text-gray-700 mb-3">Example</h3>
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <p class="text-gray-800"><strong>DE:</strong> {{ result.example.de }}</p>
            <SpeechButton :text="result.example.de" size="sm" />
          </div>
          <div class="flex items-center space-x-2">
            <p class="text-gray-600"><strong>EN:</strong> {{ result.example.en }}</p>
            <SpeechButton v-if="result.example.en" :text="result.example.en" size="sm" lang="en-US" />
          </div>
          <div v-if="result.example.zh" class="flex items-center space-x-2">
            <p class="text-gray-600"><strong>ZH:</strong> {{ result.example.zh }}</p>
            <SpeechButton :text="result.example.zh" size="sm" lang="zh-CN" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import { usePartOfSpeech } from '@/composables/usePartOfSpeech'
import SpeechButton from './SpeechButton.vue'

const props = defineProps<{
  result: WordAnalysis
}>()

const searchStore = useSearchStore()
const { isLoading, selectSuggestedWord } = searchStore

// Part of Speech utilities
const { getPosDisplay, getPosClass, isVerbType } = usePartOfSpeech()

// Helper computed properties
const hasMoreTranslations = computed(() => {
  return (props.result.translations_en && props.result.translations_en.length > 1) ||
         (props.result.translations_zh && props.result.translations_zh.length > 1)
})

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
  upos?: string
  lemma?: string
  cefr?: string
  
  // Meanings
  gloss_en?: string
  gloss_zh?: string
  translations_en?: string[]
  translations_zh?: string[]
  
  // Conjugation tables
  tables?: {
    praesens?: any
    praeteritum?: any
    perfekt?: any
    imperativ?: any
  }
  
  // Verb properties
  verb_props?: {
    separable?: boolean
    reflexive?: boolean
    aux?: string
    regularity?: string
    partizip_ii?: string
    cases?: string[]
    preps?: string[]
  }
  
  // Examples
  example?: {
    de: string
    en: string
    zh: string
  }
  
  // Meta
  cached?: boolean
  source?: string
  suggestions?: Array<{
    word: string
    pos: string
    meaning: string
  }>
  message?: string
}
</script>