<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        <span class="text-cosmic">🌌 Learning Dashboard 📊</span>
      </h1>
      <p class="text-xl text-gray-300 mb-8">
        Navigate your journey through the German language galaxy
      </p>
    </div>

    <!-- Quick Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="card-cosmic text-center">
        <div class="text-3xl mb-2">🧠</div>
        <div class="text-2xl font-bold text-cosmic">{{ srsStats.total_cards || 0 }}</div>
        <div class="text-sm text-gray-400">Cards in SRS</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-3xl mb-2">📝</div>
        <div class="text-2xl font-bold text-aurora">{{ examStats.total_attempts || 0 }}</div>
        <div class="text-sm text-gray-400">Exams Taken</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-3xl mb-2">⚡</div>
        <div class="text-2xl font-bold text-cosmic">{{ userProgress.average_accuracy || 0 }}%</div>
        <div class="text-sm text-gray-400">Average Accuracy</div>
      </div>
      
      <div class="card-cosmic text-center">
        <div class="text-3xl mb-2">🎯</div>
        <div class="text-2xl font-bold text-aurora">{{ userProgress.study_streak || 0 }}</div>
        <div class="text-sm text-gray-400">Day Streak</div>
      </div>
    </div>

    <!-- Progress Overview -->
    <div class="grid lg:grid-cols-2 gap-8">
      <!-- SRS Status -->
      <div class="glass-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-semibold text-cosmic">🧠 SRS Status</h2>
          <router-link to="/srs" class="btn-ghost">
            Review Cards
          </router-link>
        </div>

        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <span class="text-gray-300">Due Cards</span>
            <div class="flex items-center space-x-2">
              <span class="badge-warning">{{ srsStats.due_cards || 0 }}</span>
              <span class="text-sm text-gray-400">ready now</span>
            </div>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-gray-300">Learning Cards</span>
            <div class="flex items-center space-x-2">
              <span class="badge-info">{{ srsStats.learning_cards || 0 }}</span>
              <span class="text-sm text-gray-400">in progress</span>
            </div>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-gray-300">Mature Cards</span>
            <div class="flex items-center space-x-2">
              <span class="badge-success">{{ srsStats.mature_cards || 0 }}</span>
              <span class="text-sm text-gray-400">mastered</span>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <div class="flex justify-between text-sm text-gray-400 mb-2">
            <span>Overall Progress</span>
            <span>{{ progressPercentage }}%</span>
          </div>
          <div class="progress-cosmic">
            <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="glass-card p-6">
        <h2 class="text-2xl font-semibold text-aurora mb-6">📈 Recent Activity</h2>
        
        <div v-if="recentSessions.length === 0" class="text-center py-8 text-gray-400">
          <div class="text-4xl mb-2">🌟</div>
          <p>No recent activity. Start learning!</p>
        </div>
        
        <div v-else class="space-y-4">
          <div 
            v-for="session in recentSessions" 
            :key="session.id"
            class="flex items-center justify-between p-3 bg-white/5 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div class="text-2xl">
                {{ getSessionIcon(session.type) }}
              </div>
              <div>
                <div class="text-white font-medium">{{ formatSessionType(session.type) }}</div>
                <div class="text-sm text-gray-400">{{ formatDate(session.started_at) }}</div>
              </div>
            </div>
            
            <div class="text-right">
              <div class="text-sm text-gray-300">{{ session.accuracy_percentage || 0 }}% accuracy</div>
              <div class="text-xs text-gray-500">{{ session.questions_answered || 0 }} questions</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Learning Goals -->
    <div class="glass-card p-6 max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-semibold text-cosmic">🎯 Learning Goals</h2>
        <button @click="showGoalEditor = !showGoalEditor" class="btn-secondary text-sm">
          {{ showGoalEditor ? 'Cancel' : 'Edit Goals' }}
        </button>
      </div>

      <div v-if="showGoalEditor" class="mb-6 p-4 bg-white/5 rounded-lg">
        <div class="grid md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-300 mb-2">Daily Study Goal (minutes)</label>
            <input 
              v-model.number="goalForm.daily_minutes" 
              type="number" 
              min="5" 
              max="240"
              class="input-field w-full"
            >
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-2">Weekly Card Goal</label>
            <input 
              v-model.number="goalForm.weekly_cards" 
              type="number" 
              min="10" 
              max="500"
              class="input-field w-full"
            >
          </div>
        </div>
        <div class="flex justify-end mt-4 space-x-3">
          <button @click="showGoalEditor = false" class="btn-secondary">Cancel</button>
          <button @click="updateGoals" class="btn-primary">Save Goals</button>
        </div>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <div>
          <div class="flex justify-between text-sm text-gray-400 mb-2">
            <span>Daily Study Goal</span>
            <span>{{ dailyProgress }}%</span>
          </div>
          <div class="progress-cosmic">
            <div class="progress-fill" :style="{ width: Math.min(dailyProgress, 100) + '%' }"></div>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            {{ studyTimeToday }} / {{ userProgress.daily_goal_minutes || 15 }} minutes
          </div>
        </div>
        
        <div>
          <div class="flex justify-between text-sm text-gray-400 mb-2">
            <span>Weekly Card Goal</span>
            <span>{{ weeklyProgress }}%</span>
          </div>
          <div class="progress-cosmic">
            <div class="progress-fill" :style="{ width: Math.min(weeklyProgress, 100) + '%' }"></div>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            {{ cardsThisWeek }} / {{ userProgress.weekly_goal_cards || 50 }} cards
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="text-center">
      <h2 class="text-2xl font-semibold text-aurora mb-6">🚀 Quick Actions</h2>
      <div class="flex flex-wrap justify-center gap-4">
        <router-link to="/srs" class="btn-primary">
          🧠 Review SRS Cards
        </router-link>
        <router-link to="/exams" class="btn-primary">
          📝 Take an Exam
        </router-link>
        <router-link to="/" class="btn-secondary">
          🔍 Search Words
        </router-link>
        <router-link to="/history" class="btn-secondary">
          📚 View History
        </router-link>
      </div>
    </div>

    <!-- Error Messages -->
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const error = ref('')
const showGoalEditor = ref(false)

