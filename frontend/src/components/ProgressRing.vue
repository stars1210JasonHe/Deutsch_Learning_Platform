<template>
  <div class="relative inline-block">
    <svg :class="`w-${size} h-${size} transform -rotate-90`" viewBox="0 0 100 100">
      <circle
        cx="50" cy="50" r="40"
        stroke="rgba(107, 114, 128, 0.3)" 
        :stroke-width="strokeWidth"
        fill="none"
      />
      <circle
        cx="50" cy="50" r="40"
        stroke="url(#cosmic-gradient-ring)" 
        :stroke-width="strokeWidth"
        fill="none"
        stroke-dasharray="251.2"
        :stroke-dashoffset="251.2 - (251.2 * percentage / 100)"
        stroke-linecap="round"
        class="transition-all duration-1000"
      />
      <defs>
        <linearGradient id="cosmic-gradient-ring" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#8B5CF6" />
          <stop offset="50%" style="stop-color:#EC4899" />
          <stop offset="100%" style="stop-color:#00C9DB" />
        </linearGradient>
      </defs>
    </svg>
    
    <div class="absolute inset-0 flex items-center justify-center">
      <div class="text-center">
        <div :class="`text-${textSize} font-bold text-white`">
          {{ showPercentage ? Math.round(percentage) + '%' : value }}
        </div>
        <div v-if="label" class="text-xs text-gray-400 mt-1">
          {{ label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  percentage: number
  value?: string | number
  label?: string
  size?: string
  strokeWidth?: number
  textSize?: string
  showPercentage?: boolean
}

withDefaults(defineProps<Props>(), {
  size: '32',
  strokeWidth: 8,
  textSize: '2xl',
  showPercentage: true
})
</script>