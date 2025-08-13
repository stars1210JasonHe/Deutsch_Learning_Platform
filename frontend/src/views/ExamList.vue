<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">🌟 Exam Central 📝</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        Test your German skills with AI-powered exams across the galaxy
      </p>
    </div>

    <!-- Exam Generator -->
    <div class="glass-card p-8 max-w-4xl mx-auto">
      <div class="text-center mb-6">
        <h2 class="text-2xl font-semibold text-aurora mb-2">🚀 Generate New Exam</h2>
        <p class="text-gray-400">Create a personalized exam tailored to your learning level</p>
      </div>

      <div class="grid md:grid-cols-2 gap-6 mb-6">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            📊 CEFR Level
          </label>
          <select v-model="examForm.level" class="input-field w-full">
            <option value="A1">A1 - Beginner</option>
            <option value="A2">A2 - Elementary</option>
            <option value="B1">B1 - Intermediate</option>
            <option value="B2">B2 - Upper Intermediate</option>
            <option value="C1">C1 - Advanced</option>
            <option value="C2">C2 - Mastery</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            📝 Number of Questions
          </label>
          <select v-model="examForm.questionCount" class="input-field w-full">
            <option :value="5">5 Questions (Quick)</option>
            <option :value="10">10 Questions (Standard)</option>
            <option :value="15">15 Questions (Extended)</option>
            <option :value="20">20 Questions (Comprehensive)</option>
          </select>
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-3">
          🎯 Question Types
        </label>
        <div class="flex flex-wrap gap-3">
          <label class="flex items-center space-x-2 cursor-pointer">
            <input 
              type="checkbox" 
              v-model="examForm.questionTypes" 
              value="mcq" 
              class="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
            >
            <span class="text-gray-300">Multiple Choice</span>
          </label>
          <label class="flex items-center space-x-2 cursor-pointer">
            <input 
              type="checkbox" 
              v-model="examForm.questionTypes" 
              value="cloze" 
              class="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
            >
            <span class="text-gray-300">Fill in the Blank</span>
          </label>
          <label class="flex items-center space-x-2 cursor-pointer">
            <input 
              type="checkbox" 
              v-model="examForm.questionTypes" 
              value="matching" 
              class="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
            >
            <span class="text-gray-300">Matching</span>
          </label>
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-2">
          🏷️ Exam Title (Optional)
        </label>
        <input 
          v-model="examForm.title"
          type="text" 
          placeholder="My German Practice Exam"
          class="input-field w-full"
        >
      </div>

      <div class="text-center">
        <button 
          @click="generateExam" 
          :disabled="isGenerating || examForm.questionTypes.length === 0"
          class="btn-primary px-8 py-3 text-lg"
        >
          <span v-if="isGenerating" class="flex items-center space-x-2">
            <span class="loading-cosmic">🌌</span>
            <span>Generating Exam...</span>
          </span>
          <span v-else class="flex items-center space-x-2">
            <span>✨</span>
            <span>Generate Exam</span>
          </span>
        </button>
      </div>
    </div>

    <!-- Available Exams -->
    <div class="max-w-6xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-semibold text-cosmic">📚 Available Exams</h2>
        <button @click="loadExams" class="btn-secondary">
          🔄 Refresh
        </button>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="loading-cosmic text-4xl mb-4">🌌</div>
        <p class="text-gray-400">Loading exams from the cosmos...</p>
      </div>

      <div v-else-if="exams.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">🌟</div>
        <p class="text-gray-400">No exams available yet. Generate your first exam above!</p>
      </div>

      <div v-else class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="exam in exams" 
          :key="exam.id"
          class="card-cosmic"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center space-x-2">
              <span class="badge-info">{{ exam.level }}</span>
              <span class="text-sm text-gray-400">{{ exam.total_questions }} questions</span>
            </div>
            <div class="text-sm text-gray-500">
              {{ formatDate(exam.created_at) }}
            </div>
          </div>

          <h3 class="text-xl font-semibold text-white mb-3">{{ exam.title }}</h3>
          <p class="text-gray-400 mb-4 text-sm">{{ exam.description }}</p>

          <div class="flex flex-wrap gap-2 mb-4">
            <span 
              v-for="topic in exam.topics" 
              :key="topic"
              class="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full text-xs"
            >
              {{ topic }}
            </span>
          </div>

          <div class="flex justify-between items-center">
            <div class="text-sm text-gray-400">
              ⏱️ {{ exam.time_limit_minutes || 30 }} minutes
            </div>
            <button 
              @click="startExam(exam.id)" 
              class="btn-primary px-4 py-2 text-sm"
            >
              🚀 Start Exam
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="max-w-2xl mx-auto">
      <div class="glass-card bg-red-500/10 border-red-500/20 p-4">
        <div class="flex items-center space-x-2 text-red-400">
          <span>⚠️</span>
          <span>{{ error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

interface Exam {
  id: number
  title: string
  description: string
  level: string
  topics: string[]
  total_questions: number
  time_limit_minutes: number
  created_at: string
}

const router = useRouter()
const authStore = useAuthStore()

const exams = ref<Exam[]>([])
const loading = ref(false)
const isGenerating = ref(false)
const error = ref('')

const examForm = ref({
  level: 'A1',
  questionCount: 10,
  questionTypes: ['mcq', 'cloze'],
  title: ''
})

const API_BASE = 'http://localhost:8000'

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authStore.token}`,
  'Content-Type': 'application/json'
})

const loadExams = async () => {
  if (!authStore.isAuthenticated) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch(`${API_BASE}/exam/list`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      exams.value = data.exams || []
    } else {
      error.value = 'Failed to load exams'
    }
  } catch (err) {
    error.value = 'Network error loading exams'
  } finally {
    loading.value = false
  }
}

const generateExam = async () => {
  if (!authStore.isAuthenticated) return
  
  isGenerating.value = true
  error.value = ''
  
  try {
    const response = await fetch(`${API_BASE}/exam/generate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        title: examForm.value.title || `${examForm.value.level} Practice Exam`,
        level: examForm.value.level,
        question_types: examForm.value.questionTypes,
        question_count: examForm.value.questionCount
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // Reload exams to show the new one
        await loadExams()
        
        // Reset form
        examForm.value.title = ''
        
        // Show success message
        error.value = ''
      } else {
        error.value = 'Failed to generate exam'
      }
    } else {
      error.value = 'Error generating exam'
    }
  } catch (err) {
    error.value = 'Network error generating exam'
  } finally {
    isGenerating.value = false
  }
}

const startExam = (examId: number) => {
  router.push(`/exam/${examId}`)
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}

onMounted(() => {
  loadExams()
})
</script>