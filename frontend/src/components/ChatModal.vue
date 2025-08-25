<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 h-5/6 flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <h2 class="text-xl font-bold text-gray-900">💬 Chat about: {{ word }}</h2>
          <span class="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            {{ messagesCount }}/{{ maxRounds }} rounds
          </span>
        </div>
        <div class="flex items-center space-x-2">
          <button
            @click="downloadChat"
            class="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            title="Download conversation"
          >
            📥
          </button>
          <button
            @click="copyChat"
            class="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
            title="Copy conversation"
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

      <!-- Chat Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Welcome Message -->
        <div v-if="messages.length === 0" class="text-center text-gray-500 py-8">
          <div class="text-4xl mb-4">🤖</div>
          <p class="text-lg font-medium">Ask me anything about "{{ word }}"!</p>
          <p class="text-sm text-gray-400 mt-2">
            I can help explain grammar, usage, synonyms, examples, and more.
          </p>
          
          <!-- Quick Tips -->
          <div class="mt-6">
            <p class="text-sm text-gray-600 mb-3">Quick tips to get started:</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-w-4xl mx-auto">
              <button
                @click="sendQuickTip('Explain ' + word + ' in simple terms')"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm transition-colors"
              >
                <span>📖</span>
                <span>Simple Explanation</span>
              </button>
              <button
                @click="sendQuickTip('Give 3 example sentences for ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg text-sm transition-colors"
              >
                <span>📝</span>
                <span>3 Examples</span>
              </button>
              <button
                @click="sendQuickTip('Show synonyms and antonyms of ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg text-sm transition-colors"
              >
                <span>🔍</span>
                <span>Synonyms & Antonyms</span>
              </button>
              <button
                @click="sendQuickTip('Create a mnemonic for remembering ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-yellow-50 hover:bg-yellow-100 text-yellow-700 rounded-lg text-sm transition-colors"
              >
                <span>🧠</span>
                <span>Memory Aid</span>
              </button>
              <button
                v-if="isVerb"
                @click="sendQuickTip('Show conjugations for ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg text-sm transition-colors"
              >
                <span>🔄</span>
                <span>Conjugations</span>
              </button>
              <button
                v-if="isVerbOrPreposition"
                @click="sendQuickTip('What case does ' + word + ' take?')"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-orange-50 hover:bg-orange-100 text-orange-700 rounded-lg text-sm transition-colors"
              >
                <span>📐</span>
                <span>Grammar Cases</span>
              </button>
              <button
                @click="sendQuickTip('Show pronunciation guide and IPA for ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-pink-50 hover:bg-pink-100 text-pink-700 rounded-lg text-sm transition-colors"
              >
                <span>🗣️</span>
                <span>Pronunciation</span>
              </button>
              <button
                @click="sendQuickTip('Write a short dialogue using ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-sm transition-colors"
              >
                <span>💬</span>
                <span>Dialogue</span>
              </button>
              <button
                @click="sendQuickTip('Make a 5-item quiz for ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg text-sm transition-colors"
              >
                <span>🎯</span>
                <span>Quiz Me</span>
              </button>
              <button
                @click="sendQuickTip('Show common phrases and collocations with ' + word)"
                class="flex items-center justify-center space-x-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg text-sm transition-colors"
              >
                <span>🔗</span>
                <span>Common Phrases</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Chat Messages -->
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-3xl px-4 py-2 rounded-lg"
            :class="message.role === 'user' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900'"
          >
            <!-- Structured Response -->
            <div v-if="message.role === 'assistant' && message.structured" class="space-y-3">
              <div v-if="message.structured.answer" class="whitespace-pre-wrap">{{ message.structured.answer }}</div>
              
              <div v-if="message.structured.examples && message.structured.examples.length" class="space-y-1">
                <div class="font-medium text-sm text-gray-600">Examples:</div>
                <div v-for="(example, idx) in message.structured.examples" :key="idx" 
                     class="pl-3 border-l-2 border-gray-300 text-sm italic">
                  {{ example }}
                </div>
              </div>
              
              <div v-if="message.structured.mini_practice" class="bg-blue-50 p-2 rounded text-sm">
                <div class="font-medium text-blue-700 mb-1">Practice:</div>
                <div class="whitespace-pre-wrap">{{ message.structured.mini_practice }}</div>
              </div>
              
              <div v-if="message.structured.tips && message.structured.tips.length" class="space-y-1">
                <div class="font-medium text-sm text-gray-600">Tips:</div>
                <div v-for="(tip, idx) in message.structured.tips" :key="idx" class="text-sm flex items-start space-x-1">
                  <span class="text-yellow-500">💡</span>
                  <span>{{ tip }}</span>
                </div>
              </div>
            </div>
            
            <!-- Regular Response -->
            <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
            
            <div class="text-xs opacity-70 mt-1">
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
        </div>

        <!-- Loading Message -->
        <div v-if="isLoading" class="flex justify-start">
          <div class="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
            <div class="flex items-center space-x-2">
              <div class="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span>Thinking...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex space-x-2">
          <textarea
            v-model="newMessage"
            @keydown.enter.prevent="sendMessage"
            @keydown.shift.enter="addNewline"
            :disabled="isLoading || messagesCount >= maxRounds"
            placeholder="Ask me about this word... (Press Enter to send, Shift+Enter for new line)"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            rows="2"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!newMessage.trim() || isLoading || messagesCount >= maxRounds"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
        <div v-if="messagesCount >= maxRounds" class="text-center text-red-600 text-sm mt-2">
          Chat limit reached. Download or copy the conversation to save it.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import axios from 'axios'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  structured?: {
    answer?: string
    examples?: string[]
    mini_practice?: string
    tips?: string[]
  }
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

