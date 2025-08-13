<template>
  <div class="space-y-4">
    <!-- Question Counter -->
    <div class="flex justify-between items-center">
      <div class="text-sm text-gray-400">
        Question {{ current }} of {{ total }}
      </div>
      <div class="text-sm text-gray-400">
        {{ answered }} answered
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="progress-cosmic">
      <div 
        class="progress-fill transition-all duration-500" 
        :style="{ width: progressPercentage + '%' }"
      ></div>
    </div>

    <!-- Question Indicators (for smaller exams) -->
    <div v-if="total <= 20" class="flex flex-wrap gap-1 justify-center">
      <div
        v-for="(question, index) in Array.from({ length: total })"
        :key="index"
        class="w-3 h-3 rounded-full border-2 transition-all"
        :class="getQuestionIndicatorClass(index + 1)"
      ></div>
    </div>

    <!-- Completion Stats -->
    <div v-if="showStats" class="text-center">
      <div class="text-xs text-gray-500">
        {{ Math.round(completionPercentage) }}% complete
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  current: number
  total: number
  answered: number
  answeredQuestions?: Set<number>
  showStats?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showStats: true
})

const progressPercentage = computed(() => {
  if (props.total === 0) return 0
  return Math.round((props.current / props.total) * 100)
})

const completionPercentage = computed(() => {
  if (props.total === 0) return 0
  return (props.answered / props.total) * 100
})

const getQuestionIndicatorClass = (questionNumber: number) => {
  const isAnswered = props.answeredQuestions?.has(questionNumber) || false
  const isCurrent = questionNumber === props.current
  
  if (isCurrent) {
    return 'border-cosmic bg-cosmic/50'
  } else if (isAnswered) {
    return 'border-green-500 bg-green-500/50'
  } else {
    return 'border-gray-600'
  }
}
</script>