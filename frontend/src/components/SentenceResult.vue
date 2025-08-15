<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold text-gray-900">Translation Result</h2>
      <span 
        v-if="result.cached" 
        class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full"
      >
        Cached
      </span>
    </div>
    
    <div class="space-y-6">
      <!-- Original and Translation -->
      <div class="grid md:grid-cols-2 gap-6">
        <div>
          <h3 class="font-semibold text-gray-700 mb-2">Original</h3>
          <div class="bg-gray-50 p-3 rounded-lg">
            <div class="flex items-center justify-between">
              <p class="text-gray-800">{{ result.original }}</p>
              <SpeechButton :text="result.original" size="sm" lang="en-US" />
            </div>
          </div>
        </div>
        
        <div v-if="result.german">
          <h3 class="font-semibold text-gray-700 mb-2">German Translation</h3>
          <div class="bg-blue-50 p-3 rounded-lg">
            <div class="flex items-center justify-between">
              <p class="text-gray-800">{{ result.german }}</p>
              <SpeechButton :text="result.german" size="sm" />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Word-by-word Gloss -->
      <div v-if="result.gloss && result.gloss.length">
        <h3 class="font-semibold text-gray-700 mb-3">Word-by-word Analysis</h3>
        
        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr class="bg-gray-50">
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">German</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">English</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">中文</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">Note</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in result.gloss" :key="index" class="hover:bg-gray-50">
                <td class="border border-gray-300 px-3 py-2">
                  <div class="flex items-center justify-between">
                    <span class="font-medium">{{ item.de }}</span>
                    <SpeechButton :text="item.de" size="sm" />
                  </div>
                </td>
                <td class="border border-gray-300 px-3 py-2">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">{{ item.en }}</span>
                    <SpeechButton v-if="item.en" :text="item.en" size="sm" lang="en-US" />
                  </div>
                </td>
                <td class="border border-gray-300 px-3 py-2">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">{{ item.zh }}</span>
                    <SpeechButton v-if="item.zh" :text="item.zh" size="sm" lang="zh-CN" />
                  </div>
                </td>
                <td class="border border-gray-300 px-3 py-2 text-gray-500 text-sm">
                  {{ item.note || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SpeechButton from './SpeechButton.vue'

interface SentenceTranslation {
  original: string
  german: string
  gloss: Array<{
    de: string
    en: string
    zh: string
    note?: string
  }>
  cached: boolean
}

defineProps<{
  result: SentenceTranslation
}>()
</script>