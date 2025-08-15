import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

interface FavoriteItem {
  id: number
  lemma: string
  pos: string
  cefr: string
  added_at: string
}

export const useFavoritesStore = defineStore('favorites', () => {
  const authStore = useAuthStore()
  const favorites = ref<FavoriteItem[]>([])
  const isLoading = ref(false)
  const error = ref('')
  
  const API_BASE = 'http://localhost:8000'
  
  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${authStore.token}`,
    'Content-Type': 'application/json'
  })
  
  const loadFavorites = async () => {
    if (!authStore.isAuthenticated) return
    
    isLoading.value = true
    error.value = ''
    
    try {
      const response = await fetch(`${API_BASE}/favorites/`, {
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        favorites.value = await response.json()
      } else {
        error.value = 'Failed to load favorites'
      }
    } catch (err) {
      error.value = 'Network error loading favorites'
    } finally {
      isLoading.value = false
    }
  }
  
  const addToFavorites = async (lemma: string) => {
    if (!authStore.isAuthenticated) {
      throw new Error('Please login to add favorites')
    }
    
    try {
      const response = await fetch(`${API_BASE}/favorites/add/${encodeURIComponent(lemma)}`, {
        method: 'POST',
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        await loadFavorites() // Refresh the list
        return true
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to add to favorites')
      }
    } catch (err: any) {
      throw new Error(err.message || 'Failed to add to favorites')
    }
  }
  
  const removeFromFavorites = async (lemma: string) => {
    if (!authStore.isAuthenticated) {
      throw new Error('Please login to remove favorites')
    }
    
    try {
      const response = await fetch(`${API_BASE}/favorites/remove/${encodeURIComponent(lemma)}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        await loadFavorites() // Refresh the list
        return true
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to remove from favorites')
      }
    } catch (err: any) {
      throw new Error(err.message || 'Failed to remove from favorites')
    }
  }
  
  const checkIfFavorite = async (lemma: string): Promise<boolean> => {
    if (!authStore.isAuthenticated) return false
    
    try {
      const response = await fetch(`${API_BASE}/favorites/check/${encodeURIComponent(lemma)}`, {
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        const result = await response.json()
        return result.is_favorite
      }
      return false
    } catch (err) {
      return false
    }
  }
  
  const isFavorite = (lemma: string): boolean => {
    return favorites.value.some(item => item.lemma === lemma)
  }
  
  return {
    favorites,
    isLoading,
    error,
    loadFavorites,
    addToFavorites,
    removeFromFavorites,
    checkIfFavorite,
    isFavorite
  }
})