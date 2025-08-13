<template>
  <div class="flex items-center space-x-2">
    <span class="text-2xl">⏰</span>
    <span 
      :class="timeRemaining < warningThreshold ? 'text-red-400 animate-pulse' : 'text-cosmic'"
      class="text-lg font-mono font-bold"
    >
      {{ formatTime(timeRemaining) }}
    </span>
    <div v-if="showProgress" class="w-24">
      <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          class="h-full transition-all duration-1000"
          :class="timeRemaining < warningThreshold ? 'bg-red-500' : 'bg-cosmic'"
          :style="{ width: progressPercentage + '%' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  timeRemaining: number
  totalTime: number
  warningThreshold?: number
  showProgress?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  warningThreshold: 300, // 5 minutes
  showProgress: true
})

const progressPercentage = computed(() => {
  if (props.totalTime === 0) return 0
  return Math.max(0, Math.min(100, (props.timeRemaining / props.totalTime) * 100))
})

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>