const srsStats = ref({
  total_cards: 0,
  due_cards: 0,
  learning_cards: 0,
  mature_cards: 0,
  accuracy_percentage: 0
})

const examStats = ref({
  total_attempts: 0,
  average_score: 0
})

const userProgress = ref({
  current_level: 'A1',
  vocabulary_size: 0,
  average_accuracy: 0,
  study_streak: 0,
  daily_goal_minutes: 15,
  weekly_goal_cards: 50
})

// Define interface for session data
interface Session {
  id: number
  type: string
  started_at: string
  accuracy_percentage?: number
  questions_answered?: number
}

const recentSessions = ref<Session[]>([])
const studyTimeToday = ref(0)
const cardsThisWeek = ref(0)

const goalForm = ref({
  daily_minutes: 15,
  weekly_cards: 50
})

const API_BASE = 'http://localhost:8000'

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${authStore.token}`,
  'Content-Type': 'application/json'
})

// Computed properties
const progressPercentage = computed(() => {
  const total = srsStats.value.total_cards
  if (total === 0) return 0
  const mature = srsStats.value.mature_cards
  return Math.round((mature / total) * 100)
})

const dailyProgress = computed(() => {
  const goal = userProgress.value.daily_goal_minutes || 15
  return Math.round((studyTimeToday.value / goal) * 100)
})

const weeklyProgress = computed(() => {
  const goal = userProgress.value.weekly_goal_cards || 50
  return Math.round((cardsThisWeek.value / goal) * 100)
})

// Methods
const loadDashboardData = async () => {
  if (!authStore.isAuthenticated) return
  
  loading.value = true
  error.value = ''
  
  try {
    // Load SRS dashboard data
    const response = await fetch(`${API_BASE}/srs/dashboard`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      srsStats.value = data.srs_stats || {}
      recentSessions.value = data.recent_sessions || []
      studyTimeToday.value = Math.round(data.weekly_study_time_hours * 60 / 7) // Rough estimate
      cardsThisWeek.value = srsStats.value.total_cards // Placeholder
      userProgress.value = { ...userProgress.value, ...data.progress }
    }
    
    // Load exam history
    const examResponse = await fetch(`${API_BASE}/exam/user/history?limit=5`, {
      headers: getAuthHeaders()
    })
    
    if (examResponse.ok) {
      const examData = await examResponse.json()
      examStats.value.total_attempts = examData.total || 0
      
      if (examData.attempts && examData.attempts.length > 0) {
        const scores = examData.attempts.map((a: any) => a.percentage_score || 0)
        examStats.value.average_score = Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length)
      }
    }
    
  } catch (err) {
    error.value = 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

const updateGoals = async () => {
  if (!authStore.isAuthenticated) return
  
  try {
    const response = await fetch(`${API_BASE}/srs/progress/update-goals`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        daily_goal_minutes: goalForm.value.daily_minutes,
        weekly_goal_cards: goalForm.value.weekly_cards
      })
    })
    
    if (response.ok) {
      userProgress.value.daily_goal_minutes = goalForm.value.daily_minutes
      userProgress.value.weekly_goal_cards = goalForm.value.weekly_cards
      showGoalEditor.value = false
    } else {
      error.value = 'Failed to update goals'
    }
  } catch (err) {
    error.value = 'Network error updating goals'
  }
}

const getSessionIcon = (type: string) => {
  const icons: { [key: string]: string } = {
    'srs_review': '🧠',
    'exam': '📝',
    'practice': '💪',
    'word_lookup': '🔍'
  }
  return icons[type] || '📚'
}

const formatSessionType = (type: string) => {
  const types: { [key: string]: string } = {
    'srs_review': 'SRS Review',
    'exam': 'Exam',
    'practice': 'Practice',
    'word_lookup': 'Word Search'
  }
  return types[type] || 'Study Session'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  return date.toLocaleDateString()
}

onMounted(() => {
  loadDashboardData()
  
  // Set up goal form with current values
  goalForm.value.daily_minutes = userProgress.value.daily_goal_minutes
  goalForm.value.weekly_cards = userProgress.value.weekly_goal_cards
})
</script>