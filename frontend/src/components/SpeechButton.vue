<template>
  <button
    @click="speak"
    :disabled="!isSupported || isSpeaking"
    :class="[
      'inline-flex items-center justify-center p-2 rounded-full transition-all duration-200',
      'hover:bg-blue-500/20 active:scale-95',
      isSupported 
        ? 'text-blue-400 hover:text-blue-300 cursor-pointer' 
        : 'text-gray-500 cursor-not-allowed opacity-50',
      isSpeaking ? 'animate-pulse bg-blue-500/30' : '',
      size === 'sm' ? 'w-8 h-8 text-sm' : size === 'lg' ? 'w-12 h-12 text-lg' : 'w-10 h-10 text-base'
    ]"
    :title="tooltip"
    type="button"
  >
    <svg 
      v-if="!isSpeaking"
      class="w-5 h-5" 
      fill="currentColor" 
      viewBox="0 0 24 24"
    >
      <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
    </svg>
    <svg 
      v-else
      class="w-5 h-5 animate-spin" 
      fill="currentColor" 
      viewBox="0 0 24 24"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
    </svg>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  text: string
  lang?: string
  rate?: number
  pitch?: number
  volume?: number
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  lang: 'de-DE',
  rate: 0.9,
  pitch: 1.0,
  volume: 1.0,
  size: 'md'
})

// Reactive state
const isSupported = ref(false)
const isSpeaking = ref(false)
const currentUtterance = ref<SpeechSynthesisUtterance | null>(null)

// Computed properties
const tooltip = computed(() => {
  if (!isSupported.value) return 'Speech not supported in this browser'
  if (isSpeaking.value) return 'Speaking...'
  return `Listen to: "${props.text}"`
})

// Speech synthesis functionality
const checkSupport = () => {
  isSupported.value = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window
}

const getPreferredVoice = (): SpeechSynthesisVoice | null => {
  const voices = speechSynthesis.getVoices()
  const lang = props.lang.toLowerCase()
  
  // Define preferred voices for each language
  const voicePreferences: Record<string, string[]> = {
    'de-de': [
      'Google Deutsch',
      'Microsoft Hedda - German (Germany)',
      'Microsoft Katja - German (Germany)', 
      'Marlene',
      'Vicki'
    ],
    'en-us': [
      'Google US English',
      'Microsoft Zira - English (United States)',
      'Microsoft David - English (United States)',
      'Alex',
      'Samantha'
    ],
    'zh-cn': [
      'Google 中文（中国大陆）',
      'Microsoft Huihui - Chinese (Simplified, PRC)',
      'Microsoft Yaoyao - Chinese (Simplified, PRC)',
      'Ting-Ting',
      'Sin-Ji'
    ]
  }
  
  const preferred = voicePreferences[lang] || []
  
  // Try preferred voices first
  for (const voiceName of preferred) {
    const voice = voices.find(v => v.name === voiceName)
    if (voice) return voice
  }
  
  // Fallback to any voice matching the language code
  const langCode = lang.split('-')[0]
  return voices.find(v => v.lang.toLowerCase().startsWith(langCode)) || null
}

const speak = async () => {
  if (!isSupported.value || isSpeaking.value || !props.text.trim()) return
  
  // Stop any current speech
  speechSynthesis.cancel()
  
  try {
    // Wait for voices to be loaded
    if (speechSynthesis.getVoices().length === 0) {
      await new Promise(resolve => {
        const checkVoices = () => {
          if (speechSynthesis.getVoices().length > 0) {
            resolve(true)
          } else {
            setTimeout(checkVoices, 100)
          }
        }
        checkVoices()
      })
    }
    
    const utterance = new SpeechSynthesisUtterance(props.text)
    currentUtterance.value = utterance
    
    // Configure utterance
    utterance.lang = props.lang
    utterance.rate = props.rate
    utterance.pitch = props.pitch
    utterance.volume = props.volume
    
    // Set preferred voice for the language
    const preferredVoice = getPreferredVoice()
    if (preferredVoice) {
      utterance.voice = preferredVoice
    }
    
    // Event listeners
    utterance.onstart = () => {
      isSpeaking.value = true
    }
    
    utterance.onend = () => {
      isSpeaking.value = false
      currentUtterance.value = null
    }
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error)
      isSpeaking.value = false
      currentUtterance.value = null
    }
    
    // Speak the text
    speechSynthesis.speak(utterance)
    
  } catch (error) {
    console.error('Error starting speech synthesis:', error)
    isSpeaking.value = false
    currentUtterance.value = null
  }
}

const stopSpeaking = () => {
  if (isSpeaking.value) {
    speechSynthesis.cancel()
    isSpeaking.value = false
    currentUtterance.value = null
  }
}

// Lifecycle hooks
onMounted(() => {
  checkSupport()
  
  // Handle voices loaded event
  if (isSupported.value) {
    speechSynthesis.onvoiceschanged = () => {
      // Voices are now available
    }
  }
})

onBeforeUnmount(() => {
  stopSpeaking()
})

// Expose methods for parent components
defineExpose({
  speak,
  stopSpeaking,
  isSupported,
  isSpeaking
})
</script>