<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-5/6 flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <h2 class="text-xl font-bold text-gray-900">🎨 Image for: {{ word }}</h2>
          <select
            v-model="selectedModel"
            class="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="dall-e-2">DALL-E 2 (Fast)</option>
            <option value="dall-e-3">DALL-E 3 (Quality)</option>
          </select>
          <select
            v-model="selectedSize"
            class="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option 
              v-for="option in settingsStore.validSizeOptions" 
              :key="option.value" 
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <button
            v-if="generatedImage"
            @click="downloadImage"
            class="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            title="Download image"
          >
            📥
          </button>
          <button
            v-if="generatedImage"
            @click="copyImageUrl"
            class="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            title="Copy image"
          >
            📋
          </button>
          <button
            @click="closeModal"
            class="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- No Image State -->
        <div v-if="!generatedImage && !isGenerating" class="text-center py-12">
          <div class="text-6xl mb-4">🎨</div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Generate Educational Image</h3>
          <p class="text-gray-600 mb-6">
            Create a cartoon-style educational image to help learn "{{ word }}"
          </p>
          
          <!-- Style Options -->
          <div class="bg-gray-50 rounded-lg p-4 mb-6 max-w-md mx-auto">
            <h4 class="font-medium text-gray-900 mb-3">Image Style</h4>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="imageStyle"
                  value="educational"
                  class="mr-2"
                />
                <span class="text-sm">Educational/Dictionary style</span>
              </label>
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="imageStyle"
                  value="cartoon"
                  class="mr-2"
                />
                <span class="text-sm">Cartoon/Illustrative</span>
              </label>
              <label class="flex items-center">
                <input
                  type="radio"
                  v-model="imageStyle"
                  value="realistic"
                  class="mr-2"
                />
                <span class="text-sm">Semi-realistic</span>
              </label>
            </div>
          </div>

          <button
            @click="generateImage"
            :disabled="isGenerating"
            class="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Generate Image
          </button>
        </div>

        <!-- Generating State -->
        <div v-if="isGenerating" class="text-center py-12">
          <div class="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Creating...</h3>
          <p class="text-gray-600">
            Generating your educational image for "{{ word }}"
          </p>
          <div class="mt-4 text-sm text-gray-500">
            This may take 10-30 seconds
          </div>
        </div>

        <!-- Generated Image -->
        <div v-if="generatedImage && !isGenerating" class="text-center">
          <!-- Word and meaning display above image -->
          <div class="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
            <h3 class="text-2xl font-bold text-gray-900 mb-2">{{ word }}</h3>
            <div class="text-lg text-gray-700" v-if="wordData?.gloss_en || wordData?.translations_en">
              <span class="italic">
                {{ wordData?.gloss_en || wordData?.translations_en?.[0] }}
              </span>
            </div>
            <div class="text-sm text-gray-500 mt-1" v-if="wordData?.pos || wordData?.upos">
              {{ wordData?.pos || wordData?.upos }}
            </div>
          </div>
          
          <div class="mb-4">
            <img
              :src="generatedImage.url"
              :alt="`Generated image for ${word}`"
              class="max-w-full max-h-96 rounded-lg shadow-lg mx-auto"
              @load="onImageLoad"
            />
          </div>
          
          <div class="text-sm text-gray-600 mb-4">
            <div><strong>Prompt:</strong> {{ generatedImage.prompt }}</div>
            <div><strong>Model:</strong> {{ generatedImage.model }}</div>
            <div><strong>Size:</strong> {{ generatedImage.size }}</div>
          </div>

          <div class="flex justify-center space-x-3">
            <button
              @click="regenerateImage"
              class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              🔄 Regenerate
            </button>
            <button
              @click="clearImage"
              class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        <!-- Error State -->
        <div v-if="error" class="text-center py-12">
          <div class="text-6xl mb-4">⚠️</div>
          <h3 class="text-xl font-bold text-red-600 mb-2">Generation Failed</h3>
          <p class="text-gray-600 mb-6">{{ error }}</p>
          <button
            @click="clearError"
            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import axios from 'axios'

interface GeneratedImage {
  url: string
  prompt: string
  model: string
  size: string
  timestamp: Date
}

const props = defineProps<{
  word: string
  wordData: any
}>()

const emit = defineEmits<{
  close: []
}>()

// Settings store
const settingsStore = useSettingsStore()

// Image generation state
const generatedImage = ref<GeneratedImage | null>(null)
const isGenerating = ref(false)
const error = ref('')

// Use settings store for default values
const selectedModel = computed({
  get: () => settingsStore.imageDefaultModel,
  set: (value) => settingsStore.updateImageModel(value)
})

const selectedSize = computed({
  get: () => settingsStore.imageDefaultSize,
  set: (value) => settingsStore.updateImageSize(value)
})

const imageStyle = computed({
  get: () => settingsStore.imageDefaultStyle,
  set: (value) => settingsStore.updateImageStyle(value)
})

// Methods
const generateImage = async () => {
  if (isGenerating.value) return

  isGenerating.value = true
  error.value = ''

  try {
    const response = await axios.post('/api/images/generate', {
      word: props.word,
      word_data: props.wordData,
      model: selectedModel.value,
      size: selectedSize.value,
      style: imageStyle.value
    })

    generatedImage.value = {
      url: response.data.image_url,
      prompt: response.data.prompt,
      model: selectedModel.value,
      size: selectedSize.value,
      timestamp: new Date()
    }

  } catch (err: any) {
    console.error('Image generation error:', err)
    error.value = err.message || 'Failed to generate image. Please try again.'
  } finally {
    isGenerating.value = false
  }
}

const regenerateImage = () => {
  generateImage()
}

const clearImage = () => {
  generatedImage.value = null
  error.value = ''
}

const clearError = () => {
  error.value = ''
}

const downloadImage = async () => {
  if (!generatedImage.value) return

  try {
    const response = await fetch(generatedImage.value.url)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.word}-${new Date().toISOString().split('T')[0]}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download image:', error)
  }
}

const copyImageUrl = async () => {
  if (!generatedImage.value) return

  try {
    await navigator.clipboard.writeText(generatedImage.value.url)
    // Could add a toast notification here
  } catch (error) {
    console.error('Failed to copy image URL:', error)
  }
}

const onImageLoad = () => {
  // Image loaded successfully
}

// Settings are now handled by the store automatically through computed properties

const closeModal = () => {
  emit('close')
}

onMounted(() => {
  settingsStore.loadSettings()
})
</script>