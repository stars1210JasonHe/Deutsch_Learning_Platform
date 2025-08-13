import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '@/router'

interface User {
  id: number
  email: string
  role: string
}

interface LoginCredentials {
  email: string
  password: string
}

interface RegisterCredentials {
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  // Set axios default authorization header
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
  
  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials)
      const { access_token } = response.data
      
      token.value = access_token
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      // Get user info
      await getCurrentUser()
      
      router.push('/')
      
      return { success: true }
    } catch (error: any) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }
  
  const register = async (credentials: RegisterCredentials) => {
    try {
      await axios.post('/api/auth/register', credentials)
      
      // Auto-login after registration
      return await login(credentials)
    } catch (error: any) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      }
    }
  }
  
  const getCurrentUser = async () => {
    try {
      const response = await axios.get('/api/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    router.push('/login')
  }
  
  // Initialize user on store creation
  if (token.value) {
    getCurrentUser()
  }
  
  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
    getCurrentUser
  }
})