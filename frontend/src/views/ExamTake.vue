<template>
  <div class="space-y-8">
    <!-- Header -->
    <div v-if="exam && !loading" class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">📝 {{ exam.title }} 🚀</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        {{ exam.cefr_level }} Level • {{ exam.total_questions }} Questions
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="loading-cosmic text-4xl mb-4">🌌</div>
      <p class="text-gray-400">Loading exam from the cosmic database...</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="max-w-2xl mx-auto">
      <div class="glass-card bg-red-500/10 border-red-500/20 p-6">
        <div class="flex items-center space-x-2 text-red-400 mb-4">
          <span>⚠️</span>
          <span class="font-semibold">Error</span>
        </div>
        <p class="text-gray-300">{{ error }}</p>
        <div class="mt-4 flex justify-center space-x-4">
          <router-link to="/exams" class="btn-primary">Back to Exams</router-link>
          <button @click="loadExam" class="btn-secondary">Retry</button>
        </div>
      </div>
    </div>

    <!-- Exam Start Screen -->
    <div v-if="!loading && exam && !examStarted && !error" class="max-w-4xl mx-auto">
      <div class="glass-card p-8">
        <div class="text-center mb-8">
          <div class="text-6xl mb-4">🌟</div>
          <h2 class="text-2xl font-semibold text-cosmic mb-4">Ready to Begin?</h2>
          <p class="text-gray-400 mb-6">
            This exam contains {{ exam.total_questions }} questions and has a time limit of {{ exam.time_limit_minutes }} minutes.
          </p>
        </div>

        <!-- Exam Info -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
          <div class="card-cosmic">
            <div class="text-center">
              <div class="text-2xl mb-2">📊</div>
              <div class="font-semibold text-aurora">CEFR Level</div>
              <div class="text-lg">{{ exam.cefr_level }}</div>
            </div>
          </div>
          <div class="card-cosmic">
            <div class="text-center">
              <div class="text-2xl mb-2">⏰</div>
              <div class="font-semibold text-cosmic">Time Limit</div>
              <div class="text-lg">{{ exam.time_limit_minutes }} minutes</div>
            </div>
          </div>
        </div>

        <!-- Instructions -->
        <div class="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 mb-8">
          <h3 class="text-lg font-medium text-blue-300 mb-3">📋 Instructions</h3>
          <ul class="text-gray-300 space-y-2 text-sm">
            <li>• Answer all questions to the best of your ability</li>
            <li>• You can review and change answers before submitting</li>
            <li>• The exam will auto-submit when time runs out</li>
            <li>• Some questions may have multiple correct answers</li>
          </ul>
        </div>

        <div class="text-center">
          <button @click="startExam" class="btn-primary px-8 py-3 text-lg">
            🚀 Start Exam
          </button>
        </div>
      </div>
    </div>

    <!-- Exam Interface -->
    <div v-if="examStarted && currentQuestion && !submitted" class="max-w-4xl mx-auto">
      <!-- Progress and Timer -->
      <div class="glass-card p-4 mb-6">
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-4">
            <div class="text-sm text-gray-400">
              Question {{ currentQuestionIndex + 1 }} of {{ totalQuestions }}
            </div>
            <div class="progress-cosmic w-48">
              <div 
                class="progress-fill" 
                :style="{ width: progressPercentage + '%' }"
              ></div>
            </div>
          </div>
          <div class="flex items-center space-x-2 text-lg font-mono">
            <span>⏰</span>
            <span :class="timeRemaining < 300 ? 'text-red-400' : 'text-cosmic'">
              {{ formatTime(timeRemaining) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Question -->
      <div class="glass-card p-8">
        <div class="mb-6">
          <div class="flex justify-between items-start mb-4">
            <div>
              <span class="text-sm text-gray-400">{{ currentQuestion.difficulty?.toUpperCase() }}</span>
              <span class="text-cosmic ml-2">{{ currentQuestion.points }} pts</span>
            </div>
          </div>
          <h3 class="text-xl font-semibold text-white mb-4">{{ currentQuestion.prompt }}</h3>
        </div>

        <!-- Question Content by Type -->
        <div class="mb-8">
          <!-- MCQ Questions -->
          <div v-if="currentQuestion.type === 'mcq'" class="space-y-3">
            <div 
              v-for="(option, index) in currentQuestion.content.options" 
              :key="index"
              class="cursor-pointer"
              @click="selectMCQOption(index)"
            >
              <div class="border border-gray-600 rounded-lg p-4 transition-all"
                   :class="selectedAnswers[currentQuestion.id]?.includes(index) 
                     ? 'bg-cosmic/20 border-cosmic' 
                     : 'hover:border-gray-500 hover:bg-gray-700/20'"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-6 h-6 border-2 border-gray-500 rounded-full flex items-center justify-center"
                       :class="selectedAnswers[currentQuestion.id]?.includes(index) 
                         ? 'bg-cosmic border-cosmic' 
                         : ''"
                  >
                    <div v-if="selectedAnswers[currentQuestion.id]?.includes(index)" 
                         class="w-2 h-2 bg-white rounded-full">
                    </div>
                  </div>
                  <span class="text-gray-200">{{ option }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Cloze Questions -->
          <div v-if="currentQuestion.type === 'cloze'" class="space-y-4">
            <div class="text-lg leading-relaxed" v-html="renderClozeText()"></div>
          </div>

          <!-- Matching Questions -->
          <div v-if="currentQuestion.type === 'matching'" class="grid md:grid-cols-2 gap-6">
            <div>
              <h4 class="text-cosmic font-medium mb-3">Match Items</h4>
              <div class="space-y-2">
                <div 
                  v-for="(item, index) in currentQuestion.content.pairs" 
                  :key="'left-' + index"
                  class="border border-gray-600 rounded p-3 cursor-pointer transition-all"
                  :class="selectedMatching?.left === index ? 'bg-cosmic/20 border-cosmic' : 'hover:border-gray-500'"
                  @click="selectMatchingItem('left', index)"
                >
                  {{ item.left }}
                </div>
              </div>
            </div>
            <div>
              <h4 class="text-aurora font-medium mb-3">With Items</h4>
              <div class="space-y-2">
                <div 
                  v-for="(item, index) in shuffledRightItems" 
                  :key="'right-' + index"
                  class="border border-gray-600 rounded p-3 cursor-pointer transition-all"
                  :class="selectedMatching?.right === item.originalIndex ? 'bg-aurora/20 border-aurora' : 'hover:border-gray-500'"
                  @click="selectMatchingItem('right', item.originalIndex)"
                >
                  {{ item.text }}
                </div>
              </div>
            </div>
          </div>

          <!-- Writing Questions -->
          <div v-if="currentQuestion.type === 'writing'">
            <textarea
              v-model="selectedAnswers[currentQuestion.id]"
              class="w-full h-32 bg-gray-800/50 border border-gray-600 rounded-lg p-4 text-white resize-none"
              :placeholder="currentQuestion.content.placeholder || 'Write your answer here...'"
            ></textarea>
            <div class="text-sm text-gray-400 mt-2">
              {{ (selectedAnswers[currentQuestion.id] || '').length }} characters
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="flex justify-between">
          <button 
            @click="previousQuestion" 
            :disabled="currentQuestionIndex === 0"
            class="btn-secondary"
            :class="currentQuestionIndex === 0 ? 'opacity-50 cursor-not-allowed' : ''"
          >
            ← Previous
          </button>

          <div class="flex space-x-4">
            <button v-if="currentQuestionIndex < totalQuestions - 1" 
                    @click="nextQuestion" 
                    class="btn-primary">
              Next →
            </button>
            <button v-else @click="showSubmitConfirmation = true" class="btn-primary bg-green-600 hover:bg-green-700">
              🎯 Submit Exam
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Submit Confirmation Modal -->
    <div v-if="showSubmitConfirmation" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="glass-card p-8 max-w-md mx-4">
        <div class="text-center mb-6">
          <div class="text-4xl mb-4">🎯</div>
          <h3 class="text-xl font-semibold text-cosmic mb-2">Submit Exam?</h3>
          <p class="text-gray-400">
            Are you sure you want to submit your exam? This action cannot be undone.
          </p>
        </div>

        <div class="bg-blue-500/10 border border-blue-500/20 rounded p-4 mb-6">
          <div class="text-sm text-blue-300">
            <div>Answered: {{ answeredQuestions }} / {{ totalQuestions }}</div>
            <div>Time remaining: {{ formatTime(timeRemaining) }}</div>
          </div>
        </div>

        <div class="flex space-x-4">
          <button @click="showSubmitConfirmation = false" class="btn-secondary flex-1">
            Cancel
          </button>
          <button @click="submitExam" class="btn-primary flex-1" :disabled="submitting">
            {{ submitting ? 'Submitting...' : 'Submit' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Exam Submitted -->
    <div v-if="submitted" class="text-center py-12">
      <div class="glass-card p-8 max-w-2xl mx-auto">
        <div class="text-6xl mb-6">🎉</div>
        <h2 class="text-2xl font-semibold text-cosmic mb-4">Exam Submitted!</h2>
        <p class="text-gray-400 mb-6">
          Your answers have been submitted and are being graded. Results will be available shortly.
        </p>
        <div class="flex justify-center space-x-4">
          <router-link v-if="attemptId" :to="`/exam/${examId}/results/${attemptId}`" class="btn-primary">
            View Results
          </router-link>
          <router-link to="/exams" class="btn-secondary">
            Back to Exams
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

interface ExamQuestion {
  id: number
  type: 'mcq' | 'cloze' | 'matching' | 'writing' | 'reorder'
  prompt: string
  content: any
  points: number
  difficulty: string
}

interface ExamSection {
  id: number
  title: string
  questions: ExamQuestion[]
}

interface Exam {
  id: number
  title: string
  cefr_level: string
  total_questions: number
  time_limit_minutes: number
  sections: ExamSection[]
}

// Reactive data
const loading = ref(true)
const error = ref('')
const exam = ref<Exam | null>(null)
const examStarted = ref(false)
const currentQuestionIndex = ref(0)
const selectedAnswers = ref<Record<number, any>>({})
const attemptId = ref<number | null>(null)
const timeRemaining = ref(0)
const timer = ref<number | null>(null)
const showSubmitConfirmation = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const selectedMatching = ref<{ left: number | null, right: number | null }>({ left: null, right: null })
const shuffledRightItems = ref<Array<{ text: string, originalIndex: number }>>([])

const API_BASE = 'http://localhost:8000'
const examId = route.params.id as string

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authStore.token}`,
  'Content-Type': 'application/json'
})

// Computed properties
const allQuestions = computed(() => {
  if (!exam.value) return []
  return exam.value.sections.flatMap(section => section.questions)
})

const currentQuestion = computed(() => allQuestions.value[currentQuestionIndex.value] || null)
const totalQuestions = computed(() => allQuestions.value.length)

const progressPercentage = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round(((currentQuestionIndex.value + 1) / totalQuestions.value) * 100)
})

const answeredQuestions = computed(() => {
  return Object.keys(selectedAnswers.value).length
})

// Methods
const loadExam = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`${API_BASE}/exam/${examId}`, {
      headers: getAuthHeaders()
    })

    if (response.ok) {
      exam.value = await response.json()
    } else {
      error.value = 'Failed to load exam'
    }
  } catch (err) {
    error.value = 'Network error loading exam'
  } finally {
    loading.value = false
  }
}

const startExam = async () => {
  try {
    const response = await fetch(`${API_BASE}/exam/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ exam_id: parseInt(examId) })
    })

    if (response.ok) {
      const data = await response.json()
      attemptId.value = data.attempt_id
      examStarted.value = true
      timeRemaining.value = (exam.value?.time_limit_minutes || 30) * 60
      startTimer()
    } else {
      error.value = 'Failed to start exam'
    }
  } catch (err) {
    error.value = 'Network error starting exam'
  }
}

