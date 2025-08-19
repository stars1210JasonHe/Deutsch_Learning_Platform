<template>
  <div class="max-w-md mx-auto">
    <div class="bg-white rounded-lg shadow-md p-8">
      <h2 class="text-2xl font-bold text-center text-gray-900 mb-6">Register</h2>
      
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Username</label>
          <input 
            v-model="username"
            type="text" 
            required
            class="input-field w-full"
            placeholder="Choose a username"
          >
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
          <input 
            v-model="email"
            type="email" 
            required
            class="input-field w-full"
            placeholder="Enter your email"
          >
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
          <input 
            v-model="password"
            type="password" 
            required
            class="input-field w-full"
            placeholder="Choose a password (min 6 characters)"
            minlength="6"
          >
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
          <input 
            v-model="confirmPassword"
            type="password" 
            required
            class="input-field w-full"
            placeholder="Confirm your password"
          >
        </div>
        
        <div v-if="error" class="text-red-600 text-sm">
          {{ error }}
        </div>
        
        <button 
          type="submit" 
          :disabled="isLoading"
          class="btn-primary w-full"
        >
          <span v-if="isLoading">Creating account...</span>
          <span v-else>Register</span>
        </button>
      </form>
      
      <div class="mt-6 text-center">
        <p class="text-gray-600">
          Already have an account? 
          <RouterLink to="/login" class="text-primary-600 hover:text-primary-800 font-medium">
            Login here
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const isLoading = ref(false)

const handleRegister = async () => {
  error.value = ''
  
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  
  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  
  isLoading.value = true
  
  try {
    const result = await authStore.register({
      username: username.value,
      email: email.value,
      password: password.value
    })
    
    if (!result.success) {
      error.value = result.error || 'Registration failed'
    }
  } catch (err) {
    error.value = 'An unexpected error occurred'
  } finally {
    isLoading.value = false
  }
}
</script>