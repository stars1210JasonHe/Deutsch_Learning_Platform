<template>
  <div class="multiple-choice-container">
    <div class="text-center mb-6">
      <div class="text-6xl mb-4">🤔</div>
      <h3 class="text-2xl font-semibold text-white mb-2">{{ originalQuery }}</h3>
      <p class="text-gray-400 mb-4">{{ originalQuery }} has multiple meanings. Here are some options you might be looking for:</p>
      <p class="text-lg font-medium text-white">Did you mean one of these?</p>
    </div>
    
    <div class="choices-list space-y-3">
      <div 
        v-for="choice in choices" 
        :key="choice.lemma_id"
        class="choice-item"
        @click="selectChoice(choice)"
      >
        <div class="choice-content">
          <!-- Left side: Word and POS badge -->
          <div class="choice-left">
            <span class="choice-word">{{ choice.display_name }}</span>
            <span class="pos-badge" :class="`pos-${choice.pos.toLowerCase()}`">
              {{ choice.pos.toLowerCase() }}
            </span>
          </div>
          
          <!-- Right side: Translation -->
          <div class="choice-right">
            <span class="choice-translation">
              {{ getTranslationText(choice) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface WordChoice {
  lemma_id: number
  lemma: string
  pos: string
  display_name: string
  pos_display: string
  translations_en: string[]
  translations_zh: string[]
  preview: string
}

interface Props {
  choices: WordChoice[]
  message: string
  originalQuery: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  choiceSelected: [choice: WordChoice]
}>()

const selectChoice = (choice: WordChoice) => {
  emit('choiceSelected', choice)
}

const getTranslationText = (choice: WordChoice) => {
  // Combine English and Chinese translations, prefer English if available
  const translations = []
  
  if (choice.translations_en.length > 0) {
    translations.push(choice.translations_en.slice(0, 2).join(', '))
  }
  
  if (choice.translations_zh.length > 0) {
    const zhTranslations = choice.translations_zh.slice(0, 2).join(', ')
    if (translations.length > 0) {
      translations.push(`(${zhTranslations})`)
    } else {
      translations.push(zhTranslations)
    }
  }
  
  return translations.join(' ') || 'No translation available'
}
</script>

<style scoped>
.multiple-choice-container {
  @apply max-w-3xl mx-auto;
}

.choices-list {
  @apply space-y-3;
}

.choice-item {
  @apply bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 cursor-pointer transition-all duration-200 hover:bg-white/20 hover:border-white/30;
}

.choice-content {
  @apply flex justify-between items-center p-4;
}

.choice-left {
  @apply flex items-center space-x-3;
}

.choice-word {
  @apply text-lg font-medium text-white;
}

.pos-badge {
  @apply px-2 py-1 rounded text-xs font-medium text-white;
}

.pos-verb {
  @apply bg-green-500;
}

.pos-noun {
  @apply bg-blue-500;
}

.pos-adjective {
  @apply bg-purple-500;
}

.pos-adverb {
  @apply bg-orange-500;
}

.pos-preposition {
  @apply bg-pink-500;
}

.pos-article {
  @apply bg-indigo-500;
}

.choice-right {
  @apply text-right;
}

.choice-translation {
  @apply text-gray-300 text-sm;
}

/* Hover effects */
.choice-item:hover .choice-word {
  @apply text-cosmic;
}

.choice-item:hover .choice-translation {
  @apply text-white;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .choice-content {
    @apply p-3;
  }
  
  .choice-word {
    @apply text-base;
  }
  
  .choice-translation {
    @apply text-xs;
  }
}
</style>