const startTimer = () => {
  timer.value = setInterval(() => {
    timeRemaining.value--
    if (timeRemaining.value <= 0) {
      autoSubmitExam()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const selectMCQOption = (optionIndex: number) => {
  const questionId = currentQuestion.value?.id
  if (!questionId) return

  if (!selectedAnswers.value[questionId]) {
    selectedAnswers.value[questionId] = []
  }

  const answers = selectedAnswers.value[questionId]
  const index = answers.indexOf(optionIndex)
  
  if (index > -1) {
    answers.splice(index, 1)
  } else {
    answers.push(optionIndex)
  }
}

const renderClozeText = () => {
  if (!currentQuestion.value?.content?.text) return ''
  
  let text = currentQuestion.value.content.text
  const blanks = currentQuestion.value.content.blanks || []
  
  blanks.forEach((blank: any, index: number) => {
    const questionId = currentQuestion.value?.id
    const value = selectedAnswers.value[questionId]?.[blank.id] || ''
    
    text = text.replace(
      `[${blank.id}]`,
      `<input type="text" value="${value}" onchange="updateClozeAnswer('${blank.id}', this.value)" class="inline-block w-32 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white text-center mx-1" />`
    )
  })
  
  return text
}

const updateClozeAnswer = (blankId: string, value: string) => {
  const questionId = currentQuestion.value?.id
  if (!questionId) return

  if (!selectedAnswers.value[questionId]) {
    selectedAnswers.value[questionId] = {}
  }
  
  selectedAnswers.value[questionId][blankId] = value
}

const selectMatchingItem = (side: 'left' | 'right', index: number) => {
  selectedMatching.value[side] = index

  if (selectedMatching.value.left !== null && selectedMatching.value.right !== null) {
    const questionId = currentQuestion.value?.id
    if (!questionId) return

    if (!selectedAnswers.value[questionId]) {
      selectedAnswers.value[questionId] = {}
    }

    selectedAnswers.value[questionId][selectedMatching.value.left] = selectedMatching.value.right
    selectedMatching.value = { left: null, right: null }
  }
}

const initializeMatchingQuestion = () => {
  if (currentQuestion.value?.type === 'matching' && currentQuestion.value?.content?.pairs) {
    const rightItems = currentQuestion.value.content.pairs.map((pair: any, index: number) => ({
      text: pair.right,
      originalIndex: index
    }))
    
    // Shuffle right items
    shuffledRightItems.value = rightItems.sort(() => Math.random() - 0.5)
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < totalQuestions.value - 1) {
    currentQuestionIndex.value++
    if (currentQuestion.value?.type === 'matching') {
      initializeMatchingQuestion()
    }
  }
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    if (currentQuestion.value?.type === 'matching') {
      initializeMatchingQuestion()
    }
  }
}

const submitExam = async () => {
  submitting.value = true
  showSubmitConfirmation.value = false
  
  try {
    // Submit all answers
    for (const [questionId, answer] of Object.entries(selectedAnswers.value)) {
      await fetch(`${API_BASE}/exam/submit-answer`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          attempt_id: attemptId.value,
          question_id: parseInt(questionId),
          answer: answer,
          time_taken_seconds: 30 // Placeholder
        })
      })
    }

    // Complete the exam
    const response = await fetch(`${API_BASE}/exam/complete`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ attempt_id: attemptId.value })
    })

    if (response.ok) {
      stopTimer()
      submitted.value = true
    } else {
      error.value = 'Failed to submit exam'
    }
  } catch (err) {
    error.value = 'Network error submitting exam'
  } finally {
    submitting.value = false
  }
}

const autoSubmitExam = () => {
  if (!submitted.value) {
    submitExam()
  }
}

// Global function for cloze inputs
(window as any).updateClozeAnswer = updateClozeAnswer

// Lifecycle hooks
onMounted(() => {
  loadExam()
})

onBeforeUnmount(() => {
  stopTimer()
})
</script>
