<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Report Issue</h3>
        <button 
          @click="$emit('close')" 
          class="text-gray-400 hover:text-gray-600 text-xl"
        >
          ×
        </button>
      </div>
      
      <form @submit.prevent="submitFeedback" class="space-y-4">
        <!-- Word Info -->
        <div class="bg-gray-50 rounded-lg p-3">
          <p class="text-sm text-gray-600">Reporting issue for:</p>
          <p class="font-medium text-gray-900">{{ wordData.original }}</p>
        </div>
        
        <!-- Feedback Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            What's wrong?
          </label>
          <select 
            v-model="feedbackForm.feedback_type" 
            required
            class="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select issue type...</option>
            <option value="incorrect_meaning">Incorrect meaning/translation</option>
            <option value="incorrect_example">Incorrect example sentence</option>
            <option value="incorrect_grammar">Wrong grammatical information</option>
            <option value="other">Other issue</option>
          </select>
        </div>
        
        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Describe the issue
          </label>
          <textarea 
            v-model="feedbackForm.description"
            required
            rows="4"
            placeholder="Please explain what's wrong with this word information..."
            class="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          ></textarea>
        </div>
        
        <!-- Suggested Correction -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Suggested correction (optional)
          </label>
          <textarea 
            v-model="feedbackForm.suggested_correction"
            rows="2"
            placeholder="If you know the correct information, please share it here..."
            class="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          ></textarea>
        </div>
        
        <!-- Buttons -->
        <div class="flex space-x-3 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="flex-1 px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 transition-colors"
          >
            {{ isSubmitting ? 'Submitting...' : 'Submit Report' }}
          </button>
        </div>
      </form>
      
      <!-- Success Message -->
      <div v-if="showSuccess" class="mt-4 p-3 bg-green-100 border border-green-300 rounded-md">
        <p class="text-green-700 text-sm">
          ✓ Thank you! Your feedback has been submitted and will be reviewed by our team.
        </p>
      </div>
      
      <!-- Error Message -->
      <div v-if="errorMessage" class="mt-4 p-3 bg-red-100 border border-red-300 rounded-md">
        <p class="text-red-700 text-sm">
          {{ errorMessage }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import axios from 'axios'

const props = defineProps<{
  word: string
  wordData: any
  lemmaId?: number
}>()

defineEmits<{
  close: []
}>()

const isSubmitting = ref(false)
const showSuccess = ref(false)
const errorMessage = ref('')

const feedbackForm = reactive({
  feedback_type: '',
  description: '',
  suggested_correction: ''
})

const submitFeedback = async () => {
  if (!props.lemmaId) {
    errorMessage.value = 'Unable to submit feedback: word ID not found'
    return
  }
  
  isSubmitting.value = true
  errorMessage.value = ''
  
  try {
    await axios.post(`/api/feedback/word/${props.lemmaId}`, feedbackForm)
    showSuccess.value = true
    
    // Reset form
    feedbackForm.feedback_type = ''
    feedbackForm.description = ''
    feedbackForm.suggested_correction = ''
    
    // Close modal after 2 seconds
    setTimeout(() => {
      showSuccess.value = false
      // Emit close event
      document.dispatchEvent(new CustomEvent('closeFeedbackModal'))
    }, 2000)
    
  } catch (error: any) {
    console.error('Failed to submit feedback:', error)
    errorMessage.value = error.response?.data?.detail || 'Failed to submit feedback. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>