// Chat state
const messages = ref<ChatMessage[]>([])
const newMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()

// Use settings store for max rounds
const maxRounds = computed(() => settingsStore.chatMaxRounds)

// Computed
const messagesCount = computed(() => {
  return Math.ceil(messages.value.filter(m => m.role === 'user').length)
})

const isVerb = computed(() => {
  return props.wordData?.pos === 'verb' || props.wordData?.pos === 'v'
})

const isVerbOrPreposition = computed(() => {
  const pos = props.wordData?.pos?.toLowerCase()
  return pos === 'verb' || pos === 'v' || pos === 'preposition' || pos === 'prep'
})

// Methods
const sendQuickTip = async (tipMessage: string) => {
  if (isLoading.value || messagesCount.value >= maxRounds.value) {
    return
  }

  newMessage.value = tipMessage
  await sendMessage()
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || isLoading.value || messagesCount.value >= maxRounds.value) {
    return
  }

  const userMessage: ChatMessage = {
    role: 'user',
    content: newMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const messageText = newMessage.value.trim()
  newMessage.value = ''

  await scrollToBottom()

  isLoading.value = true

  try {
    const response = await axios.post('/api/chat/word', {
      word: props.word,
      word_data: props.wordData,
      message: messageText,
      chat_history: messages.value.slice(0, -1) // Exclude the current message
    })

    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: response.data.response,
      timestamp: new Date(),
      structured: response.data.structured
    }

    messages.value.push(assistantMessage)
    await scrollToBottom()

  } catch (error) {
    console.error('Chat error:', error)
    const errorMessage: ChatMessage = {
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
      timestamp: new Date()
    }
    messages.value.push(errorMessage)
    await scrollToBottom()
  } finally {
    isLoading.value = false
  }
}

const addNewline = () => {
  newMessage.value += '\n'
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const copyChat = async () => {
  const chatText = messages.value.map(m => 
    `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`
  ).join('\n\n')

  const fullText = `Chat about: ${props.word}\n${'='.repeat(40)}\n\n${chatText}`

  try {
    await navigator.clipboard.writeText(fullText)
    // Could add a toast notification here
  } catch (error) {
    console.error('Failed to copy chat:', error)
  }
}

const downloadChat = () => {
  const chatData = {
    word: props.word,
    wordData: props.wordData,
    messages: messages.value,
    exportedAt: new Date().toISOString()
  }

  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${props.word}-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const closeModal = () => {
  emit('close')
}

// Load settings
onMounted(() => {
  settingsStore.loadSettings()
})
</script>