import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ChatSettings {
  maxRounds: number
}

interface ImageSettings {
  defaultModel: 'dall-e-2' | 'dall-e-3'
  defaultSize: '256x256' | '512x512' | '1024x1024' | '1792x1024' | '1024x1792'
  defaultStyle: 'educational' | 'cartoon' | 'realistic'
}

interface AppSettings {
  chat: ChatSettings
  image: ImageSettings
}

export const useSettingsStore = defineStore('settings', () => {
  // Default settings
  const defaultSettings: AppSettings = {
    chat: {
      maxRounds: 10
    },
    image: {
      defaultModel: 'dall-e-2',
      defaultSize: '512x512',
      defaultStyle: 'educational'
    }
  }

  // Reactive settings
  const chatMaxRounds = ref<number>(defaultSettings.chat.maxRounds)
  const imageDefaultModel = ref<'dall-e-2' | 'dall-e-3'>(defaultSettings.image.defaultModel)
  const imageDefaultSize = ref<string>(defaultSettings.image.defaultSize)
  const imageDefaultStyle = ref<'educational' | 'cartoon' | 'realistic'>(defaultSettings.image.defaultStyle)

  // Computed getters
  const chatSettings = computed<ChatSettings>(() => ({
    maxRounds: chatMaxRounds.value
  }))

  const imageSettings = computed<ImageSettings>(() => ({
    defaultModel: imageDefaultModel.value,
    defaultSize: imageDefaultSize.value as any,
    defaultStyle: imageDefaultStyle.value
  }))

  const allSettings = computed<AppSettings>(() => ({
    chat: chatSettings.value,
    image: imageSettings.value
  }))

  // Actions
  const loadSettings = () => {
    try {
      // Load chat settings
      const savedChatMaxRounds = localStorage.getItem('chat_max_rounds')
      if (savedChatMaxRounds) {
        const rounds = parseInt(savedChatMaxRounds)
        if (rounds > 0 && rounds <= 50) { // Reasonable limits
          chatMaxRounds.value = rounds
        }
      }

      // Load image settings
      const savedImageModel = localStorage.getItem('image_model')
      if (savedImageModel && ['dall-e-2', 'dall-e-3'].includes(savedImageModel)) {
        imageDefaultModel.value = savedImageModel as 'dall-e-2' | 'dall-e-3'
      }

      const savedImageSize = localStorage.getItem('image_size')
      if (savedImageSize && ['256x256', '512x512', '1024x1024', '1792x1024', '1024x1792'].includes(savedImageSize)) {
        imageDefaultSize.value = savedImageSize
      }

      const savedImageStyle = localStorage.getItem('image_style')
      if (savedImageStyle && ['educational', 'cartoon', 'realistic'].includes(savedImageStyle)) {
        imageDefaultStyle.value = savedImageStyle as 'educational' | 'cartoon' | 'realistic'
      }
    } catch (error) {
      console.error('Failed to load settings from localStorage:', error)
    }
  }

  const saveSettings = () => {
    try {
      localStorage.setItem('chat_max_rounds', chatMaxRounds.value.toString())
      localStorage.setItem('image_model', imageDefaultModel.value)
      localStorage.setItem('image_size', imageDefaultSize.value)
      localStorage.setItem('image_style', imageDefaultStyle.value)
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error)
    }
  }

  const updateChatMaxRounds = (rounds: number) => {
    if (rounds > 0 && rounds <= 50) {
      chatMaxRounds.value = rounds
      saveSettings()
    }
  }

  const updateImageModel = (model: 'dall-e-2' | 'dall-e-3') => {
    imageDefaultModel.value = model
    // Auto-adjust size if needed for model compatibility
    if (model === 'dall-e-3' && !['1024x1024', '1792x1024', '1024x1792'].includes(imageDefaultSize.value)) {
      imageDefaultSize.value = '1024x1024'
    } else if (model === 'dall-e-2' && !['256x256', '512x512', '1024x1024'].includes(imageDefaultSize.value)) {
      imageDefaultSize.value = '512x512'
    }
    saveSettings()
  }

  const updateImageSize = (size: string) => {
    // Validate size for current model
    const validSizes = imageDefaultModel.value === 'dall-e-3' 
      ? ['1024x1024', '1792x1024', '1024x1792']
      : ['256x256', '512x512', '1024x1024']
    
    if (validSizes.includes(size)) {
      imageDefaultSize.value = size
      saveSettings()
    }
  }

  const updateImageStyle = (style: 'educational' | 'cartoon' | 'realistic') => {
    imageDefaultStyle.value = style
    saveSettings()
  }

  const resetToDefaults = () => {
    chatMaxRounds.value = defaultSettings.chat.maxRounds
    imageDefaultModel.value = defaultSettings.image.defaultModel
    imageDefaultSize.value = defaultSettings.image.defaultSize
    imageDefaultStyle.value = defaultSettings.image.defaultStyle
    saveSettings()
  }

  const clearUserData = () => {
    // Called on logout to clear temporary data
    // Settings are persistent, but this could be extended for user-specific settings
    try {
      // Clear any temporary settings if needed
      localStorage.removeItem('temp_chat_data')
      localStorage.removeItem('temp_image_data')
    } catch (error) {
      console.error('Failed to clear user data:', error)
    }
  }

  // Valid size options based on current model
  const validSizeOptions = computed(() => {
    return imageDefaultModel.value === 'dall-e-3' 
      ? [
          { value: '1024x1024', label: '1024x1024 (Square)' },
          { value: '1792x1024', label: '1792x1024 (Landscape)' },
          { value: '1024x1792', label: '1024x1792 (Portrait)' }
        ]
      : [
          { value: '256x256', label: '256x256 (Small)' },
          { value: '512x512', label: '512x512 (Medium)' },
          { value: '1024x1024', label: '1024x1024 (Large)' }
        ]
  })

  return {
    // State
    chatMaxRounds,
    imageDefaultModel,
    imageDefaultSize,
    imageDefaultStyle,
    
    // Computed
    chatSettings,
    imageSettings,
    allSettings,
    validSizeOptions,
    
    // Actions
    loadSettings,
    saveSettings,
    updateChatMaxRounds,
    updateImageModel,
    updateImageSize,
    updateImageStyle,
    resetToDefaults,
    clearUserData
  }
})