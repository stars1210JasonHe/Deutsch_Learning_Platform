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
                <span class="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {{ suggestion.pos }}
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
          <AddToSRSButton :lemma="result.original" v-if="result.found" />
        </div>
      </div>
    
      <div class="space-y-6">
      <!-- Debug info (uncomment for debugging) -->
      <!-- <div class="text-xs text-gray-500 bg-gray-100 p-2 rounded">
        Debug: {{ JSON.stringify(result, null, 2) }}
      </div> -->
      
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
      </div>
      
      <!-- Part of Speech & Basic Info -->
      <div class="space-y-4">
        <!-- Primary Info Row -->
        <div class="flex flex-wrap gap-2">
          <span v-if="result.upos || result.pos" class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
            {{ result.upos || result.pos }}
          </span>
          
          <!-- Article for Nouns (also as badge) -->
          <span v-if="result.article && (result.pos === 'noun' || result.upos === 'NOUN')" class="px-3 py-1 rounded-full text-sm font-medium"
                :class="getArticleClass(result.article)">
            {{ result.article }}
          </span>
          
          <!-- Verb Properties -->
          <span v-if="result.verb_props?.separable" class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm">
            separable
          </span>
          <span v-if="result.verb_props?.aux" class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
            {{ result.verb_props.aux }}
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
        <div v-if="result.verb_props && result.upos === 'VERB'" class="bg-green-50 rounded-lg p-4">
          <h4 class="font-medium text-green-900 mb-2">Verb Properties</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div v-if="result.verb_props.partizip_ii">
              <span class="text-green-600">Partizip II:</span>
              <span class="ml-1 font-medium">{{ result.verb_props.partizip_ii }}</span>
            </div>
            <div v-if="result.verb_props.regularity">
              <span class="text-green-600">Type:</span>
              <span class="ml-1 font-medium">{{ result.verb_props.regularity }}</span>
            </div>
            <div v-if="result.verb_props.prefix">
              <span class="text-green-600">Prefix:</span>
              <span class="ml-1 font-medium">{{ result.verb_props.prefix }}</span>
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
      
      <!-- Conjugation Tables (for verbs) -->
      <div v-if="result.tables && (result.pos === 'verb' || result.upos === 'VERB')" class="space-y-4">
        <h3 class="font-semibold text-gray-700">Conjugation</h3>
        
        <!-- Primary Tenses Grid -->
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Präsens -->
          <div v-if="result.tables.praesens" class="border rounded-lg p-4 bg-blue-50 border-blue-200">
            <h4 class="font-medium text-blue-800 mb-3">Präsens (Present)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.praesens.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.ich }}</span>
              </div>
              <div v-if="result.tables.praesens.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.du }}</span>
              </div>
              <div v-if="result.tables.praesens.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.praesens.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.wir }}</span>
              </div>
              <div v-if="result.tables.praesens.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.ihr }}</span>
              </div>
              <div v-if="result.tables.praesens.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-blue-900">{{ result.tables.praesens.sie_Sie }}</span>
              </div>
            </div>
          </div>
          
          <!-- Präteritum -->
          <div v-if="result.tables.praeteritum" class="border rounded-lg p-4 bg-green-50 border-green-200">
            <h4 class="font-medium text-green-800 mb-3">Präteritum (Simple Past)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.praeteritum.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.ich }}</span>
              </div>
              <div v-if="result.tables.praeteritum.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.du }}</span>
              </div>
              <div v-if="result.tables.praeteritum.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.praeteritum.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.wir }}</span>
              </div>
              <div v-if="result.tables.praeteritum.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.ihr }}</span>
              </div>
              <div v-if="result.tables.praeteritum.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-green-900">{{ result.tables.praeteritum.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Perfekt -->
          <div v-if="result.tables.perfekt" class="border rounded-lg p-4 bg-purple-50 border-purple-200">
            <h4 class="font-medium text-purple-800 mb-3">Perfekt (Present Perfect)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.perfekt.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.ich }}</span>
              </div>
              <div v-if="result.tables.perfekt.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.du }}</span>
              </div>
              <div v-if="result.tables.perfekt.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.perfekt.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.wir }}</span>
              </div>
              <div v-if="result.tables.perfekt.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.ihr }}</span>
              </div>
              <div v-if="result.tables.perfekt.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-purple-900">{{ result.tables.perfekt.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Plusquamperfekt -->
          <div v-if="result.tables.plusquamperfekt" class="border rounded-lg p-4 bg-orange-50 border-orange-200">
            <h4 class="font-medium text-orange-800 mb-3">Plusquamperfekt (Past Perfect)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.plusquamperfekt.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.ich }}</span>
              </div>
              <div v-if="result.tables.plusquamperfekt.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.du }}</span>
              </div>
              <div v-if="result.tables.plusquamperfekt.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.plusquamperfekt.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.wir }}</span>
              </div>
              <div v-if="result.tables.plusquamperfekt.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.ihr }}</span>
              </div>
              <div v-if="result.tables.plusquamperfekt.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-orange-900">{{ result.tables.plusquamperfekt.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Futur I -->
          <div v-if="result.tables.futur_i" class="border rounded-lg p-4 bg-indigo-50 border-indigo-200">
            <h4 class="font-medium text-indigo-800 mb-3">Futur I (Future I)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.futur_i.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.ich }}</span>
              </div>
              <div v-if="result.tables.futur_i.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.du }}</span>
              </div>
              <div v-if="result.tables.futur_i.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.futur_i.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.wir }}</span>
              </div>
              <div v-if="result.tables.futur_i.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.ihr }}</span>
              </div>
              <div v-if="result.tables.futur_i.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-indigo-900">{{ result.tables.futur_i.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Futur II -->
          <div v-if="result.tables.futur_ii" class="border rounded-lg p-4 bg-pink-50 border-pink-200">
            <h4 class="font-medium text-pink-800 mb-3">Futur II (Future II)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.futur_ii.ich" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ich</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.ich }}</span>
              </div>
              <div v-if="result.tables.futur_ii.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.du }}</span>
              </div>
              <div v-if="result.tables.futur_ii.er_sie_es" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.er_sie_es }}</span>
              </div>
              <div v-if="result.tables.futur_ii.wir" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">wir</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.wir }}</span>
              </div>
              <div v-if="result.tables.futur_ii.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.ihr }}</span>
              </div>
              <div v-if="result.tables.futur_ii.sie_Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                <span class="font-medium text-pink-900">{{ result.tables.futur_ii.sie_Sie }}</span>
              </div>
            </div>
          </div>

          <!-- Imperativ (Commands) - moved to main grid with red styling -->
          <div v-if="result.tables && result.tables.imperativ" class="border rounded-lg p-4 bg-red-50 border-red-200">
            <h4 class="font-medium text-red-800 mb-3">Imperativ (Commands)</h4>
            <div class="space-y-2 text-sm">
              <div v-if="result.tables.imperativ.du" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">du</span>
                <span class="font-medium text-red-900">{{ result.tables.imperativ.du }}</span>
              </div>
              <div v-if="result.tables.imperativ.ihr" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">ihr</span>
                <span class="font-medium text-red-900">{{ result.tables.imperativ.ihr }}</span>
              </div>
              <div v-if="result.tables.imperativ.Sie" class="flex justify-between">
                <span class="text-gray-600 w-20 font-medium">Sie</span>
                <span class="font-medium text-red-900">{{ result.tables.imperativ.Sie }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Subjunctive Forms (if available) -->
        <div v-if="result.tables.konjunktiv_i || result.tables.konjunktiv_ii" class="space-y-4">
          <h4 class="font-medium text-gray-700 mt-6 mb-3">Subjunctive Forms</h4>
          <div class="grid md:grid-cols-2 gap-4">
            <!-- Konjunktiv I -->
            <div v-if="result.tables.konjunktiv_i" class="border rounded-lg p-4 bg-red-50 border-red-200">
              <h5 class="font-medium text-red-800 mb-3">Konjunktiv I (Subjunctive I)</h5>
              <div class="space-y-2 text-sm">
                <div v-if="result.tables.konjunktiv_i.ich" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">ich</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.ich }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_i.du" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">du</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.du }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_i.er_sie_es" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.er_sie_es }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_i.wir" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">wir</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.wir }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_i.ihr" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">ihr</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.ihr }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_i.sie_Sie" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                  <span class="font-medium text-red-900">{{ result.tables.konjunktiv_i.sie_Sie }}</span>
                </div>
              </div>
            </div>

            <!-- Konjunktiv II -->
            <div v-if="result.tables.konjunktiv_ii" class="border rounded-lg p-4 bg-yellow-50 border-yellow-200">
              <h5 class="font-medium text-yellow-800 mb-3">Konjunktiv II (Subjunctive II)</h5>
              <div class="space-y-2 text-sm">
                <div v-if="result.tables.konjunktiv_ii.ich" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">ich</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.ich }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_ii.du" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">du</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.du }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_ii.er_sie_es" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">er/sie/es</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.er_sie_es }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_ii.wir" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">wir</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.wir }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_ii.ihr" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">ihr</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.ihr }}</span>
                </div>
                <div v-if="result.tables.konjunktiv_ii.sie_Sie" class="flex justify-between">
                  <span class="text-gray-600 w-20 font-medium">sie/Sie</span>
                  <span class="font-medium text-yellow-900">{{ result.tables.konjunktiv_ii.sie_Sie }}</span>
                </div>
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
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import SpeechButton from './SpeechButton.vue'
import FavoriteButton from './FavoriteButton.vue'
import AddToSRSButton from './AddToSRSButton.vue'

const props = defineProps<{
  result: WordAnalysis
}>()

const searchStore = useSearchStore()
const { isLoading, selectSuggestedWord } = searchStore

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