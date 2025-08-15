<template>
  <div id="app" class="min-h-screen space-bg">
    <!-- Floating Stars Background -->
    <div class="stars" v-if="showStars">
      <div
        v-for="star in stars"
        :key="star.id"
        class="star"
        :style="{
          left: star.x + '%',
          top: star.y + '%',
          width: star.size + 'px',
          height: star.size + 'px',
          animationDelay: star.delay + 's'
        }"
      ></div>
    </div>

    <!-- Navigation -->
    <nav class="glass-nav sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <RouterLink to="/" class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                <span class="text-white font-bold text-lg">🚀</span>
              </div>
              <h1 class="text-2xl font-bold text-cosmic">Vibe Deutsch</h1>
            </RouterLink>
          </div>
          
          <div class="flex items-center space-x-6">
            <!-- Navigation Links for Authenticated Users -->
            <div v-if="authStore.isAuthenticated" class="hidden md:flex items-center space-x-6">
              <RouterLink to="/" class="nav-link">
                🏠 Home
              </RouterLink>
              <RouterLink to="/favorites" class="nav-link">
                ⭐ Favorites
              </RouterLink>
              <RouterLink to="/exams" class="nav-link">
                📝 Exams
              </RouterLink>
              <RouterLink to="/srs" class="nav-link">
                🧠 SRS
              </RouterLink>
              <RouterLink to="/dashboard" class="nav-link">
                📊 Dashboard
              </RouterLink>
              <RouterLink to="/history" class="nav-link">
                📚 History
              </RouterLink>
            </div>

            <!-- Auth Buttons -->
            <div class="flex items-center space-x-3">
              <RouterLink 
                v-if="!authStore.isAuthenticated"
                to="/login" 
                class="btn-secondary"
              >
                Login
              </RouterLink>
              <RouterLink 
                v-if="!authStore.isAuthenticated"
                to="/register" 
                class="btn-primary"
              >
                Register
              </RouterLink>
              
              <div v-if="authStore.isAuthenticated" class="flex items-center space-x-3">
                <div class="text-sm text-gray-300">
                  Welcome back! ✨
                </div>
                <button @click="logout" class="btn-secondary">
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Mobile Menu (if needed) -->
    <div v-if="authStore.isAuthenticated" class="md:hidden glass-card mx-4 mt-4 p-4">
      <div class="flex justify-center space-x-4 text-sm">
        <RouterLink to="/" class="nav-link">🏠</RouterLink>
        <RouterLink to="/favorites" class="nav-link">⭐</RouterLink>
        <RouterLink to="/exams" class="nav-link">📝</RouterLink>
        <RouterLink to="/srs" class="nav-link">🧠</RouterLink>
        <RouterLink to="/dashboard" class="nav-link">📊</RouterLink>
        <RouterLink to="/history" class="nav-link">📚</RouterLink>
      </div>
    </div>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="mt-16 border-t border-white/10 bg-black/20">
      <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 text-center">
        <p class="text-gray-400 text-sm">
          Made with 💫 and ☕ for German learners exploring the universe of language
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const showStars = ref(true)
const stars = ref<Array<{
  id: number
  x: number
  y: number
  size: number
  delay: number
}>>([])

// Generate random stars for background
const generateStars = () => {
  const starArray = []
  for (let i = 0; i < 50; i++) {
    starArray.push({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 2
    })
  }
  stars.value = starArray
}

onMounted(() => {
  generateStars()
})

const logout = () => {
  authStore.logout()
}
</script>