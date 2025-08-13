<template>
  <div class="space-y-8">
    <!-- Header -->
    <div v-if="results && !loading" class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">🎯 {{ results.exam_title }} Results 📊</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        Your cosmic learning performance analysis
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="loading-cosmic text-4xl mb-4">🌌</div>
      <p class="text-gray-400">Loading your results from the cosmic database...</p>
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
          <button @click="loadResults" class="btn-secondary">Retry</button>
        </div>
      </div>
    </div>

    <!-- Results Content -->
    <div v-if="results && !loading && !error" class="space-y-8">
      <!-- Score Overview -->
      <div class="glass-card p-8 max-w-4xl mx-auto">
        <div class="text-center mb-8">
          <div class="text-8xl mb-4">
            {{ results.percentage_score >= 80 ? '🏆' : results.percentage_score >= 60 ? '🌟' : '💪' }}
          </div>
          <h2 class="text-3xl font-bold mb-2" 
              :class="results.percentage_score >= 80 ? 'text-green-400' : 
                     results.percentage_score >= 60 ? 'text-aurora' : 'text-orange-400'">
            {{ Math.round(results.percentage_score) }}%
          </h2>
          <p class="text-gray-400">
            {{ getPerformanceMessage(results.percentage_score) }}
          </p>
        </div>

        <!-- Score Breakdown -->
        <div class="grid md:grid-cols-4 gap-6 mb-8">
          <div class="card-cosmic text-center">
            <div class="text-2xl mb-2">📝</div>
            <div class="text-2xl font-bold text-cosmic">{{ Math.round(results.total_points) }}</div>
            <div class="text-sm text-gray-400">Points Earned</div>
          </div>
          <div class="card-cosmic text-center">
            <div class="text-2xl mb-2">🎯</div>
            <div class="text-2xl font-bold text-aurora">{{ Math.round(results.max_points) }}</div>
            <div class="text-sm text-gray-400">Max Points</div>
          </div>
          <div class="card-cosmic text-center">
            <div class="text-2xl mb-2">📊</div>
            <div class="text-2xl font-bold text-green-400">{{ Math.round(results.percentage_score) }}%</div>
            <div class="text-sm text-gray-400">Score</div>
          </div>
          <div class="card-cosmic text-center">
            <div class="text-2xl mb-2">⏱️</div>
            <div class="text-2xl font-bold text-purple-400">{{ formatTime(results.time_taken_seconds) }}</div>
            <div class="text-sm text-gray-400">Time</div>
          </div>
        </div>

        <!-- Progress Ring -->
        <div class="text-center mb-8">
          <div class="relative inline-block">
            <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50" cy="50" r="40"
                stroke="rgba(107, 114, 128, 0.3)" stroke-width="8"
                fill="none"
              />
              <circle
                cx="50" cy="50" r="40"
                stroke="url(#cosmic-gradient)" stroke-width="8"
                fill="none"
                stroke-dasharray="251.2"
                :stroke-dashoffset="251.2 - (251.2 * results.percentage_score / 100)"
                stroke-linecap="round"
                class="transition-all duration-1000"
              />
              <defs>
                <linearGradient id="cosmic-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#8B5CF6" />
                  <stop offset="50%" style="stop-color:#EC4899" />
                  <stop offset="100%" style="stop-color:#00C9DB" />
                </linearGradient>
              </defs>
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-2xl font-bold text-white">{{ Math.round(results.percentage_score) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Section Performance -->
      <div v-if="results.section_scores && results.section_scores.length > 1" class="glass-card p-8 max-w-4xl mx-auto">
        <h3 class="text-2xl font-semibold text-cosmic mb-6">📊 Section Performance</h3>
        <div class="space-y-4">
          <div 
            v-for="section in results.section_scores" 
            :key="section.section_id"
            class="border border-gray-600 rounded-lg p-4"
          >
            <div class="flex justify-between items-center mb-2">
              <h4 class="font-medium text-aurora">{{ section.section_title }}</h4>
              <span class="text-sm text-gray-400">
                {{ section.correct }} / {{ section.total }}
              </span>
            </div>
            <div class="progress-cosmic">
              <div 
                class="progress-fill" 
                :style="{ width: (section.correct / section.total * 100) + '%' }"
              ></div>
            </div>
            <div class="text-sm text-gray-400 mt-1">
              {{ Math.round(section.correct / section.total * 100) }}% accuracy
            </div>
          </div>
        </div>
      </div>

      <!-- Question Analysis -->
      <div v-if="results.results && results.results.length > 0" class="glass-card p-8 max-w-4xl mx-auto">
        <h3 class="text-2xl font-semibold text-cosmic mb-6">🔍 Question Analysis</h3>
        
        <div class="space-y-6">
          <div 
            v-for="(question, index) in results.results" 
            :key="question.question_id"
            class="border rounded-lg p-4"
            :class="question.is_correct ? 'border-green-500/40 bg-green-500/5' : 'border-red-500/40 bg-red-500/5'"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center space-x-2">
                <span class="text-2xl">{{ question.is_correct ? '✅' : '❌' }}</span>
                <span class="text-sm text-gray-400">Question {{ index + 1 }}</span>
                <span class="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                  {{ question.question_type.toUpperCase() }}
                </span>
              </div>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-400">{{ question.max_points }} pts</span>
                <span class="text-sm" :class="question.is_correct ? 'text-green-400' : 'text-red-400'">
                  +{{ question.points_earned || 0 }}
                </span>
              </div>
            </div>

            <div class="mb-3">
              <p class="text-gray-200 font-medium">{{ question.prompt }}</p>
            </div>

            <div class="space-y-2">
              <div class="text-sm">
                <span class="text-gray-400">Your answer:</span>
                <span class="ml-2 text-white">{{ formatAnswer(question.user_answer) }}</span>
              </div>
              <div v-if="!question.is_correct" class="text-sm">
                <span class="text-gray-400">Correct answer:</span>
                <span class="ml-2 text-green-400">{{ formatAnswer(question.correct_answer) }}</span>
              </div>
              <div v-if="question.explanation" class="text-sm text-blue-300 bg-blue-500/10 rounded p-2">
                <span class="font-medium">💡 Explanation:</span>
                <span class="ml-2">{{ question.explanation }}</span>
              </div>
              <div v-if="question.feedback" class="text-sm text-purple-300 bg-purple-500/10 rounded p-2">
                <span class="font-medium">📝 Feedback:</span>
                <span class="ml-2">{{ question.feedback }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Study Recommendations -->
      <div class="glass-card p-8 max-w-4xl mx-auto">
        <h3 class="text-2xl font-semibold text-cosmic mb-6">📚 Study Recommendations</h3>
        
        <div class="grid md:grid-cols-2 gap-6">
          <!-- Strengths -->
          <div class="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
            <h4 class="font-medium text-green-400 mb-3 flex items-center">
              <span class="text-xl mr-2">💪</span>
              Strengths
            </h4>
            <ul class="text-sm text-gray-300 space-y-1">
              <li v-for="strength in getStrengths(results)" :key="strength">
                • {{ strength }}
              </li>
            </ul>
          </div>

          <!-- Areas for Improvement -->
          <div class="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4">
            <h4 class="font-medium text-orange-400 mb-3 flex items-center">
              <span class="text-xl mr-2">🎯</span>
              Focus Areas
            </h4>
            <ul class="text-sm text-gray-300 space-y-1">
              <li v-for="area in getImprovementAreas(results)" :key="area">
                • {{ area }}
              </li>
            </ul>
          </div>
        </div>

        <div class="mt-6 text-center">
          <p class="text-gray-400 mb-4">Ready to continue your German learning journey?</p>
          <div class="flex justify-center space-x-4">
            <router-link to="/srs" class="btn-primary">
              🧠 Review Vocabulary
            </router-link>
            <router-link to="/exams" class="btn-secondary">
              📝 Take Another Exam
            </router-link>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <div class="flex justify-center space-x-4">
        <router-link to="/exams" class="btn-primary">
          ← Back to Exams
        </router-link>
        <router-link to="/dashboard" class="btn-secondary">
          📊 View Dashboard
        </router-link>
        <router-link to="/" class="btn-secondary">
          🏠 Home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

interface QuestionResult {
  question_id: number
  question_type: string
  prompt: string
  user_answer: any
  correct_answer: any
  is_correct: boolean
  points: number
  max_points?: number
  points_earned?: number
  difficulty: string
  explanation?: string
  feedback?: string
  target_words?: string[]
}

interface SectionScore {
  section_id: number
  section_title: string
  correct: number
  total: number
}

interface ExamResults {
  exam_title: string
  level: string
  percentage_score: number
  total_points: number
  max_points: number
  time_taken_seconds: number
  completed_at: string
  results?: QuestionResult[]
  section_scores?: SectionScore[]
}

// Reactive data
const loading = ref(true)
const error = ref('')
const results = ref<ExamResults | null>(null)

const API_BASE = 'http://localhost:8000'
const examId = route.params.id as string
const attemptId = route.params.attemptId as string

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authStore.token}`,
  'Content-Type': 'application/json'
})

// Methods
const loadResults = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`${API_BASE}/exam/attempt/${attemptId}/results`, {
      headers: getAuthHeaders()
    })

    if (response.ok) {
      results.value = await response.json()
    } else {
      error.value = 'Failed to load exam results'
    }
  } catch (err) {
    error.value = 'Network error loading results'
  } finally {
    loading.value = false
  }
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatAnswer = (answer: any) => {
  if (Array.isArray(answer)) {
    return answer.join(', ')
  }
  if (typeof answer === 'object') {
    return Object.values(answer).join(', ')
  }
  return String(answer)
}

const getPerformanceMessage = (score: number) => {
  if (score >= 90) return 'Outstanding performance! You\'re mastering German! 🏆'
  if (score >= 80) return 'Excellent work! You\'re doing great! 🌟'
  if (score >= 70) return 'Good job! Keep up the steady progress! 👍'
  if (score >= 60) return 'Not bad! There\'s room for improvement! 📚'
  if (score >= 50) return 'Keep practicing! You\'ll get there! 💪'
  return 'Don\'t give up! Every expert was once a beginner! 🚀'
}

const getStrengths = (results: ExamResults) => {
  const strengths = []
  
  if (results.percentage_score >= 80) {
    strengths.push('Excellent overall performance')
  }
  
  // Analyze by question type if available
  if (results.results) {
    const typeStats = results.results.reduce((acc: any, q) => {
      if (!acc[q.question_type]) acc[q.question_type] = { correct: 0, total: 0 }
      acc[q.question_type].total++
      if (q.is_correct) acc[q.question_type].correct++
      return acc
    }, {})

    Object.entries(typeStats).forEach(([type, stats]: [string, any]) => {
      const accuracy = stats.correct / stats.total
      if (accuracy >= 0.8) {
        strengths.push(`Strong ${type.toUpperCase()} question performance`)
      }
    })
  }
  
  if (results.time_taken_seconds < 1800) { // Less than 30 minutes
    strengths.push('Efficient time management')
  }
  
  if (strengths.length === 0) {
    strengths.push('Completed the full exam')
  }
  
  return strengths
}

const getImprovementAreas = (results: ExamResults) => {
  const areas = []
  
  if (results.percentage_score < 70) {
    areas.push('Overall accuracy needs improvement')
  }
  
  // Analyze by question type if available
  if (results.results) {
    const typeStats = results.results.reduce((acc: any, q) => {
      if (!acc[q.question_type]) acc[q.question_type] = { correct: 0, total: 0 }
      acc[q.question_type].total++
      if (q.is_correct) acc[q.question_type].correct++
      return acc
    }, {})

    Object.entries(typeStats).forEach(([type, stats]: [string, any]) => {
      const accuracy = stats.correct / stats.total
      if (accuracy < 0.6) {
        areas.push(`Focus on ${type.toUpperCase()} question types`)
      }
    })
  }
  
  // Skip difficulty analysis since it's not in the API response
  // if (results.results) {
  //   const difficultyStats = results.results.reduce((acc: any, q) => {
  //     if (!acc[q.difficulty]) acc[q.difficulty] = { correct: 0, total: 0 }
  //     acc[q.difficulty].total++
  //     if (q.is_correct) acc[q.difficulty].correct++
  //     return acc
  //   }, {})

  //   Object.entries(difficultyStats).forEach(([diff, stats]: [string, any]) => {
  //     const accuracy = stats.correct / stats.total
  //     if (accuracy < 0.5) {
  //       areas.push(`Practice more ${diff} level questions`)
  //     }
  //   })
  // }

  if (areas.length === 0) {
    areas.push('Keep practicing to maintain your level')
  }
  
  return areas.slice(0, 4) // Limit to 4 areas
}

// Lifecycle hooks
onMounted(() => {
  loadResults()
})
</script>
