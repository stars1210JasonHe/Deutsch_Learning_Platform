import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface WordChoice {
  lemma_id: number
  lemma: string
  pos: string
  display_name: string
  pos_display: string
  translations_en: string[]
  translations_zh: string[]
  preview: string
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
  // Multiple choice fields
  multiple_choices?: boolean
  choices?: WordChoice[]
  choice_count?: number
  original_query?: string
}

interface SentenceTranslation {
  original: string
  german: string
  gloss: Array<{
    de: string
    en: string
    zh: string
    note?: string
  }>
  cached: boolean
}

interface TranslationOption {
  german_word: string
  context: string
  pos: string
}

interface TranslateSearchResult {
  original_text: string
  detected_language: string
  detected_language_name: string
  confidence: number
  german_translations: TranslationOption[]
  is_ambiguous: boolean
  search_results?: {
    results: any[]
    total: number
    cached: boolean
  }
  selected_translation?: string
  error_message?: string
}

interface SearchHistoryItem {
  id: number
  query_text: string
  query_type: string
  timestamp: string
}

export const useSearchStore = defineStore('search', () => {
  const isLoading = ref(false)
  const lastWordResult = ref<WordAnalysis | null>(null)
  const lastSentenceResult = ref<SentenceTranslation | null>(null)
  const lastTranslateResult = ref<TranslateSearchResult | null>(null)
  const searchHistory = ref<SearchHistoryItem[]>([])
  
  const analyzeWord = async (word: string) => {
    isLoading.value = true
    try {
      // Use direct word lookup endpoint that creates missing words via OpenAI
      const response = await axios.get(`/api/words/${encodeURIComponent(word)}`)
      lastWordResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Word analysis failed:', error)
      throw new Error(error.response?.data?.detail || 'Analysis failed')
    } finally {
      isLoading.value = false
    }
  }
  
  const translateSentence = async (sentence: string) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/translate/sentence', { input: sentence })
      lastSentenceResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Sentence translation failed:', error)
      throw new Error(error.response?.data?.detail || 'Translation failed')
    } finally {
      isLoading.value = false
    }
  }
  
  const getSearchHistory = async () => {
    try {
      const response = await axios.get('/api/search/history')
      searchHistory.value = response.data.items
      return response.data
    } catch (error: any) {
      console.error('Failed to load search history:', error)
      throw new Error('Failed to load search history')
    }
  }
  
  const deleteHistoryItem = async (id: number) => {
    try {
      await axios.delete(`/api/search/history/${id}`)
      searchHistory.value = searchHistory.value.filter(item => item.id !== id)
    } catch (error: any) {
      console.error('Failed to delete history item:', error)
      throw new Error('Failed to delete history item')
    }
  }
  
  const selectSuggestedWord = async (word: string) => {
    isLoading.value = true
    try {
      // Use direct word lookup endpoint that creates missing words via OpenAI
      const response = await axios.get(`/api/words/${encodeURIComponent(word)}`)
      lastWordResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Word selection failed:', error)
      throw new Error(error.response?.data?.detail || 'Selection failed')
    } finally {
      isLoading.value = false
    }
  }

  const selectWordChoice = async (lemmaId: number, originalQuery: string) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/translate/word/choice', { 
        lemma_id: lemmaId,
        original_query: originalQuery
      })
      lastWordResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Word choice selection failed:', error)
      throw new Error(error.response?.data?.detail || 'Selection failed')
    } finally {
      isLoading.value = false
    }
  }
  
  const translateSearch = async (text: string) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/words/translate-search', { 
        text: text,
        translate_mode: true
      })
      lastTranslateResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Translate search failed:', error)
      throw new Error(error.response?.data?.detail || 'Translate search failed')
    } finally {
      isLoading.value = false
    }
  }
  
  const selectTranslation = async (originalText: string, selectedGermanWord: string) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/words/translate-search-select', {
        original_text: originalText,
        selected_german_word: selectedGermanWord
      })
      lastTranslateResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Translation selection failed:', error)
      throw new Error(error.response?.data?.detail || 'Translation selection failed')
    } finally {
      isLoading.value = false
    }
  }
  
  const selectLanguageChoice = async (originalText: string, languageCode: string, action: string) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/words/translate-language-select', {
        original_text: originalText,
        selected_language: languageCode,
        selected_action: action
      })
      lastTranslateResult.value = response.data
      return response.data
    } catch (error: any) {
      console.error('Language choice selection failed:', error)
      throw new Error(error.response?.data?.detail || 'Language choice selection failed')
    } finally {
      isLoading.value = false
    }
  }
  
  return {
    isLoading,
    lastWordResult,
    lastSentenceResult,
    lastTranslateResult,
    searchHistory,
    analyzeWord,
    translateSentence,
    getSearchHistory,
    deleteHistoryItem,
    selectSuggestedWord,
    selectWordChoice,
    translateSearch,
    selectTranslation,
    selectLanguageChoice
  }
})