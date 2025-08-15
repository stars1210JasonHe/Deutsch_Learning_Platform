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
  remember_me?: boolean
}

interface RegisterCredentials {
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const tokenExpiry = ref<number | null>(parseInt(localStorage.getItem('tokenExpiry') || '0'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  // Set axios default authorization header
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
  
  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials)
      const { access_token, refresh_token, expires_in } = response.data
      
      // Store tokens and expiry
      token.value = access_token
      refreshToken.value = refresh_token
      const expiryTime = Date.now() + (expires_in * 60 * 1000) // Convert minutes to milliseconds
      tokenExpiry.value = expiryTime
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('refreshToken', refresh_token)
      localStorage.setItem('tokenExpiry', expiryTime.toString())
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      // Get user info
      await getCurrentUser()
      
      // Start token refresh timer
      startTokenRefreshTimer()
      
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
  
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('No refresh token available')
      }
      
      const response = await axios.post('/api/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      const { access_token, refresh_token: new_refresh_token, expires_in } = response.data
      
      // Update tokens
      token.value = access_token
      refreshToken.value = new_refresh_token
      const expiryTime = Date.now() + (expires_in * 60 * 1000)
      tokenExpiry.value = expiryTime
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('refreshToken', new_refresh_token)
      localStorage.setItem('tokenExpiry', expiryTime.toString())
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      return false
    }
  }

  let refreshTimer: number | null = null

  const startTokenRefreshTimer = () => {
    // Clear existing timer
    if (refreshTimer) {
      clearTimeout(refreshTimer)
    }
    
    if (!tokenExpiry.value) return
    
    // Refresh token 5 minutes before expiry
    const refreshTime = tokenExpiry.value - Date.now() - (5 * 60 * 1000)
    
    if (refreshTime > 0) {
      refreshTimer = setTimeout(async () => {
        const success = await refreshAccessToken()
        if (success) {
          startTokenRefreshTimer() // Schedule next refresh
        }
      }, refreshTime)
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    refreshToken.value = null
    tokenExpiry.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('tokenExpiry')
    
    delete axios.defaults.headers.common['Authorization']
    
    // Clear refresh timer
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }
    
    router.push('/login')
  }
  
  // Initialize user on store creation
  if (token.value) {
    getCurrentUser()
    startTokenRefreshTimer() // Start auto-refresh on page load
  }
  
  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    login,
    register,
    logout,
    getCurrentUser,
    refreshAccessToken
  }
})