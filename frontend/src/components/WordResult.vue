<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <!-- Word Not Found - Show Suggestions -->
    <div v-if="result.found === false" class="text-center">
      <div class="text-6xl mb-4">🤔</div>
      <h2 class="text-2xl font-bold text-gray-900 mb-4">{{ result.original }}</h2>
      <p class="text-gray-600 mb-6">{{ result.message || "Word not found" }}</p>
      
      <div v-if="result.suggestions && result.suggestions.length > 0" class="space-y-4">
        <h3 class="text-lg font-semibold text-gray-700">Did you mean one of these?</h3>
        <div class="grid gap-3">
          <button
            v-for="(suggestion, index) in result.suggestions"
            :key="suggestion.word"
            @click="selectSuggestion(suggestion.word)"
            class="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
            :disabled="isLoading"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-gray-900">{{ suggestion.word }}</span>
                <span class="ml-2 text-sm px-2 py-1 rounded-full"
                      :class="getPosClass(suggestion.pos)">
                  {{ getPosDisplay(suggestion.pos) }}
                </span>
              </div>
              <span class="text-sm text-gray-500">{{ suggestion.meaning }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Word Found - Show Analysis -->
    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <h2 class="text-2xl font-bold text-gray-900">{{ result.original }}</h2>
          <SpeechButton :text="result.original" size="sm" />
          <FavoriteButton :lemma="result.original" />
          <button 
            @click="openChatModal"
            class="p-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-lg transition-colors"
            title="Chat about this word"
            :disabled="isLoading"
          >
            💬
          </button>
          <button 
            @click="openImageModal"
            class="p-2 bg-purple-100 hover:bg-purple-200 text-purple-800 rounded-lg transition-colors"
            title="Generate image for this word"
            :disabled="isLoading"
          >
            🎨
          </button>
        </div>
      </div>
    
      <div class="space-y-6">
      
      <!-- Word Title with Article (for nouns) -->
      <div class="mb-4">
        <h2 class="text-3xl font-bold text-gray-900">
          <span v-if="result.article && (result.pos === 'noun' || result.upos === 'NOUN')" class="text-blue-600 mr-2">
            {{ result.article }}
          </span>
          {{ result.original }}
        </h2>
        
        <!-- Plural form for nouns -->
        <div v-if="result.plural && (result.pos === 'noun' || result.upos === 'NOUN')" class="mt-2">
          <span class="text-sm text-gray-600">Plural: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.plural }}</span>
        </div>
        
        <!-- Comparative and Superlative for adjectives -->
        <div v-if="result.degree_forms && result.pos === 'adj'" class="mt-2 space-y-1">
          <div v-if="result.degree_forms.comparative">
            <span class="text-sm text-gray-600">Comparative: </span>
            <span class="text-sm font-medium text-gray-800">{{ result.degree_forms.comparative }}</span>
          </div>
          <div v-if="result.degree_forms.superlative">
            <span class="text-sm text-gray-600">Superlative: </span>
            <span class="text-sm font-medium text-gray-800">{{ result.degree_forms.superlative }}</span>
          </div>
        </div>
        
        <!-- Case governance for prepositions -->
        <div v-if="result.governance && (result.pos === 'prep' || result.pos === 'preposition' || result.upos === 'ADP')" class="mt-2">
          <span class="text-sm text-gray-600">Governs: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.governance }}</span>
        </div>
        
        <!-- Type classification for adverbs -->
        <div v-if="result.adv_type && result.pos === 'adv'" class="mt-2">
          <span class="text-sm text-gray-600">Type: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.adv_type }}</span>
        </div>
        
        <!-- Conjunction type -->
        <div v-if="result.conj_type && result.pos === 'conj'" class="mt-2">
          <span class="text-sm text-gray-600">Type: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.conj_type }}</span>
        </div>
        
        <!-- Pronoun information -->
        <div v-if="result.pron_info && result.pos === 'pron'" class="mt-2">
          <div v-if="result.pron_info.type">
            <span class="text-sm text-gray-600">Type: </span>
            <span class="text-sm font-medium text-gray-800">{{ result.pron_info.type }}</span>
          </div>
          <div v-if="result.pron_info.cases" class="mt-1">
            <span class="text-sm text-gray-600">Cases: </span>
            <span class="text-sm font-medium text-gray-800">
              <span v-for="(form, case_name) in result.pron_info.cases" :key="case_name" class="mr-2">
                {{ case_name }}: {{ form }}
              </span>
            </span>
          </div>
        </div>
        
        <!-- Determiner type -->
        <div v-if="result.det_type && result.pos === 'det'" class="mt-2">
          <span class="text-sm text-gray-600">Type: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.det_type }}</span>
        </div>
        
        <!-- Numeral information -->
        <div v-if="result.num_info && (result.pos === 'num' || result.pos === 'numeral')" class="mt-2">
          <div v-if="result.num_info.type">
            <span class="text-sm text-gray-600">Type: </span>
            <span class="text-sm font-medium text-gray-800">{{ result.num_info.type }}</span>
          </div>
          <div v-if="result.num_info.value" class="mt-1">
            <span class="text-sm text-gray-600">Value: </span>
            <span class="text-sm font-medium text-gray-800">{{ result.num_info.value }}</span>
          </div>
        </div>
        
        <!-- Particle type -->
        <div v-if="result.particle_type && result.pos === 'particle'" class="mt-2">
          <span class="text-sm text-gray-600">Type: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.particle_type }}</span>
        </div>
        
        <!-- Interjection register -->
        <div v-if="result.interj_register && result.pos === 'interj'" class="mt-2">
          <span class="text-sm text-gray-600">Register: </span>
          <span class="text-sm font-medium text-gray-800">{{ result.interj_register }}</span>
        </div>
      </div>
      
      <!-- Part of Speech & Basic Info -->
      <div class="space-y-4">
        <!-- Primary Info Row -->
        <div class="flex flex-wrap gap-2">
          <span v-if="result.upos || result.pos" class="px-3 py-1 rounded-full text-sm font-medium"
                :class="getPosClass(result.pos || result.upos || '')">
            {{ getPosDisplay(result.pos || result.upos || '', result.verb_props) }}
          </span>
          
          <!-- Article for Nouns (also as badge) -->
          <span v-if="result.article && (result.pos === 'noun' || result.upos === 'NOUN')" class="px-3 py-1 rounded-full text-sm font-medium"
                :class="getArticleClass(result.article)">
            {{ result.article }}
          </span>
          
          <!-- Verb Properties (badges) -->
          <span v-if="result.verb_props?.separable" class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm">
            separable
          </span>
          <span v-if="result.verb_props?.reflexive" class="bg-teal-100 text-teal-800 px-3 py-1 rounded-full text-sm">
            reflexive
          </span>
          <span v-if="result.verb_props?.aux" class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">
            {{ result.verb_props.aux }}
          </span>
          <span v-if="result.verb_props?.regularity" class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm">
            {{ result.verb_props.regularity }}
          </span>
          
          <!-- Adjective badges -->
          <span v-if="result.degree_forms?.comparative" class="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
            comparative
          </span>
          <span v-if="result.degree_forms?.superlative" class="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm">
            superlative
          </span>
          
          <!-- Preposition badge -->
          <span v-if="result.governance && (result.pos === 'prep' || result.pos === 'preposition' || result.upos === 'ADP')" class="bg-cyan-100 text-cyan-800 px-3 py-1 rounded-full text-sm">
            + {{ result.governance }}
          </span>
          
          <!-- Adverb type badge -->
          <span v-if="result.adv_type" class="bg-lime-100 text-lime-800 px-3 py-1 rounded-full text-sm">
            {{ result.adv_type }}
          </span>
          
          <!-- Conjunction type badge -->
          <span v-if="result.conj_type" class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
            {{ result.conj_type }}
          </span>
          
          <!-- Pronoun type badge -->
          <span v-if="result.pron_info?.type" class="bg-pink-100 text-pink-800 px-3 py-1 rounded-full text-sm">
            {{ result.pron_info.type }}
          </span>
          
          <!-- Determiner type badge -->
          <span v-if="result.det_type" class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">
            {{ result.det_type }}
          </span>
          
          <!-- Numeral type badge -->
          <span v-if="result.num_info?.type" class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm">
            {{ result.num_info.type }}
          </span>
          
          <!-- Numeral value badge -->
          <span v-if="result.num_info?.value" class="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
            = {{ result.num_info.value }}
          </span>
          
          <!-- Particle type badge -->
          <span v-if="result.particle_type" class="bg-teal-100 text-teal-800 px-3 py-1 rounded-full text-sm">
            {{ result.particle_type }}
          </span>
          
          <!-- Interjection register badge -->
          <span v-if="result.interj_register" class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm">
            {{ result.interj_register }}
          </span>
        </div>

        <!-- Noun Properties -->
        <div v-if="result.noun_props && result.upos === 'NOUN'" class="bg-purple-50 rounded-lg p-4">
          <h4 class="font-medium text-purple-900 mb-2">Noun Properties</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div v-if="result.noun_props.plural">
              <span class="text-purple-600">Plural:</span>
              <span class="ml-1 font-medium">{{ result.noun_props.plural }}</span>
            </div>
            <div v-if="result.noun_props.gen_sg">
              <span class="text-purple-600">Genitive:</span>
              <span class="ml-1 font-medium">{{ result.noun_props.gen_sg }}</span>
            </div>
            <div v-if="result.noun_props.declension_class">
              <span class="text-purple-600">Declension:</span>
              <span class="ml-1 font-medium">{{ result.noun_props.declension_class }}</span>
            </div>
          </div>
        </div>

        <!-- Verb Properties -->
        <div v-if="result.verb_props && result.pos === 'verb'" class="bg-green-50 rounded-lg p-4">
          <h4 class="font-medium text-green-900 mb-2">🔧 Verb Properties</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <!-- Separability -->
            <div v-if="result.verb_props.separable" class="flex items-center space-x-2">
              <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium">
                SEPARABLE
              </span>
              <span class="text-gray-600">Can be split</span>
            </div>
            
            <!-- Reflexivity -->
            <div v-if="result.verb_props.reflexive" class="flex items-center space-x-2">
              <span class="bg-teal-100 text-teal-800 px-2 py-1 rounded text-xs font-medium">
                REFLEXIVE
              </span>
              <span class="text-gray-600">Used with sich</span>
            </div>
            
            <!-- Auxiliary -->
            <div v-if="result.verb_props.aux" class="flex items-center space-x-2">
              <span class="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs font-medium">
                AUX: {{ result.verb_props.aux.toUpperCase() }}
              </span>
              <span class="text-gray-600">Perfect tense</span>
            </div>
            
            <!-- Regularity -->
            <div v-if="result.verb_props.regularity">
              <span class="text-green-600 font-medium">Type:</span>
              <span class="ml-1 capitalize">{{ result.verb_props.regularity }}</span>
            </div>
            
            <!-- Partizip II -->
            <div v-if="result.verb_props.partizip_ii">
              <span class="text-green-600 font-medium">Partizip II:</span>
              <span class="ml-1 font-medium">{{ result.verb_props.partizip_ii }}</span>
            </div>
            
            <!-- Valency (Cases) -->
            <div v-if="result.verb_props.cases && result.verb_props.cases.length > 0">
              <span class="text-green-600 font-medium">Cases:</span>
              <div class="flex flex-wrap gap-1 mt-1">
                <span 
                  v-for="case_type in result.verb_props.cases" 
                  :key="case_type"
                  class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs"
                >
                  {{ case_type }}
                </span>
              </div>
            </div>
            
            <!-- Prepositions -->
            <div v-if="result.verb_props.preps && result.verb_props.preps.length > 0">
              <span class="text-green-600 font-medium">Prepositions:</span>
              <div class="flex flex-wrap gap-1 mt-1">
                <span 
                  v-for="prep in result.verb_props.preps" 
                  :key="prep"
                  class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs"
                >
                  {{ prep }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Adjective Properties -->
        <div v-if="result.degree_forms && result.pos === 'adj'" class="bg-yellow-50 rounded-lg p-4">
          <h4 class="font-medium text-yellow-900 mb-2">📐 Adjective Forms</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div v-if="result.degree_forms.comparative">
              <span class="text-yellow-600 font-medium">Comparative:</span>
              <span class="ml-1 font-medium">{{ result.degree_forms.comparative }}</span>
            </div>
            <div v-if="result.degree_forms.superlative">
              <span class="text-yellow-600 font-medium">Superlative:</span>
              <span class="ml-1 font-medium">{{ result.degree_forms.superlative }}</span>
            </div>
          </div>
        </div>
        
        <!-- Preposition Properties -->
        <div v-if="result.governance && (result.pos === 'prep' || result.pos === 'preposition' || result.upos === 'ADP')" class="bg-cyan-50 rounded-lg p-4">
          <h4 class="font-medium text-cyan-900 mb-2">⚖️ Preposition Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-cyan-600 font-medium">Case Governance:</span>
              <span class="ml-1 font-medium">{{ result.governance }}</span>
            </div>
          </div>
        </div>
        
        <!-- Adverb Properties -->
        <div v-if="result.adv_type && result.pos === 'adv'" class="bg-lime-50 rounded-lg p-4">
          <h4 class="font-medium text-lime-900 mb-2">🎯 Adverb Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-lime-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.adv_type }}</span>
            </div>
          </div>
        </div>
        
        <!-- Conjunction Properties -->
        <div v-if="result.conj_type && result.pos === 'conj'" class="bg-purple-50 rounded-lg p-4">
          <h4 class="font-medium text-purple-900 mb-2">🔗 Conjunction Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-purple-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.conj_type }}</span>
            </div>
          </div>
        </div>
        
        <!-- Pronoun Properties -->
        <div v-if="result.pron_info && result.pos === 'pron'" class="bg-pink-50 rounded-lg p-4">
          <h4 class="font-medium text-pink-900 mb-2">👤 Pronoun Properties</h4>
          <div class="text-sm space-y-2">
            <div v-if="result.pron_info.type">
              <span class="text-pink-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.pron_info.type }}</span>
            </div>
            <div v-if="result.pron_info.cases">
              <span class="text-pink-600 font-medium">Case Forms:</span>
              <div class="mt-1 grid grid-cols-2 gap-2">
                <div v-for="(form, case_name) in result.pron_info.cases" :key="case_name" class="text-sm">
                  <span class="text-pink-500 font-medium">{{ case_name }}:</span>
                  <span class="ml-1 font-medium">{{ form }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Determiner Properties -->
        <div v-if="result.det_type && result.pos === 'det'" class="bg-indigo-50 rounded-lg p-4">
          <h4 class="font-medium text-indigo-900 mb-2">📍 Determiner Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-indigo-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.det_type }}</span>
            </div>
          </div>
        </div>
        
        <!-- Numeral Properties -->
        <div v-if="result.num_info && (result.pos === 'num' || result.pos === 'numeral')" class="bg-orange-50 rounded-lg p-4">
          <h4 class="font-medium text-orange-900 mb-2">🔢 Numeral Properties</h4>
          <div class="text-sm space-y-1">
            <div v-if="result.num_info.type">
              <span class="text-orange-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.num_info.type }}</span>
            </div>
            <div v-if="result.num_info.value">
              <span class="text-orange-600 font-medium">Numeric Value:</span>
              <span class="ml-1 font-medium">{{ result.num_info.value }}</span>
            </div>
          </div>
        </div>
        
        <!-- Particle Properties -->
        <div v-if="result.particle_type && result.pos === 'particle'" class="bg-teal-50 rounded-lg p-4">
          <h4 class="font-medium text-teal-900 mb-2">✨ Particle Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-teal-600 font-medium">Type:</span>
              <span class="ml-1 font-medium capitalize">{{ result.particle_type }}</span>
            </div>
          </div>
        </div>
        
        <!-- Interjection Properties -->
        <div v-if="result.interj_register && result.pos === 'interj'" class="bg-gray-50 rounded-lg p-4">
          <h4 class="font-medium text-gray-900 mb-2">❗ Interjection Properties</h4>
          <div class="text-sm">
            <div>
              <span class="text-gray-600 font-medium">Register:</span>
              <span class="ml-1 font-medium capitalize">{{ result.interj_register }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Glosses & Translations -->
      <div class="space-y-4">
        <!-- Primary Glosses -->
        <div v-if="result.gloss_en || result.gloss_zh || hasTranslations" class="bg-gray-50 rounded-lg p-4">
          <h3 class="font-semibold text-gray-700 mb-2">Meaning</h3>
          <div class="space-y-2">
            <div v-if="result.gloss_en" class="text-gray-800">
              <span class="font-medium text-gray-600">EN:</span> {{ result.gloss_en }}
            </div>
            <div v-if="result.gloss_zh" class="text-gray-800">
              <span class="font-medium text-gray-600">中文:</span> {{ result.gloss_zh }}
            </div>
            
            <!-- Show first translation if no gloss -->
            <div v-if="!result.gloss_en && result.translations_en && result.translations_en.length > 0" class="text-gray-800">
              <span class="font-medium text-gray-600">EN:</span> {{ result.translations_en.join(', ') }}
            </div>
            <div v-if="!result.gloss_zh && result.translations_zh && result.translations_zh.length > 0" class="text-gray-800">
              <span class="font-medium text-gray-600">中文:</span> {{ result.translations_zh.join('、') }}
            </div>
          </div>
        </div>

        <!-- Fallback: Show basic info if no translations -->
        <div v-else-if="result.pos || result.upos" class="bg-yellow-50 rounded-lg p-4">
          <h3 class="font-semibold text-gray-700 mb-2">Word Information</h3>
          <div class="text-gray-800">
            <p>This is a German <strong>{{ result.pos || result.upos }}</strong>.</p>
            <p class="text-sm text-gray-600 mt-2">Translation data is being processed. Please try searching again in a moment.</p>
          </div>
        </div>

        <!-- Additional Translations -->
        <div v-if="showAdditionalTranslations" class="grid md:grid-cols-2 gap-6">
          <div v-if="result.translations_en && result.translations_en.length > 1">
            <h3 class="font-semibold text-gray-700 mb-2">More English Translations</h3>
            <ul class="space-y-1">
              <li v-for="translation in result.translations_en.slice(1)" :key="translation" 
                  class="text-gray-600">
                • {{ translation }}
              </li>
            </ul>
          </div>
          
          <div v-if="result.translations_zh && result.translations_zh.length > 1">
            <h3 class="font-semibold text-gray-700 mb-2">更多中文翻译</h3>
            <ul class="space-y-1">
              <li v-for="translation in result.translations_zh.slice(1)" :key="translation" 
                  class="text-gray-600">
                • {{ translation }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- Conjugation Tables (for verbs) - Dynamic Display -->
      <div v-if="result.tables && (result.pos === 'verb' || result.upos === 'VERB')" class="space-y-4">
        <h3 class="font-semibold text-gray-700">Conjugation</h3>
        
        <!-- Dynamic Tenses Grid -->
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="(forms, tenseName) in result.tables" 
            :key="tenseName"
            :class="getTenseStyle(String(tenseName))"
            class="border rounded-lg p-4"
          >
            <h4 :class="getTenseHeaderClass(String(tenseName))" class="font-medium mb-3">
              {{ getTenseDisplayName(String(tenseName)) }}
            </h4>
            <div class="space-y-2 text-sm">
              <!-- Regular persons (ich, du, er_sie_es, wir, ihr, sie_Sie) -->
              <div v-for="person in getPersonsForTense(String(tenseName), forms)" :key="person" class="flex justify-between">
                <span class="text-gray-600 w-24 font-medium">{{ getPersonDisplayName(person) }}</span>
                <span :class="getTenseTextClass(String(tenseName))" class="font-medium">{{ forms[person] }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
      
      <!-- Example Sentence -->
      <div v-if="result.example" class="bg-gray-50 rounded-lg p-4">
        <h3 class="font-semibold text-gray-700 mb-3">Example</h3>
        <div class="space-y-2">
          <div class="flex items-center space-x-2">
            <p class="text-gray-800"><strong>DE:</strong> {{ result.example.de }}</p>
            <SpeechButton :text="result.example.de" size="sm" />
          </div>
          <div class="flex items-center space-x-2">
            <p class="text-gray-600"><strong>EN:</strong> {{ result.example.en }}</p>
            <SpeechButton v-if="result.example.en" :text="result.example.en" size="sm" lang="en-US" />
          </div>
          <div v-if="result.example.zh" class="flex items-center space-x-2">
            <p class="text-gray-600"><strong>ZH:</strong> {{ result.example.zh }}</p>
            <SpeechButton :text="result.example.zh" size="sm" lang="zh-CN" />
          </div>
        </div>
      </div>
    </div>
    </div>

    <!-- Chat Modal -->
    <ChatModal
      v-if="showChatModal"
      :word="result.original"
      :wordData="result"
      @close="closeChatModal"
    />

    <!-- Image Modal -->
    <ImageModal
      v-if="showImageModal"
      :word="result.original"
      :wordData="result"
      @close="closeImageModal"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSearchStore } from '@/stores/search'
import { usePartOfSpeech } from '@/composables/usePartOfSpeech'
import SpeechButton from './SpeechButton.vue'
import FavoriteButton from './FavoriteButton.vue'
import ChatModal from './ChatModal.vue'
import ImageModal from './ImageModal.vue'

const props = defineProps<{
  result: WordAnalysis
}>()

const searchStore = useSearchStore()
const { isLoading, selectSuggestedWord } = searchStore

// Part of Speech utilities
const { getPosDisplay, getPosClass, isVerbType } = usePartOfSpeech()

// Modal state
const showChatModal = ref(false)
const showImageModal = ref(false)

// Modal functions
const openChatModal = () => {
  showChatModal.value = true
}

const closeChatModal = () => {
  showChatModal.value = false
}

const openImageModal = () => {
  showImageModal.value = true
}

const closeImageModal = () => {
  showImageModal.value = false
}

// Helper computed properties
const hasTranslations = computed(() => {
  return (props.result.translations_en && props.result.translations_en.length > 0) ||
         (props.result.translations_zh && props.result.translations_zh.length > 0)
})

const showAdditionalTranslations = computed(() => {
  return (props.result.translations_en && props.result.translations_en.length > 1) ||
         (props.result.translations_zh && props.result.translations_zh.length > 1)
})

const selectSuggestion = async (word: string) => {
  try {
    await selectSuggestedWord(word)
  } catch (error: any) {
    console.error('Failed to select suggestion:', error)
  }
}
// Helper functions for styling
const getConfidenceClass = (confidence: number) => {
  if (confidence >= 0.8) return 'bg-green-100 text-green-800'
  if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const getGenderClass = (gender: string) => {
  const g = gender.toLowerCase()
  if (g === 'masc' || g === 'masculine') return 'bg-blue-100 text-blue-800'
  if (g === 'fem' || g === 'feminine') return 'bg-pink-100 text-pink-800'
  if (g === 'neut' || g === 'neuter') return 'bg-gray-100 text-gray-800'
  return 'bg-purple-100 text-purple-800'
}

const getGenderDisplay = (gender: string) => {
  const g = gender.toLowerCase()
  if (g === 'masc' || g === 'masculine') return 'der'
  if (g === 'fem' || g === 'feminine') return 'die'
  if (g === 'neut' || g === 'neuter') return 'das'
  return gender
}

const getArticleClass = (article: string) => {
  const a = article.toLowerCase()
  if (a === 'der') return 'bg-blue-100 text-blue-800'
  if (a === 'die') return 'bg-pink-100 text-pink-800'
  if (a === 'das') return 'bg-gray-100 text-gray-800'
  return 'bg-purple-100 text-purple-800'
}

// Dynamic tense display helpers
const getTenseDisplayName = (tenseName: string): string => {
  const tenseNames: { [key: string]: string } = {
    'praesens': 'Präsens (Present)',
    'präsens': 'Präsens (Present)',
    'praeteritum': 'Präteritum (Simple Past)',
    'präteritum': 'Präteritum (Simple Past)',
    'perfekt': 'Perfekt (Present Perfect)',
    'plusquamperfekt': 'Plusquamperfekt (Past Perfect)',
    'futur_i': 'Futur I (Future I)',
    'futur1': 'Futur I (Future I)',
    'futur_ii': 'Futur II (Future II)',
    'futur2': 'Futur II (Future II)',
    'imperativ': 'Imperativ (Commands)',
    'konjunktiv_i': 'Konjunktiv I (Subjunctive I)',
    'konjunktiv_ii': 'Konjunktiv II (Subjunctive II)'
  }
  return tenseNames[tenseName] || tenseName.charAt(0).toUpperCase() + tenseName.slice(1)
}

const getTenseStyle = (tenseName: string): string => {
  const styles: { [key: string]: string } = {
    'praesens': 'bg-blue-50 border-blue-200',
    'präsens': 'bg-blue-50 border-blue-200',
    'praeteritum': 'bg-green-50 border-green-200',
    'präteritum': 'bg-green-50 border-green-200',
    'perfekt': 'bg-purple-50 border-purple-200',
    'plusquamperfekt': 'bg-orange-50 border-orange-200',
    'futur_i': 'bg-indigo-50 border-indigo-200',
    'futur1': 'bg-indigo-50 border-indigo-200',
    'futur_ii': 'bg-pink-50 border-pink-200',
    'futur2': 'bg-pink-50 border-pink-200',
    'imperativ': 'bg-red-50 border-red-200',
    'konjunktiv_i': 'bg-amber-50 border-amber-200',
    'konjunktiv_ii': 'bg-yellow-50 border-yellow-200'
  }
  return styles[tenseName] || 'bg-gray-50 border-gray-200'
}

const getTenseHeaderClass = (tenseName: string): string => {
  const classes: { [key: string]: string } = {
    'praesens': 'text-blue-800',
    'präsens': 'text-blue-800',
    'praeteritum': 'text-green-800',
    'präteritum': 'text-green-800',
    'perfekt': 'text-purple-800',
    'plusquamperfekt': 'text-orange-800',
    'futur_i': 'text-indigo-800',
    'futur1': 'text-indigo-800',
    'futur_ii': 'text-pink-800',
    'futur2': 'text-pink-800',
    'imperativ': 'text-red-800',
    'konjunktiv_i': 'text-amber-800',
    'konjunktiv_ii': 'text-yellow-800'
  }
  return classes[tenseName] || 'text-gray-800'
}

// POS display functions now provided by usePartOfSpeech() composable

const getTenseTextClass = (tenseName: string): string => {
  const classes: { [key: string]: string } = {
    'praesens': 'text-blue-900',
    'präsens': 'text-blue-900',
    'praeteritum': 'text-green-900',
    'präteritum': 'text-green-900',
    'perfekt': 'text-purple-900',
    'plusquamperfekt': 'text-orange-900',
    'futur_i': 'text-indigo-900',
    'futur1': 'text-indigo-900',
    'futur_ii': 'text-pink-900',
    'futur2': 'text-pink-900',
    'imperativ': 'text-red-900',
    'konjunktiv_i': 'text-amber-900',
    'konjunktiv_ii': 'text-yellow-900'
  }
  return classes[tenseName] || 'text-gray-900'
}

const getPersonsForTense = (tenseName: string, forms: any): string[] => {
  if (!forms || typeof forms !== 'object') return []
  
  // Define order for regular persons (imperative has different persons)
  const regularPersons = ['ich', 'du', 'er_sie_es', 'wir', 'ihr', 'sie_Sie']
  const imperativPersons = ['du', 'ihr', 'Sie']
  
  const availablePersons = Object.keys(forms).filter(person => forms[person])
  
  if (tenseName === 'imperativ') {
    return imperativPersons.filter(person => availablePersons.includes(person))
  } else {
    return regularPersons.filter(person => availablePersons.includes(person))
  }
}

const getPersonDisplayName = (person: string): string => {
  const personNames: { [key: string]: string } = {
    'ich': 'ich',
    'du': 'du',
    'er_sie_es': 'er/sie/es',
    'wir': 'wir',
    'ihr': 'ihr',
    'sie_Sie': 'sie/Sie',
    'Sie': 'Sie'
  }
  return personNames[person] || person
}

interface WordAnalysis {
  original: string
  found?: boolean
  pos?: string
  upos?: string
  xpos?: string
  cefr?: string
  confidence?: number
  enhanced?: boolean
  
  // Basic properties
  article?: string
  gender?: string
  
  // New grammatical features
  degree_forms?: {
    comparative?: string
    superlative?: string
  }
  governance?: string
  adv_type?: string
  
  // Function word features
  conj_type?: string
  pron_info?: {
    type?: string
    cases?: Record<string, string>
  }
  det_type?: string
  num_info?: {
    type?: string
    value?: string
  }
  particle_type?: string
  interj_register?: string
  
  // Meanings
  gloss_en?: string
  gloss_zh?: string
  translations_en?: string[]
  translations_zh?: string[]
  
  // Morphology
  noun_props?: {
    gen_sg?: string
    plural?: string
    declension_class?: string
    dative_plural_ends_n?: boolean
  }
  
  verb_props?: {
    separable?: boolean
    prefix?: string
    aux?: string
    regularity?: string
    partizip_ii?: string
    reflexive?: boolean
    cases?: string[]
    preps?: string[]
    valency?: any
  }
  
  // Legacy fields
  plural?: string
  tables?: any
  
  // Examples
  example?: {
    de: string
    en: string
    zh: string
  }
  examples?: Array<{
    de: string
    en: string
    zh: string
  }>
  
  // Meta
  cached?: boolean
  source?: string
  suggestions?: Array<{
    word: string
    pos: string
    meaning: string
  }>
  message?: string
}
</script>